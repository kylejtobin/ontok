from asyncio import gather
from typing import Annotated, Literal

from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    TypeAdapter,
)

from nats.aio.client import Client
from ontok.core import NodeId, PositiveDuration
from ontok.events import (
    Append,
    AppendOutcome,
    Initial,
    Occurrence,
    Position,
    State,
    Version,
    VersionMismatch,
)
from ontok.nats.batch import BatchId, BatchSequenceHeader, ExpectedSequenceHeader, VersionHeader
from ontok.nats.error import ApiError, DuplicateMessage, WrongLastSequence
from ontok.nats.stream import EventSubject, Sequence, Subject


class PubAck(BaseModel):
    """The acknowledgement of a publish: the sequence the message landed at."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    seq: Sequence = Field(description="The sequence the message landed at.")


PublishReply = PubAck | WrongLastSequence | DuplicateMessage | ApiError
PublishReplyConstructor: TypeAdapter[PublishReply] = TypeAdapter(PublishReply)


class BatchHeaders(BaseModel):
    """The headers of a following message of a batch: which batch, and its place in it."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: NodeId = Field(serialization_alias="Ontok-Stream")
    version: VersionHeader = Field(
        validation_alias=AliasPath("version"), serialization_alias="Ontok-Version"
    )
    msg_id: NodeId = Field(
        validation_alias=AliasPath("payload", "id"), serialization_alias="Nats-Msg-Id"
    )
    batch_id: BatchId = Field(serialization_alias="Nats-Batch-Id")
    batch_sequence: BatchSequenceHeader = Field(
        validation_alias=AliasPath("place"), serialization_alias="Nats-Batch-Sequence"
    )


class OpeningHeaders(BaseModel):
    """The headers of the opening message of a batch: which batch, place 1, and the sequence
    the subject is expected at."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: NodeId = Field(serialization_alias="Ontok-Stream")
    version: VersionHeader = Field(
        validation_alias=AliasPath("version"), serialization_alias="Ontok-Version"
    )
    msg_id: NodeId = Field(
        validation_alias=AliasPath("payload", "id"), serialization_alias="Nats-Msg-Id"
    )
    batch_id: BatchId = Field(serialization_alias="Nats-Batch-Id")
    batch_sequence: Literal["1"] = Field(default="1", serialization_alias="Nats-Batch-Sequence")
    expected: ExpectedSequenceHeader = Field(
        validation_alias=AliasPath("expected", "header"),
        serialization_alias="Nats-Expected-Last-Subject-Sequence",
    )


class ClosingHeaders(BaseModel):
    """The headers of the last message of a batch: which batch, its place, and that it commits
    the batch."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: NodeId = Field(serialization_alias="Ontok-Stream")
    version: VersionHeader = Field(
        validation_alias=AliasPath("version"), serialization_alias="Ontok-Version"
    )
    msg_id: NodeId = Field(
        validation_alias=AliasPath("payload", "id"), serialization_alias="Nats-Msg-Id"
    )
    batch_id: BatchId = Field(serialization_alias="Nats-Batch-Id")
    batch_sequence: BatchSequenceHeader = Field(
        validation_alias=AliasPath("place"), serialization_alias="Nats-Batch-Sequence"
    )
    commit: Literal["1"] = Field(default="1", serialization_alias="Nats-Batch-Commit")


class OpeningClosingHeaders(BaseModel):
    """The headers of a batch of one message: it opens, carries the expectation, and commits."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: NodeId = Field(serialization_alias="Ontok-Stream")
    version: VersionHeader = Field(
        validation_alias=AliasPath("version"), serialization_alias="Ontok-Version"
    )
    msg_id: NodeId = Field(
        validation_alias=AliasPath("payload", "id"), serialization_alias="Nats-Msg-Id"
    )
    batch_id: BatchId = Field(serialization_alias="Nats-Batch-Id")
    batch_sequence: Literal["1"] = Field(
        validation_alias=AliasPath("place", "root"), serialization_alias="Nats-Batch-Sequence"
    )
    expected: ExpectedSequenceHeader = Field(
        validation_alias=AliasPath("expected", "header"),
        serialization_alias="Nats-Expected-Last-Subject-Sequence",
    )
    commit: Literal["1"] = Field(default="1", serialization_alias="Nats-Batch-Commit")


ClosingHeadersOf = Annotated[
    OpeningClosingHeaders | ClosingHeaders, Field(union_mode="left_to_right")
]
ClosingHeadersOfConstructor: TypeAdapter[ClosingHeadersOf] = TypeAdapter(ClosingHeadersOf)


OpeningOrBatchHeaders = Annotated[OpeningHeaders | BatchHeaders, Field(union_mode="left_to_right")]
OpeningOrBatchHeadersConstructor: TypeAdapter[OpeningOrBatchHeaders] = TypeAdapter(
    OpeningOrBatchHeaders
)


class LastSequence(BaseModel):
    """A batch whose Append asserts its Stream is at a Version: the last Event's position is
    the sequence its subject is expected at."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    version: Version = Field(validation_alias=AliasPath("append", "expected", "version"))
    last_position: Position = Field(validation_alias=AliasPath("prior", "event", "position"))

    @property
    def header(self) -> ExpectedSequenceHeader:
        return ExpectedSequenceHeader(f"{self.last_position.root}")


