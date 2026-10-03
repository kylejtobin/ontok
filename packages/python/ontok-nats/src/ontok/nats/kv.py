from typing import Annotated, Literal

from pydantic import (
    AliasChoices,
    AliasPath,
    Base64Bytes,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    TypeAdapter,
)

from nats.aio.client import Client
from ontok.core import NodeId, PositiveDuration
from ontok.events import Outcome, PersistReadModel, ReadModel, ReadModelLookup
from ontok.nats.batch import ExpectedSequenceHeader
from ontok.nats.error import ApiError, WrongLastSequence
from ontok.nats.publish import PubAck, PublishReply, PublishReplyConstructor
from ontok.nats.stream import Subject


class Bucket(RootModel[str]):
    """The name of a key-value bucket."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")


class Key(RootModel[str]):
    """A key in a bucket."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[-/_=.a-zA-Z0-9]+$")


class Revision(RootModel[int]):
    """The revision of a key: the sequence of its entry in the bucket. The first is 1."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class ReadModelKey(BaseModel):
    """The key a ReadModel is held under: its identity."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    id: NodeId = Field(description="The ReadModel.")

    @property
    def key(self) -> Key:
        return Key(self.id.root)


class Entry(BaseModel):
    """The last message on a key, as the Get Message API returns it: a value at a revision."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    seq: Revision = Field(validation_alias=AliasPath("message", "seq"))
    data: Base64Bytes = Field(validation_alias=AliasPath("message", "data"))

    @property
    def expected(self) -> ExpectedSequenceHeader:
        return ExpectedSequenceHeader(f"{self.seq.root}")


class Deleted(BaseModel):
    """The last message on a key, as the Get Message API returns it: the key was deleted or
    purged, so the message carries no value."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    seq: Revision = Field(validation_alias=AliasPath("message", "seq"))

    @property
    def expected(self) -> ExpectedSequenceHeader:
        return ExpectedSequenceHeader(f"{self.seq.root}")


KvReply = Annotated[Entry | Deleted | ApiError, Field(union_mode="left_to_right")]
KvReplyConstructor: TypeAdapter[KvReply] = TypeAdapter(KvReply)


class NoEntry(BaseModel):
    """A key that has never held a message: the API found none."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    err_code: Literal[10037] = Field(validation_alias=AliasPath("error", "err_code", "root"))

    @property
    def expected(self) -> ExpectedSequenceHeader:
        return ExpectedSequenceHeader("0")


Prior = Annotated[Entry | Deleted | NoEntry, Field(union_mode="left_to_right")]
PriorConstructor: TypeAdapter[Prior] = TypeAdapter(Prior)


class ExpectedHeaders(BaseModel):
    """The header asserting the sequence a subject is expected at."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    expected: ExpectedSequenceHeader = Field(
        serialization_alias="Nats-Expected-Last-Subject-Sequence"
    )


class NewEntry(BaseModel):
    """A ReadModel as NATS receives it: a value put on its key, expected after the entry the
    key last held."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    bucket: Bucket = Field(description="The bucket.")
    action: PersistReadModel = Field(description="The ReadModel to record.")
    prior: Prior = Field(description="What the key last held.")

    @property
    def read_model(self) -> ReadModel:
        return self.action.read_model

    @property
    def subject(self) -> Subject:
        return Subject(f"$KV.{self.bucket.root}.{ReadModelKey(id=self.read_model.id).key.root}")

    @property
    def headers(self) -> ExpectedHeaders:
        return ExpectedHeaders(expected=self.prior.expected)


class EntryAck(BaseModel):
    """An entry and the acknowledgement of its put: the ReadModel is held."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    entry: NewEntry = Field(description="The entry.")
    ack: PubAck = Field(
        validation_alias=AliasChoices("ack", "reply"),
        description="The acknowledgement of its put.",
    )

    @property
    def read_model(self) -> ReadModel:
        return self.entry.read_model

    @property
    def outcome(self) -> Outcome:
        return Outcome.COMPLETE


class EntryRefusal(BaseModel):
    """An entry and the refusal of its put: the key was not at the expected revision."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    entry: NewEntry = Field(description="The entry.")
    error: WrongLastSequence = Field(
        validation_alias=AliasChoices("error", "reply"), description="The refusal."
    )

    @property
    def outcome(self) -> Outcome:
        return Outcome.RETURNED


Keeping = Annotated[EntryAck | EntryRefusal, Field(union_mode="left_to_right")]
KeepingConstructor: TypeAdapter[Keeping] = TypeAdapter(Keeping)


class EntryReply(BaseModel):
    """An entry and NATS's reply to its put: held, or refused, chosen by what came back."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    entry: NewEntry = Field(description="The entry.")
    reply: PublishReply = Field(description="NATS's reply to its put.")

    @property
    def keeping(self) -> Keeping:
        return KeepingConstructor.validate_python(self, from_attributes=True)


class LastBySubject(BaseModel):
    """A Get Message request for the last message on one subject."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    last_by_subj: Subject = Field(description="The subject.")


class KeyLookup(BaseModel):
    """A ReadModelLookup as NATS receives it: the last message on the key in the bucket."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    bucket: Bucket = Field(description="The bucket.")
    action: ReadModelLookup = Field(description="The ReadModel asked for.")

    @property
    def subject(self) -> Subject:
        return Subject(f"$KV.{self.bucket.root}.{ReadModelKey(id=self.action.id).key.root}")

    @property
    def api(self) -> Subject:
        return Subject(f"$JS.API.STREAM.MSG.GET.KV_{self.bucket.root}")

    @property
    def body(self) -> LastBySubject:
        return LastBySubject(last_by_subj=self.subject)


class LookupReply(BaseModel):
    """A lookup and NATS's reply to it: what the key last held, which a put is expected after."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    lookup: KeyLookup = Field(description="The lookup.")
    reply: KvReply = Field(description="NATS's reply to it.")

    @property
    def prior(self) -> Prior:
        return PriorConstructor.validate_python(self.reply, from_attributes=True)


class EntryInterpreter(BaseModel):
    """An entry put: the publish reply is NATS's answer."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )

    action: NewEntry = Field(description="The entry to put.")
    wait: PositiveDuration = Field(description="How long the put waits for its reply.")
    client: Client = Field(exclude=True, repr=False, description="The NATS connection.")

    async def execute(self) -> EntryReply:
        return EntryReply(
            entry=self.action,
            reply=PublishReplyConstructor.validate_json(
                (
                    await self.client.request(
                        self.action.subject.root,
                        self.action.read_model.model_dump_json().encode(),
                        headers=self.action.headers.model_dump(by_alias=True),
                        timeout=self.wait.root.total_seconds(),
                    )
                ).data
            ),
        )


class MessageGetInterpreter(BaseModel):
    """A key looked up: the Get Message reply is NATS's answer."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )

    action: KeyLookup = Field(description="The lookup.")
    wait: PositiveDuration = Field(description="How long the lookup waits for its reply.")
    client: Client = Field(exclude=True, repr=False, description="The NATS connection.")

    async def execute(self) -> LookupReply:
        return LookupReply(
            lookup=self.action,
            reply=KvReplyConstructor.validate_json(
                (
                    await self.client.request(
                        self.action.api.root,
                        self.action.body.model_dump_json().encode(),
                        timeout=self.wait.root.total_seconds(),
                    )
                ).data
            ),
        )
