from datetime import timedelta
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, RootModel, TypeAdapter

from nats.aio.client import Client
from ontok.core import NodeId, PositiveDuration
from ontok.events import (
    Attempt,
    Delivery,
    DeliveryIdentity,
    Event,
    Occurrence,
    Position,
    Read,
    Subscription,
    Version,
)
from ontok.nats.batch import VersionHeader
from ontok.nats.error import ApiError
from ontok.nats.stream import EventSubject, FilterSubject, Payload, Sequence, StreamName, Subject


class ConsumerName(RootModel[str]):
    """The name of a consumer: no whitespace, period, asterisk, greater-than, or slash."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[^\s.*>/\\]+$")


class NumDelivered(RootModel[int]):
    """How many times a message has been delivered to a consumer."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class NumPending(RootModel[int]):
    """How many messages remain for a consumer."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=0)


class MaxDeliver(RootModel[int]):
    """The most times a message is delivered to a consumer."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class Nanoseconds(RootModel[int]):
    """A duration as a consumer configuration states it."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class DeliverPolicy(StrEnum):
    """Where a consumer begins in the stream."""

    ALL = "all"
    LAST = "last"
    NEW = "new"
    BY_START_SEQUENCE = "by_start_sequence"
    BY_START_TIME = "by_start_time"
    LAST_PER_SUBJECT = "last_per_subject"


class AckPolicy(StrEnum):
    """How a consumer requires messages to be acknowledged."""

    NONE = "none"
    ALL = "all"
    EXPLICIT = "explicit"


class Ack(StrEnum):
    """The reply a consumer sends on a delivered message's reply subject."""

    ACK = "+ACK"
    NAK = "-NAK"
    TERM = "+TERM"


class DeliveredMessage(BaseModel):
    """A message a consumer delivered: where to answer, the Stream it is in, its sequence, its
    count, and what it carries."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    reply: Subject = Field(description="The subject an Ack is sent to.")
    stream: NodeId = Field(validation_alias=AliasPath("headers", "Ontok-Stream"))
    version: VersionHeader = Field(validation_alias=AliasPath("headers", "Ontok-Version"))
    stream_sequence: Sequence = Field(validation_alias=AliasPath("metadata", "sequence", "stream"))
    num_delivered: NumDelivered = Field(validation_alias=AliasPath("metadata", "num_delivered"))
    payload: Payload = Field(validation_alias="data")


class DeliveryRoute(BaseModel):
    """A delivered message as a program receives it: the Stream, the Version, the Position, and
    the Attempt are NATS's, and the Event is all of them with the occurrence the payload carries.
    An organization refines this route to construct its own occurrence from the payload."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    message: DeliveredMessage = Field(description="The message as NATS delivered it.")

    @property
    def stream(self) -> NodeId:
        return self.message.stream

    @property
    def version(self) -> Version:
        return Version.model_validate(self.message.version.root, strict=False)

    @property
    def position(self) -> Position:
        return Position(self.message.stream_sequence.root)

    @property
    def attempt(self) -> Attempt:
        return Attempt(self.message.num_delivered.root)

    @property
    def occurrence(self) -> Occurrence:
        return Occurrence.model_validate_json(self.message.payload.root)

    @property
    def event(self) -> Event:
        return Event(
            occurrence=self.occurrence,
            stream=self.stream,
            version=self.version,
            position=self.position,
        )


class ConsumerDelivery(BaseModel):
    """A message a Subscription's consumer delivered, as the Delivery it is."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    route: DeliveryRoute = Field(description="The delivered message.")
    subscription: Subscription = Field(description="The Subscription it was delivered to.")

    @property
    def delivery(self) -> Delivery:
        return Delivery(
            id=DeliveryIdentity(
                subscription=self.subscription.id,
                event=self.route.event.occurrence.id,
                attempt=self.route.attempt,
            ).id,
            action=self.subscription,
            event=self.route.event,
            attempt=self.route.attempt,
        )


class MaxDeliveriesAdvisory(BaseModel):
    """The server's advisory that a message reached a consumer's max deliver: the consumer, the
    message's stream sequence, and how many times it was delivered."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    consumer: ConsumerName = Field(description="The consumer that gave up.")
    stream_seq: Sequence = Field(description="The message's sequence in the stream.")
    deliveries: NumDelivered = Field(description="How many times it was delivered.")