class ZeroSequence(BaseModel):
    """A batch whose Append asserts its Stream does not exist: its subject is expected at 0."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["no_stream"] = Field(validation_alias=AliasPath("append", "expected", "value"))

    @property
    def header(self) -> ExpectedSequenceHeader:
        return ExpectedSequenceHeader("0")


class NoExpectation(BaseModel):
    """A batch whose Append asserts nothing of its Stream: the opening message expects no
    sequence."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["any"] = Field(validation_alias=AliasPath("append", "expected", "value"))


ExpectedSequence = LastSequence | ZeroSequence | NoExpectation
ExpectedSequenceConstructor: TypeAdapter[ExpectedSequence] = TypeAdapter(ExpectedSequence)


class Placed(BaseModel):
    """An occurrence at its place in a batch."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    batch: "Batch" = Field(description="The batch.")
    occurrence: SerializeAsAny[Occurrence] = Field(description="The occurrence.")
    place: BatchSequenceHeader = Field(description="Its place in the batch.")
    version: VersionHeader = Field(description="The Version it will hold in its Stream.")


class Opening(BaseModel):
    """The opening message of a batch: the first occurrence, with what the batch expects."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subject: Subject = Field(validation_alias=AliasPath("batch", "subject"))
    stream: NodeId = Field(validation_alias=AliasPath("batch", "append", "stream"))
    batch_id: BatchId = Field(validation_alias=AliasPath("batch", "batch_id"))
    expected: ExpectedSequence = Field(validation_alias=AliasPath("batch", "expected"))
    place: Literal["1"] = Field(validation_alias=AliasPath("place", "root"))
    version: VersionHeader = Field(validation_alias=AliasPath("version"))
    payload: SerializeAsAny[Occurrence] = Field(validation_alias=AliasPath("occurrence"))

    @property
    def headers(self) -> "OpeningOrBatchHeaders":
        return OpeningOrBatchHeadersConstructor.validate_python(self, from_attributes=True)


class Following(BaseModel):
    """A following message of a batch: a later occurrence at its place."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subject: Subject = Field(validation_alias=AliasPath("batch", "subject"))
    stream: NodeId = Field(validation_alias=AliasPath("batch", "append", "stream"))
    batch_id: BatchId = Field(validation_alias=AliasPath("batch", "batch_id"))
    place: BatchSequenceHeader = Field(validation_alias=AliasPath("place"))
    version: VersionHeader = Field(validation_alias=AliasPath("version"))
    payload: SerializeAsAny[Occurrence] = Field(validation_alias=AliasPath("occurrence"))

    @property
    def headers(self) -> BatchHeaders:
        return BatchHeaders.model_validate(self, from_attributes=True)


Message = Annotated[Opening | Following, Field(union_mode="left_to_right")]
MessageConstructor: TypeAdapter[Message] = TypeAdapter(Message)


class LastOccurrence(BaseModel):
    """The last occurrence of an Append."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    occurrence: SerializeAsAny[Occurrence] = Field(validation_alias=AliasPath("root", -1))


