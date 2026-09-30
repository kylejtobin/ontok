from typing import Annotated, Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

FOREIGN = ConfigDict(
    frozen=True, strict=True, validate_default=True, revalidate_instances="never", extra="ignore"
)


class Acknowledgement(BaseModel):
    """JetStream's acknowledgement of a publish: the stream and the sequence it landed at. An error
    reply also carries these, so this is what remains when no error is present."""

    model_config = FOREIGN

    stream: str
    seq: int


class ClaimRefused(BaseModel):
    """JetStream's refusal of a claim: error 10071, wrong last sequence, with its description."""

    model_config = FOREIGN

    err_code: Literal[10071] = Field(validation_alias=AliasPath("error", "err_code"))
    refusal: str = Field(validation_alias=AliasPath("error", "description"))


class Failed(BaseModel):
    """Any other JetStream API error, with its description."""

    model_config = FOREIGN

    failure: str = Field(validation_alias=AliasPath("error", "description"))


PublishReply = Annotated[ClaimRefused | Failed | Acknowledgement, Field(union_mode="left_to_right")]
PublishReplyConstructor: TypeAdapter[ClaimRefused | Failed | Acknowledgement] = TypeAdapter(
    PublishReply
)


class Remembered(BaseModel):
    """A direct-get reply carrying an occurrence: its sequence as header text and its body."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    sequence: str = Field(validation_alias=AliasPath("headers", "Nats-Sequence"))
    data: bytes


class NoResults(BaseModel):
    """A direct-get reply that found nothing: status 404."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    status: Literal["404"] = Field(validation_alias=AliasPath("headers", "Status"))


class EndOfBatch(BaseModel):
    """The reply that ends a batched direct get: status 204, with what is still pending."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    status: Literal["204"] = Field(validation_alias=AliasPath("headers", "Status"))
    pending: str = Field(validation_alias=AliasPath("headers", "Nats-Num-Pending"))
    last: str = Field(validation_alias=AliasPath("headers", "Nats-Last-Sequence"))


LatestReply = Annotated[Remembered | NoResults, Field(union_mode="left_to_right")]
LatestReplyConstructor: TypeAdapter[Remembered | NoResults] = TypeAdapter(LatestReply)

BatchReply = Annotated[Remembered | EndOfBatch | NoResults, Field(union_mode="left_to_right")]
BatchReplyConstructor: TypeAdapter[Remembered | EndOfBatch | NoResults] = TypeAdapter(BatchReply)


class LastBySubject(BaseModel):
    """This program's direct-get request for the latest message on a subject."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    last_by_subj: str


class NextBySubject(BaseModel):
    """This program's batched direct-get request: from a sequence, on a subject, this many."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    seq: int
    next_by_subj: str
    batch: int
