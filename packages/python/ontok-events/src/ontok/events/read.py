from typing import Annotated, Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import Action, NodeId
from ontok.events.event import Event, Events
from ontok.events.position import Position
from ontok.events.subscription import FromPosition, Start


class Read(Action):
    """A Stream asked for: whole from its beginning, or what it holds after a Position."""

    stream: NodeId = Field(description="The Stream asked for.")
    after: FromPosition | Literal[Start.BEGINNING] = Field(description="Where the read begins.")


class Frontier(BaseModel):
    """A Stream's frontier: the Position after which it holds no Event."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    position: Position = Field(description="The last Position the Stream holds.")

    @property
    def events(self) -> tuple[Event, ...]:
        return ()

    @property
    def last(self) -> Position:
        return self.position


class NoStream(BaseModel):
    """A Stream that holds no Event."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    @property
    def events(self) -> tuple[Event, ...]:
        return ()


ReadOutcome = Events | Frontier | NoStream
ReadOutcomeConstructor: TypeAdapter[ReadOutcome] = TypeAdapter(ReadOutcome)


class Returned(BaseModel):
    """A read that returned Events: the Stream holds them after the position."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    events: Events = Field(validation_alias=AliasPath("events"))

    @property
    def outcome(self) -> Events:
        return self.events

    @property
    def last(self) -> Position:
        return self.events.last


class AtFrontier(BaseModel):
    """A read after a Position that returned nothing: the Stream's frontier is that Position."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    events: tuple[()] = Field(description="Nothing was returned.")
    after: FromPosition = Field(description="Where the read began.")

    @property
    def outcome(self) -> Frontier:
        return Frontier(position=self.after.position)

    @property
    def last(self) -> Position:
        return self.after.position


class Empty(BaseModel):
    """A read from the beginning that returned nothing: the Stream holds no Event."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    events: tuple[()] = Field(description="Nothing was returned.")
    after: Literal[Start.BEGINNING] = Field(description="Where the read began.")

    @property
    def outcome(self) -> NoStream:
        return NoStream()


Reading = Annotated[Returned | AtFrontier | Empty, Field(union_mode="left_to_right")]
ReadingConstructor: TypeAdapter[Reading] = TypeAdapter(Reading)

Positioned = Annotated[Returned | AtFrontier, Field(union_mode="left_to_right")]
PositionedConstructor: TypeAdapter[Positioned] = TypeAdapter(Positioned)


class Page(BaseModel):
    """What a read of a Stream returned: the Events it holds after a position, in order."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    after: FromPosition | Literal[Start.BEGINNING] = Field(description="Where the read began.")
    events: tuple[Event, ...] = Field(description="The Events returned, in order.")

    @property
    def reading(self) -> Reading:
        return ReadingConstructor.validate_python(self, from_attributes=True)

    @property
    def outcome(self) -> ReadOutcome:
        return self.reading.outcome

    @property
    def last(self) -> Position:
        return PositionedConstructor.validate_python(self, from_attributes=True).last