class Closing(BaseModel):
    """The last message of a batch: the last occurrence at its place, committing the batch."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subject: Subject = Field(validation_alias=AliasPath("batch", "subject"))
    stream: NodeId = Field(validation_alias=AliasPath("batch", "append", "stream"))
    batch_id: BatchId = Field(validation_alias=AliasPath("batch", "batch_id"))
    expected: ExpectedSequence = Field(validation_alias=AliasPath("batch", "expected"))
    place: BatchSequenceHeader = Field(validation_alias=AliasPath("place"))
    version: VersionHeader = Field(validation_alias=AliasPath("version"))
    payload: SerializeAsAny[Occurrence] = Field(validation_alias=AliasPath("occurrence"))

    @property
    def headers(self) -> ClosingHeadersOf:
        return ClosingHeadersOfConstructor.validate_python(self, from_attributes=True)


class Batch(BaseModel):
    """An Append as NATS receives it: its occurrences as the messages of one atomic batch,
    under what the fold it was declared from says the Stream last holds."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    append: Append = Field(description="The Append.")
    prior: Initial | State = Field(description="The fold the Append was declared from.")

    @property
    def batch_id(self) -> BatchId:
        return BatchId(self.append.id.root)

    @property
    def subject(self) -> Subject:
        return EventSubject(stream=self.append.stream).subject

    @property
    def expected(self) -> ExpectedSequence:
        return ExpectedSequenceConstructor.validate_python(self, from_attributes=True)

    @property
    def messages(self) -> tuple[Message, ...]:
        return tuple(
            MessageConstructor.validate_python(
                Placed(
                    batch=self,
                    occurrence=occurrence,
                    place=BatchSequenceHeader(f"{place}"),
                    version=VersionHeader(f"{self.prior.version.root + place}"),
                ),
                from_attributes=True,
            )
            for occurrence, place in zip(
                self.append.occurrences.root,
                range(1, len(self.append.occurrences.root)),
                strict=False,
            )
        )

    @property
    def closing(self) -> Closing:
        return Closing.model_validate(
            Placed(
                batch=self,
                occurrence=LastOccurrence.model_validate(
                    self.append.occurrences, from_attributes=True
                ).occurrence,
                place=BatchSequenceHeader(f"{len(self.append.occurrences.root)}"),
                version=VersionHeader(
                    f"{self.prior.version.root + len(self.append.occurrences.root)}"
                ),
            ),
            from_attributes=True,
        )


Placed.model_rebuild()


class BatchAck(BaseModel):
    """A batch and the acknowledgement of its commit: the position the Stream is now at."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    batch: Batch = Field(description="The batch.")
    ack: PubAck = Field(
        validation_alias=AliasChoices("ack", "reply"),
        description="The acknowledgement of its commit.",
    )

    @property
    def position(self) -> Position:
        return Position(self.ack.seq.root)

    @property
    def outcome(self) -> AppendOutcome:
        return self.position


class BatchRefusal(BaseModel):
    """A batch and the refusal of its commit: the Stream was not at the expected Version."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    batch: Batch = Field(description="The batch.")
    error: WrongLastSequence = Field(
        validation_alias=AliasChoices("error", "reply"), description="The refusal."
    )

    @property
    def mismatch(self) -> VersionMismatch:
        return VersionMismatch.model_validate(self.batch.append, from_attributes=True)

    @property
    def outcome(self) -> AppendOutcome:
        return self.mismatch


class BatchDuplicate(BaseModel):
    """A batch and the refusal of its commit: an occurrence in it was already stored. NATS
    refuses where the pattern would acknowledge; the stream holds the occurrence once."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    batch: Batch = Field(description="The batch.")
    error: DuplicateMessage = Field(
        validation_alias=AliasChoices("error", "reply"), description="The refusal."
    )

    @property
    def outcome(self) -> DuplicateMessage:
        return self.error


class ProviderRefusal(BaseModel):
    """A batch and a reply that is no outcome of event sourcing: a limit, a permission, or an
    error the provider names and the pattern does not."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    batch: Batch = Field(description="The batch.")
    error: ApiError = Field(
        validation_alias=AliasChoices("error", "reply"), description="The provider's refusal."
    )

    @property
    def outcome(self) -> ApiError:
        return self.error


Landing = Annotated[
    BatchAck | BatchRefusal | BatchDuplicate | ProviderRefusal, Field(union_mode="left_to_right")
]
LandingConstructor: TypeAdapter[Landing] = TypeAdapter(Landing)


class BatchReply(BaseModel):
    """A batch and NATS's reply to its commit: the Append's outcome, chosen by what came back."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    batch: Batch = Field(description="The batch.")
    reply: PublishReply = Field(description="NATS's reply to its commit.")

    @property
    def landing(self) -> Landing:
        return LandingConstructor.validate_python(self, from_attributes=True)

    @property
    def outcome(self) -> AppendOutcome | DuplicateMessage | ApiError:
        return self.landing.outcome


class BatchInterpreter(BaseModel):
    """A batch published: its messages, then its closing message, whose reply is NATS's answer."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )

    action: Batch = Field(description="The batch to publish.")
    wait: PositiveDuration = Field(description="How long the commit waits for its reply.")
    client: Client = Field(exclude=True, repr=False, description="The NATS connection.")

    async def execute(self) -> PublishReply:
        await gather(
            *(
                self.client.publish(
                    message.subject.root,
                    message.payload.model_dump_json().encode(),
                    headers=message.headers.model_dump(by_alias=True),
                )
                for message in self.action.messages
            )
        )
        return PublishReplyConstructor.validate_json(
            (
                await self.client.request(
                    self.action.closing.subject.root,
                    self.action.closing.payload.model_dump_json().encode(),
                    headers=self.action.closing.headers.model_dump(by_alias=True),
                    timeout=self.wait.root.total_seconds(),
                )
            ).data
        )
