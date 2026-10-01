from pydantic import ConfigDict, Field, RootModel

from ontok import core
from ontok.core import NodeId
from ontok.events.position import Position, Version


class Event(core.Event):
    """An occurrence in a Stream, at its Version in that Stream and its Position in the log."""

    stream: NodeId = Field(description="The Stream this Event is in.")
    version: Version = Field(description="The place this Event holds in its Stream.")
    position: Position = Field(description="The place this Event holds in the log.")


class Events(RootModel[tuple[Event, ...]]):
    """The Events of one Stream, read whole."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: tuple[Event, ...] = Field(min_length=1)
