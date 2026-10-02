from enum import StrEnum
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, Json, RootModel, TypeAdapter

from ontok.core import NodeId
from ontok.nats.direct_get import NoMessages


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


class Operation(StrEnum):
    """What an entry did to its key."""

    PUT = "PUT"
    DEL = "DEL"
    PURGE = "PURGE"


class Entry(BaseModel):
    """The last entry on a key, as a direct get returns it: a value put at a revision."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    revision: Json[Revision] = Field(validation_alias=AliasPath("headers", "Nats-Sequence"))
    operation: Literal[Operation.PUT] = Field(
        default=Operation.PUT, validation_alias=AliasPath("headers", "KV-Operation")
    )


class Deleted(BaseModel):
    """The last entry on a key, as a direct get returns it: the key was deleted or purged."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    revision: Json[Revision] = Field(validation_alias=AliasPath("headers", "Nats-Sequence"))
    operation: Literal[Operation.DEL, Operation.PURGE] = Field(
        validation_alias=AliasPath("headers", "KV-Operation")
    )


KvReply = Entry | Deleted | NoMessages
KvReplyConstructor: TypeAdapter[KvReply] = TypeAdapter(KvReply)


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
