from collections.abc import Callable
from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

import nats.errors
import nats.js.errors
from nats.aio.client import Client
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from ontok.core import Event, NodeId
from ontok.events import (
    Absent,
    Acknowledge,
    Acknowledged,
    Acknowledgement,
    Answer,
    Append,
    AppendUnavailable,
    ClaimRefusal,
    Contested,
    Deleted,
    DeleteSubscription,
    Disposition,
    Ensured,
    EnsureSubscription,
    EnsureUnavailable,
    FailureReason,
    History,
    HistoryReading,
    LatestReading,
    LogSequence,
    ReadAddress,
    ReadHistory,
    Readings,
    ReadLatest,
    Retained,
    Settled,
    SubscriptionDeleted,
    SubscriptionEnsured,
    Unavailable,
    Written,
)
from ontok.nats.model import (
    BatchReplyConstructor,
    EndOfBatch,
    LastBySubject,
    LatestReplyConstructor,
    NextBySubject,
    NoResults,
    PublishReply,
    PublishReplyConstructor,
    Remembered,
)
from ontok.nats.subject import (
    AddressSubjectConstructor,
    EntitySubject,
    FilterSubject,
    LatestSubjectConstructor,
)

INTERPRETER = ConfigDict(
    frozen=True,
    extra="forbid",
    strict=True,
    validate_default=True,
    revalidate_instances="never",
    arbitrary_types_allowed=True,
)
STRICT = ConfigDict(
    frozen=True, extra="forbid", strict=True, validate_default=True, revalidate_instances="never"
)
STREAM = "EVENTS"
DIRECT_GET = "$JS.API.DIRECT.GET.EVENTS"
DELIVER_PREFIX = "_INBOX.ontok."
TIMEOUT = 5.0
UNAVAILABLE = (
    nats.errors.TimeoutError,
    nats.errors.NoRespondersError,
    nats.errors.ConnectionClosedError,
)
ACK: dict[Disposition, bytes] = {
    Disposition.COMPLETE: b"+ACK",
    Disposition.RETRY: b"-NAK",
    Disposition.REJECT: b"+TERM",
}


# --- A claim's headers ---------------------------------------------------------------------------


class SequenceClaim(BaseModel):
    """The append claims the entity's latest occurrence has this sequence."""

    model_config = STRICT

    sequence: LogSequence = Field(validation_alias=AliasPath("expectation", "sequence"))
    about: NodeId = Field(validation_alias=AliasPath("lead", "address", "about"))

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Nats-Expected-Last-Subject-Sequence": str(self.sequence.root),
            "Nats-Expected-Last-Subject-Sequence-Subject": EntitySubject(about=self.about).text,
        }


class AnyClaim(BaseModel):
    """The append claims nothing is at its first occurrence's own address."""

    model_config = STRICT

    @property
    def headers(self) -> dict[str, str]:
        return {"Nats-Expected-Last-Subject-Sequence": "0"}


Claim = Annotated[SequenceClaim | AnyClaim, Field(union_mode="left_to_right")]
ClaimConstructor: TypeAdapter[SequenceClaim | AnyClaim] = TypeAdapter(Claim)


# --- The answer to an append, from its reply -----------------------------------------------------


class ContestedPublication(BaseModel):
    """The claim did not hold: the reply carried memory's refusal."""

    model_config = STRICT

    append: Append
    refusal: ClaimRefusal = Field(validation_alias=AliasPath("reply", "refusal"))

    @property
    def answer(self) -> Answer:
        return Contested(append=self.append, refusal=self.refusal)


class FailedPublication(BaseModel):
    """The provider did not complete the append: the reply carried a failure."""

    model_config = STRICT

    append: Append
    reason: FailureReason = Field(validation_alias=AliasPath("reply", "failure"))

    @property
    def answer(self) -> Answer:
        return AppendUnavailable(append=self.append, reason=self.reason)


class WrittenPublication(BaseModel):
    """What remains: the reply acknowledged the append."""

    model_config = STRICT

    append: Append

    @property
    def answer(self) -> Answer:
        return Written(append=self.append)


Publication = Annotated[
    ContestedPublication | FailedPublication | WrittenPublication,
    Field(union_mode="left_to_right"),
]
PublicationConstructor: TypeAdapter[
    ContestedPublication | FailedPublication | WrittenPublication
] = TypeAdapter(Publication)


