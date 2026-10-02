from pydantic import BaseModel, ConfigDict, Field, RootModel

from ontok.core import NodeId


class StreamName(RootModel[str]):
    """The name of a stream: no whitespace, period, asterisk, greater-than, or slash."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[^\s.*>/\\]+$")


class Sequence(RootModel[int]):
    """The sequence number a stream assigns to a message. The first message is 1."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class Subject(RootModel[str]):
    """A subject a message is published to: dot-separated tokens with no wildcard."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[^\s.*>]+(\.[^\s.*>]+)*$")


class FilterSubject(RootModel[str]):
    """A subject that selects messages: tokens, `*` for one token, `>` for the remainder."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^(([^\s.*>]+|\*)\.)*([^\s.*>]+|\*|>)$")


class EventSubject(BaseModel):
    """The subject the occurrences of one Stream are published to: `event.` and the Stream's
    identity."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: NodeId = Field(description="The Stream.")

    @property
    def subject(self) -> Subject:
        return Subject(f"event.{self.stream.root}")
