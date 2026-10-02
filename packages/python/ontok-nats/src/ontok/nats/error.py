from typing import Literal

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


class WrongLastSequenceError(BaseModel):
    """The error a publish reply carries when the expected last sequence was wrong."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    err_code: Literal[10071] = Field(description="Wrong last sequence.")


class DuplicateMessageError(BaseModel):
    """The error a publish reply carries when a batch repeats a message id."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    err_code: Literal[10201] = Field(description="Duplicate message id in a batch.")


class DuplicateMessage(BaseModel):
    """A publish reply that refused the batch because a message id was already stored."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    error: DuplicateMessageError = Field(description="The refusal.")


class WrongLastSequence(BaseModel):
    """A publish reply that refused the message because the expected last sequence was wrong."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    error: WrongLastSequenceError = Field(description="The refusal.")
