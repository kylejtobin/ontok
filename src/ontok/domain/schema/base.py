from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


OntokId = str
OntokLabel = str
OntokDescription = str
OntokNote = str
OntokMetadata = dict[str, Any]


class OntokModel(BaseModel):
    """Base class for immutable ONTOK schema objects."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: OntokId = Field(min_length=1)
    label: OntokLabel = Field(min_length=1)
    description: OntokDescription | None = None
    metadata: OntokMetadata = Field(default_factory=dict)

    @field_validator("id", "label")
    @classmethod
    def _strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank")
        return stripped


class TimeInterval(BaseModel):
    """Optional interval for time-scoped knowledge."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def _ends_after_start(self) -> "TimeInterval":
        if self.starts_at is not None and self.ends_at is not None and self.ends_at < self.starts_at:
            raise ValueError("ends_at must be greater than or equal to starts_at")
        return self
