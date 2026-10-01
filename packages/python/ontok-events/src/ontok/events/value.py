from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ontok.events.position import Version


class Expectation(StrEnum):
    """What is asserted of a Stream when no Version is."""

    NO_STREAM = "no_stream"
    ANY = "any"


class AtVersion(BaseModel):
    """The Stream is at this Version."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    version: Version = Field(description="The Version the Stream is at.")


ExpectedVersion = AtVersion | Expectation


class VersionMismatch(BaseModel):
    """The Stream was not at the expected Version."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    expected: ExpectedVersion = Field(description="What was expected of the Stream.")
    actual: AtVersion | Literal[Expectation.NO_STREAM] = Field(
        description="What was true of the Stream."
    )
