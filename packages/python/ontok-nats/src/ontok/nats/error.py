from pydantic import ConfigDict, Field, RootModel


class ErrorCode(RootModel[int]):
    """The JetStream error code, `err_code`, that identifies why a request was refused."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=10000, le=19999)
