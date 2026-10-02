from pydantic import ConfigDict, Field, RootModel


class BatchId(RootModel[str]):
    """The identifier shared by every message of one atomic batch."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(min_length=1, max_length=64)


class BatchSequenceHeader(RootModel[str]):
    """The text of a Nats-Batch-Sequence header: the place a message holds in its batch."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[1-9]\d*$")


class VersionHeader(RootModel[str]):
    """The text of an Ontok-Version header: the place an occurrence holds in its Stream."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[1-9]\d*$")


class ExpectedSequenceHeader(RootModel[str]):
    """The text of a Nats-Expected-Last-Subject-Sequence header: the sequence the subject is
    expected at, 0 when it is expected to hold none."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^(0|[1-9]\d*)$")
