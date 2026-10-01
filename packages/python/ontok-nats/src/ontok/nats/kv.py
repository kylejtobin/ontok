from enum import StrEnum

from pydantic import ConfigDict, Field, RootModel


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
