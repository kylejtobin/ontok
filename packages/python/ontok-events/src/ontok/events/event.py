from pydantic import BaseModel, ConfigDict, Field, RootModel

from ontok import core
from ontok.core import NodeId
from ontok.events.position import Position, Version


class Occurrence(core.Event):
    """An occurrence at its Version in a Stream."""

    version: Version = Field(description="The place this occurrence holds in its Stream.")


class Event(BaseModel):
    """An Occurrence as memory holds it: in its Stream, at its Position in the log."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    occurrence: Occurrence = Field(description="The occurrence memory holds.")
    stream: NodeId = Field(description="The Stream this Event is in.")
    position: Position = Field(description="The place this Event holds in the log.")


class Events(RootModel[tuple[Event, ...]]):
    """The Events of one Stream, read whole."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: tuple[Event, ...] = Field(min_length=1)
