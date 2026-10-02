from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import Action, NodeId
from ontok.events.event import Events
from ontok.events.position import Position
from ontok.events.subscription import FromPosition, Start
from ontok.events.value import Expectation


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


ReadOutcome = Events | Frontier | Literal[Expectation.NO_STREAM]
ReadOutcomeConstructor: TypeAdapter[ReadOutcome] = TypeAdapter(ReadOutcome)
