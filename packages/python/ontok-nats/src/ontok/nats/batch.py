from pydantic import ConfigDict, Field, RootModel


class BatchId(RootModel[str]):
    """The identifier shared by every message of one atomic batch."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(min_length=1, max_length=64)


class BatchSequence(RootModel[int]):
    """The place a message holds in its atomic batch. The first message is 1."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)
