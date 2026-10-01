from pydantic import ConfigDict, Field, RootModel


class Version(RootModel[int]):
    """The place an Event holds in its Stream."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=0)


class Position(RootModel[int]):
    """The place an Event holds in the log of every Stream."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=0)
