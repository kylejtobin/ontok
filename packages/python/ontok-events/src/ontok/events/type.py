from enum import StrEnum

from pydantic import ConfigDict, Field, RootModel


class EventTypeName(RootModel[str]):
    """The interchange identity of a kind of occurrence: the declaring namespace and the class."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[a-z][a-z0-9_]*-[A-Z][A-Za-z0-9]*$")


class WorkTypeName(RootModel[str]):
    """The interchange identity of a responsibility: the declaring namespace and the class."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[a-z][a-z0-9_]*-[A-Z][A-Za-z0-9]*$")


class LogSequence(RootModel[int]):
    """The position of a remembered occurrence in memory."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class Ordinal(RootModel[int]):
    """The position of an emission among a response's emissions."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=0, le=999)


class Digest(RootModel[str]):
    """The SHA-256 of some content in lowercase hex: the identity of a thing that is its content."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[0-9a-f]{64}$")


class DeliveryToken(RootModel[str]):
    """The provider's acknowledgement address for one delivery."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^\S+$")


class ClaimRefusal(RootModel[str]):
    """Memory's account of why an append's claim did not hold."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(min_length=1)


class FailureReason(RootModel[str]):
    """A provider's or a capability's account of why an effect did not complete."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(min_length=1)


class Disposition(StrEnum):
    """What remains for an append's author: nothing, another attempt, or a terminal refusal."""

    COMPLETE = "complete"
    RETRY = "retry"
    REJECT = "reject"