class Published(BaseModel):
    """An append and the reply memory gave it."""

    model_config = STRICT

    append: Append
    reply: PublishReply

    @property
    def answer(self) -> Answer:
        return PublicationConstructor.validate_python(self, from_attributes=True).answer


def subject_of(event: Event) -> str:
    return AddressSubjectConstructor.validate_python(event, from_attributes=True).text


# --- Interpreters --------------------------------------------------------------------------------


class AppendInterpreter(BaseModel):
    """Commits an append as one atomic batch, headers set by hand, and returns memory's answer."""

    model_config = INTERPRETER

    action: Append
    client: Client = Field(exclude=True, repr=False)

    async def execute(self) -> Answer:
        events = self.action.events
        if not events:
            return Written(append=self.action)
        batch = events[0].id.root
        claim = ClaimConstructor.validate_python(self.action, from_attributes=True).headers
        try:
            for position, event in enumerate(events[:-1]):
                await self.client.publish(
                    subject_of(event),
                    event.model_dump_json(by_alias=True).encode(),
                    headers={
                        "Nats-Batch-Id": batch,
                        "Nats-Batch-Sequence": str(position + 1),
                        **(claim if position == 0 else AnyClaim().headers),
                    },
                )
            reply = await self.client.request(
                subject_of(events[-1]),
                events[-1].model_dump_json(by_alias=True).encode(),
                timeout=TIMEOUT,
                headers={
                    "Nats-Batch-Id": batch,
                    "Nats-Batch-Sequence": str(len(events)),
                    "Nats-Batch-Commit": "1",
                    **(claim if len(events) == 1 else AnyClaim().headers),
                },
            )
        except UNAVAILABLE as failure:
            return AppendUnavailable(append=self.action, reason=FailureReason(repr(failure)))
        return Published(
            append=self.action, reply=PublishReplyConstructor.validate_json(reply.data)
        ).answer


class ReadLatestInterpreter(BaseModel):
    """Reads the latest occurrence in a scope through a direct get in the body form."""

    model_config = INTERPRETER

    action: ReadLatest
    client: Client = Field(exclude=True, repr=False)
    constructor: Callable[[bytes], Event] = Field(exclude=True, repr=False)

    async def execute(self) -> LatestReading:
        subject = LatestSubjectConstructor.validate_python(self.action, from_attributes=True).text
        try:
            reply = await self.client.request(
                DIRECT_GET, LastBySubject(last_by_subj=subject).model_dump_json().encode(), TIMEOUT
            )
        except UNAVAILABLE as failure:
            return Unavailable(reason=FailureReason(repr(failure)))
        match LatestReplyConstructor.validate_python(reply, from_attributes=True):
            case Remembered(sequence=sequence, data=data):
                return Retained(
                    event=self.constructor(data), sequence=LogSequence.model_validate_json(sequence)
                )
            case NoResults():
                return Absent(about=self.action.about)


class ReadAddressInterpreter(BaseModel):
    """Reads the occurrence at one address through a direct get on its exact subject."""

    model_config = INTERPRETER

    action: ReadAddress
    client: Client = Field(exclude=True, repr=False)
    constructor: Callable[[bytes], Event] = Field(exclude=True, repr=False)

    async def execute(self) -> LatestReading:
        subject = AddressSubjectConstructor.validate_python(
            self.action.address, from_attributes=True
        ).text
        try:
            reply = await self.client.request(
                DIRECT_GET, LastBySubject(last_by_subj=subject).model_dump_json().encode(), TIMEOUT
            )
        except UNAVAILABLE as failure:
            return Unavailable(reason=FailureReason(repr(failure)))
        match LatestReplyConstructor.validate_python(reply, from_attributes=True):
            case Remembered(sequence=sequence, data=data):
                return Retained(
                    event=self.constructor(data), sequence=LogSequence.model_validate_json(sequence)
                )
            case NoResults():
                return Absent(about=self.action.address.about)


