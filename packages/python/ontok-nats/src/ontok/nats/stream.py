from pydantic import ConfigDict, Field, RootModel


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
