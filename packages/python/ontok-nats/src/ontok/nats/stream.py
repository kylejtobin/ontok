from typing import Literal

from pydantic import BaseModel, ConfigDict


class StreamSpecification(BaseModel):
    """What the stream that is memory must be: one per account, holding every occurrence, kept
    forever, never deleted or purged, readable directly, and accepting atomic batches."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    name: Literal["EVENTS"]
    subjects: tuple[Literal["event.>"]]
    storage: Literal["file"]
    retention: Literal["limits"]
    deny_delete: Literal[True]
    deny_purge: Literal[True]
    allow_direct: Literal[True]
    allow_atomic: Literal[True]


EVENTS = StreamSpecification(
    name="EVENTS",
    subjects=("event.>",),
    storage="file",
    retention="limits",
    deny_delete=True,
    deny_purge=True,
    allow_direct=True,
    allow_atomic=True,
)