class ReadHistoryInterpreter(BaseModel):
    """Reads an entity's whole history through a batched direct get, paged until the end."""

    model_config = INTERPRETER

    action: ReadHistory
    client: Client = Field(exclude=True, repr=False)
    constructor: Callable[[bytes], Event] = Field(exclude=True, repr=False)

    async def execute(self) -> HistoryReading:
        subject = EntitySubject(about=self.action.about).text
        inbox = self.client.new_inbox()
        remembered: list[Retained] = []
        try:
            subscription = await self.client.subscribe(inbox)  # pyright: ignore[reportUnknownMemberType]
            await self.client.publish(
                DIRECT_GET,
                NextBySubject(seq=1, next_by_subj=subject, batch=1).model_dump_json().encode(),
                reply=inbox,
            )
            while True:
                reply = await subscription.next_msg(timeout=TIMEOUT)
                match BatchReplyConstructor.validate_python(reply, from_attributes=True):
                    case Remembered(sequence=sequence, data=data):
                        remembered.append(
                            Retained(
                                event=self.constructor(data),
                                sequence=LogSequence.model_validate_json(sequence),
                            )
                        )
                    case EndOfBatch(pending="0"):
                        break
                    case EndOfBatch(pending=pending, last=last):
                        await self.client.publish(
                            DIRECT_GET,
                            NextBySubject(
                                seq=int(last) + 1, next_by_subj=subject, batch=int(pending)
                            )
                            .model_dump_json()
                            .encode(),
                            reply=inbox,
                        )
                    case NoResults():
                        return Absent(about=self.action.about)
            await subscription.unsubscribe()
        except UNAVAILABLE as failure:
            return Unavailable(reason=FailureReason(repr(failure)))
        return History(tuple(remembered))


class SettleInterpreter(BaseModel):
    """Reads the addresses an answer authorizes and returns the settlement that couples it."""

    model_config = INTERPRETER

    action: Answer
    client: Client = Field(exclude=True, repr=False)
    constructor: Callable[[bytes], Event] = Field(exclude=True, repr=False)

    async def execute(self) -> Settled:
        return Settled(
            answer=self.action,
            readings=Readings(
                tuple(
                    [
                        await ReadAddressInterpreter(
                            action=read, client=self.client, constructor=self.constructor
                        ).execute()
                        for read in self.action.reads
                    ]
                )
            ),
        )


class EnsureSubscriptionInterpreter(BaseModel):
    """Makes a subscription exist as a durable push consumer, idempotently."""

    model_config = INTERPRETER

    action: EnsureSubscription
    client: Client = Field(exclude=True, repr=False)

    async def execute(self) -> Ensured:
        subscription = self.action.subscription
        name = subscription.work_type.root
        config = ConsumerConfig(
            name=name,
            durable_name=name,
            deliver_subject=DELIVER_PREFIX + name,
            deliver_group=name,
            ack_policy=AckPolicy.EXPLICIT,
            ack_wait=subscription.patience.root.total_seconds(),
            max_deliver=-1,
            max_ack_pending=1,
            deliver_policy=DeliverPolicy.ALL,
            filter_subjects=[
                FilterSubject(event_type=event_type).text for event_type in subscription.event_types
            ],
            flow_control=False,
        )
        try:
            await self.client.jetstream().add_consumer(STREAM, config, timeout=TIMEOUT)  # pyright: ignore[reportUnknownMemberType]
        except (nats.js.errors.APIError, *UNAVAILABLE) as failure:
            return EnsureUnavailable(subscription=subscription, reason=FailureReason(repr(failure)))
        return SubscriptionEnsured(subscription=subscription)


class DeleteSubscriptionInterpreter(BaseModel):
    """Removes a subscription's consumer; one that is already gone is gone."""

    model_config = INTERPRETER

    action: DeleteSubscription
    client: Client = Field(exclude=True, repr=False)

    async def execute(self) -> Deleted:
        subscription = self.action.subscription
        try:
            await self.client.jetstream().delete_consumer(STREAM, subscription.work_type.root)  # pyright: ignore[reportUnknownMemberType]
        except nats.js.errors.NotFoundError:
            return SubscriptionDeleted(subscription=subscription)
        except (nats.js.errors.APIError, *UNAVAILABLE) as failure:
            return Unavailable(reason=FailureReason(repr(failure)))
        return SubscriptionDeleted(subscription=subscription)


class AcknowledgeInterpreter(BaseModel):
    """Tells memory what became of a delivery by publishing to its token."""

    model_config = INTERPRETER

    action: Acknowledge
    client: Client = Field(exclude=True, repr=False)

    async def execute(self) -> Acknowledgement:
        try:
            await self.client.publish(self.action.token.root, ACK[self.action.disposition])
        except UNAVAILABLE as failure:
            return Unavailable(reason=FailureReason(repr(failure)))
        return Acknowledged()
