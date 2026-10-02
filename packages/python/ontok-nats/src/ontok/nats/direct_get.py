from enum import StrEnum
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field


class Status(StrEnum):
    """The status header on a direct get reply that carries no message."""

    NO_MESSAGES = "404"


class NoMessages(BaseModel):
    """A direct get reply: the stream holds no message that matches."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    status: Literal[Status.NO_MESSAGES] = Field(validation_alias=AliasPath("headers", "Status"))