class Messages(RootModel[tuple[DeliveredMessage, ...]]):
    """The messages one pull delivered, in order."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )


class StreamFilter(BaseModel):
    """A Subscription to one Stream: the consumer filters that Stream's subject."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: NodeId = Field(validation_alias=AliasPath("stream"))

    @property
    def subject(self) -> FilterSubject:
        return FilterSubject(EventSubject(stream=self.stream).subject.root)


class AllFilter(BaseModel):
    """A Subscription to every Event: the consumer filters every Stream's subject."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    @property
    def subject(self) -> FilterSubject:
        return FilterSubject("event.>")


Filter = Annotated[StreamFilter | AllFilter, Field(union_mode="left_to_right")]
FilterConstructor: TypeAdapter[Filter] = TypeAdapter(Filter)


class BeginAfter(BaseModel):
    """A Subscription beginning after a Position: the consumer starts at the next sequence."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    position: Sequence = Field(validation_alias=AliasPath("begins", "position", "root"))

    @property
    def deliver_policy(self) -> DeliverPolicy:
        return DeliverPolicy.BY_START_SEQUENCE

    @property
    def opt_start_seq(self) -> Sequence:
        return Sequence(self.position.root + 1)


class BeginAll(BaseModel):
    """A Subscription beginning at the beginning: the consumer delivers all."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["beginning"] = Field(validation_alias=AliasPath("begins", "value"))

    @property
    def deliver_policy(self) -> DeliverPolicy:
        return DeliverPolicy.ALL


class BeginNew(BaseModel):
    """A Subscription beginning now: the consumer delivers only what is new."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["now"] = Field(validation_alias=AliasPath("begins", "value"))

    @property
    def deliver_policy(self) -> DeliverPolicy:
        return DeliverPolicy.NEW


Begin = BeginAfter | BeginAll | BeginNew
BeginConstructor: TypeAdapter[Begin] = TypeAdapter(Begin)


class AfterPosition(BaseModel):
    """A Read beginning after a Position: the consumer starts at the next sequence."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    position: Sequence = Field(validation_alias=AliasPath("after", "position", "root"))

    @property
    def deliver_policy(self) -> DeliverPolicy:
        return DeliverPolicy.BY_START_SEQUENCE

    @property
    def opt_start_seq(self) -> Sequence:
        return Sequence(self.position.root + 1)


class FromBeginning(BaseModel):
    """A Read from the beginning: the consumer delivers all."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["beginning"] = Field(validation_alias=AliasPath("after", "value"))

    @property
    def deliver_policy(self) -> DeliverPolicy:
        return DeliverPolicy.ALL


After = AfterPosition | FromBeginning
AfterConstructor: TypeAdapter[After] = TypeAdapter(After)


class PullConsumerConfig(BaseModel):
    """The configuration of an ephemeral pull consumer over one Stream's subject."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    filter_subject: FilterSubject = Field(validation_alias=AliasPath("filter", "subject"))
    deliver_policy: DeliverPolicy = Field(validation_alias=AliasPath("after", "deliver_policy"))
    ack_policy: Literal[AckPolicy.NONE] = AckPolicy.NONE


class PullConsumerFromConfig(PullConsumerConfig):
    """The configuration of an ephemeral pull consumer that begins at a sequence."""

    opt_start_seq: Sequence = Field(validation_alias=AliasPath("after", "opt_start_seq"))


PullConfig = Annotated[
    PullConsumerFromConfig | PullConsumerConfig, Field(union_mode="left_to_right")
]
PullConfigConstructor: TypeAdapter[PullConfig] = TypeAdapter(PullConfig)


class PushConsumerConfig(BaseModel):
    """The configuration of a durable push consumer for a Subscription: one deliver group, so
    every process serving the Subscription shares its deliveries."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    durable_name: ConsumerName = Field(validation_alias=AliasPath("durable_name"))
    deliver_subject: Subject = Field(validation_alias=AliasPath("deliver_subject"))
    deliver_group: ConsumerName = Field(validation_alias=AliasPath("durable_name"))
    filter_subject: FilterSubject = Field(validation_alias=AliasPath("filter", "subject"))
    deliver_policy: DeliverPolicy = Field(validation_alias=AliasPath("begin", "deliver_policy"))
    ack_policy: Literal[AckPolicy.EXPLICIT] = AckPolicy.EXPLICIT
    ack_wait: Nanoseconds = Field(validation_alias=AliasPath("nanoseconds"))
    max_deliver: MaxDeliver = Field(validation_alias=AliasPath("max_deliver"))


