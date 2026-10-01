from pydantic import BaseModel, ConfigDict, Field, RootModel


class ErrorCode(RootModel[int]):
    """The JetStream error code, `err_code`, that identifies why a request was refused."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=10000, le=19999)


class JetStreamError(BaseModel):
    """The error a JetStream API reply carries when the request was refused."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    err_code: ErrorCode = Field(description="Why the request was refused.")


class ApiError(BaseModel):
    """A JetStream API reply that refused the request."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    error: JetStreamError = Field(description="The refusal.")
