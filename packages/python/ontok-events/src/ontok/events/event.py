from pydantic import AliasPath, BaseModel, ConfigDict, Field, RootModel, SerializeAsAny

from ontok import core
from ontok.core import NodeId
from ontok.events.position import Position, Version


class Occurrence(core.Event):
    """An occurrence the organization declares."""


class Event(BaseModel):
    """An Occurrence as memory holds it: in its Stream, at its Version there and its Position in
    the log."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    occurrence: SerializeAsAny[Occurrence] = Field(description="The occurrence memory holds.")
    stream: NodeId = Field(description="The Stream this Event is in.")
    version: Version = Field(description="The place this Event holds in its Stream.")
    position: Position = Field(description="The place this Event holds in the log.")


class Events(RootModel[tuple[Event, ...]]):
    """The Events of one Stream a read returned, in order."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: tuple[Event, ...] = Field(min_length=1)

    @property
    def events(self) -> tuple[Event, ...]:
        return self.root

    @property
    def last(self) -> Position:
        return LastEvent.model_validate(self, from_attributes=True).event.position


class LastEvent(BaseModel):
    """The last Event of a read."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    event: Event = Field(validation_alias=AliasPath("root", -1))
