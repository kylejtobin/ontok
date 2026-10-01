from enum import StrEnum
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, Json, TypeAdapter

from ontok.nats.stream import Sequence, StreamName, Subject


class Status(StrEnum):
    """The status header on a direct get reply that carries no message."""

    END_OF_BATCH = "204"
    NO_MESSAGES = "404"


class StoredMessage(BaseModel):
    """A message a stream holds, as a direct get returns it: its headers name where it is."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: StreamName = Field(validation_alias=AliasPath("headers", "Nats-Stream"))
    subject: Subject = Field(validation_alias=AliasPath("headers", "Nats-Subject"))
    sequence: Json[Sequence] = Field(validation_alias=AliasPath("headers", "Nats-Sequence"))


class NoMessages(BaseModel):
    """A direct get reply: the stream holds no message that matches."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    status: Literal[Status.NO_MESSAGES] = Field(validation_alias=AliasPath("headers", "Status"))


class EndOfBatch(BaseModel):
    """A direct get reply: the batch has no more messages."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    status: Literal[Status.END_OF_BATCH] = Field(validation_alias=AliasPath("headers", "Status"))


DirectGetReply = StoredMessage | NoMessages | EndOfBatch
DirectGetReplyConstructor: TypeAdapter[DirectGetReply] = TypeAdapter(DirectGetReply)