class PushConsumerFromConfig(PushConsumerConfig):
    """The configuration of a durable push consumer that begins at a sequence."""

    opt_start_seq: Sequence = Field(validation_alias=AliasPath("begin", "opt_start_seq"))


PushConfig = Annotated[
    PushConsumerFromConfig | PushConsumerConfig, Field(union_mode="left_to_right")
]
PushConfigConstructor: TypeAdapter[PushConfig] = TypeAdapter(PushConfig)


class PullConsumer(BaseModel):
    """A Read as NATS receives it: an ephemeral pull consumer over the Stream's subject, begun
    where the Read begins."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    read: Read = Field(description="The Read.")

    @property
    def filter(self) -> StreamFilter:
        return StreamFilter(stream=self.read.stream)

    @property
    def after(self) -> After:
        return AfterConstructor.validate_python(self.read, from_attributes=True)

    @property
    def config(self) -> PullConfig:
        return PullConfigConstructor.validate_python(self, from_attributes=True)


class PushConsumer(BaseModel):
    """A Subscription as NATS receives it: a durable push consumer, filtered and begun as the
    Subscription says, acknowledged within a wait and up to a count."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subscription: Subscription = Field(description="The Subscription.")
    ack_wait: PositiveDuration = Field(description="How long a delivery waits for its Ack.")
    max_deliver: MaxDeliver = Field(description="The most times an Event is delivered.")

    @property
    def durable_name(self) -> ConsumerName:
        return ConsumerName(self.subscription.id.root)

    @property
    def deliver_subject(self) -> Subject:
        return Subject(f"deliver.{self.subscription.id.root}")

    @property
    def filter(self) -> Filter:
        return FilterConstructor.validate_python(self.subscription, from_attributes=True)

    @property
    def begin(self) -> Begin:
        return BeginConstructor.validate_python(self.subscription, from_attributes=True)

    @property
    def nanoseconds(self) -> Nanoseconds:
        return Nanoseconds(self.ack_wait.root // timedelta(microseconds=1) * 1000)

    @property
    def config(self) -> PushConfig:
        return PushConfigConstructor.validate_python(self, from_attributes=True)


class EphemeralConsumerRequest(BaseModel):
    """A request to create an ephemeral consumer on a stream."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream_name: StreamName = Field(description="The stream.")
    config: PullConfig = Field(description="The consumer.")

    @property
    def api(self) -> Subject:
        return Subject(f"$JS.API.CONSUMER.CREATE.{self.stream_name.root}")


class DurableConsumerRequest(BaseModel):
    """A request to create a durable consumer on a stream."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream_name: StreamName = Field(description="The stream.")
    config: PushConfig = Field(description="The consumer.")

    @property
    def api(self) -> Subject:
        return Subject(
            f"$JS.API.CONSUMER.CREATE.{self.stream_name.root}.{self.config.durable_name.root}"
        )


class ConsumerInfo(BaseModel):
    """A consumer as the API describes it: its name, its stream, and how many messages remain."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    name: ConsumerName = Field(description="The consumer.")
    stream_name: StreamName = Field(description="Its stream.")
    num_pending: NumPending = Field(description="How many messages remain for it.")


ConsumerReply = ConsumerInfo | ApiError
ConsumerReplyConstructor: TypeAdapter[ConsumerReply] = TypeAdapter(ConsumerReply)


class NextRequest(BaseModel):
    """A pull request: a batch, answered at once with what is available and no waiting."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    batch: NumPending = Field(description="How many messages are asked for.")
    no_wait: Literal[True] = Field(default=True, description="Answer at once.")


class ConsumerCreation(BaseModel):
    """A consumer request and NATS's reply to it."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    request: EphemeralConsumerRequest | DurableConsumerRequest = Field(description="The request.")
    reply: ConsumerReply = Field(description="NATS's reply to it.")


class Pull(BaseModel):
    """A pull of every pending message from the consumer created for a Read: a pull of none is
    empty."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream_name: StreamName = Field(validation_alias=AliasPath("creation", "reply", "stream_name"))
    consumer: ConsumerName = Field(validation_alias=AliasPath("creation", "reply", "name"))
    batch: NumPending = Field(validation_alias=AliasPath("creation", "reply", "num_pending"))

    @property
    def api(self) -> Subject:
        return Subject(f"$JS.API.CONSUMER.MSG.NEXT.{self.stream_name.root}.{self.consumer.root}")

    @property
    def request(self) -> NextRequest:
        return NextRequest(batch=self.batch)


class ReadRefusal(BaseModel):
    """A Read whose consumer NATS refused to create: there is nothing to pull."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    read: Read = Field(validation_alias=AliasPath("read"))
    error: ApiError = Field(validation_alias=AliasPath("creation", "reply"))


Pulling = Annotated[Pull | ReadRefusal, Field(union_mode="left_to_right")]
PullingConstructor: TypeAdapter[Pulling] = TypeAdapter(Pulling)


class ReadReply(BaseModel):
    """A Read and the creation of the consumer requested for it: what there is to pull, or the
    refusal."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    read: Read = Field(description="The Read.")
    creation: ConsumerCreation = Field(description="The creation of its consumer.")

    @property
    def pulling(self) -> Pulling:
        return PullingConstructor.validate_python(self, from_attributes=True)


class Pulled(BaseModel):
    """A pull and the messages it was answered with, in order."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    pull: Pull = Field(description="The pull.")
    messages: Messages = Field(description="The messages it was answered with.")


class ConsumerInterpreter(BaseModel):
    """A consumer requested: the API's reply is NATS's answer."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )

    action: EphemeralConsumerRequest | DurableConsumerRequest = Field(description="The request.")
    wait: PositiveDuration = Field(description="How long the request waits for its reply.")
    client: Client = Field(exclude=True, repr=False, description="The NATS connection.")

    async def execute(self) -> ConsumerCreation:
        return ConsumerCreation(
            request=self.action,
            reply=ConsumerReplyConstructor.validate_json(
                (
                    await self.client.request(
                        self.action.api.root,
                        self.action.model_dump_json(by_alias=True).encode(),
                        timeout=self.wait.root.total_seconds(),
                    )
                ).data
            ),
        )


class PullInterpreter(BaseModel):
    """A pull made: the request on the consumer's next subject, and the batch it is answered with
    on an inbox."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )

    action: Pull = Field(description="The pull.")
    wait: PositiveDuration = Field(description="How long each message is waited for.")
    client: Client = Field(exclude=True, repr=False, description="The NATS connection.")

    async def execute(self) -> Pulled:
        inbox = await self.client.subscribe(self.client.new_inbox())  # pyright: ignore[reportUnknownMemberType]
        await self.client.publish(
            self.action.api.root,
            self.action.request.model_dump_json().encode(),
            reply=inbox.subject,
        )
        pulled = Pulled(
            pull=self.action,
            messages=Messages(
                tuple(
                    [
                        DeliveredMessage.model_validate(
                            await inbox.next_msg(self.wait.root.total_seconds()),
                            from_attributes=True,
                        )
                        for _ in range(self.action.batch.root)
                    ]
                )
            ),
        )
        await inbox.unsubscribe()
        return pulled
