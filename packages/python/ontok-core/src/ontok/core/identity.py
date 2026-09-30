from pydantic import ConfigDict, Field, RootModel


class NodeId(RootModel[str]):
    """A canonical UUIDv7 identifier that distinguishes a Node."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    )
