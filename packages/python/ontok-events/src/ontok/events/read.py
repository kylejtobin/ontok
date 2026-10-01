from typing import Literal

from pydantic import Field, TypeAdapter

from ontok.core import Action, NodeId
from ontok.events.event import Events
from ontok.events.value import Expectation


class Read(Action):
    """A Stream asked for whole."""

    stream: NodeId = Field(description="The Stream asked for.")


ReadOutcome = Events | Literal[Expectation.NO_STREAM]
ReadOutcomeConstructor: TypeAdapter[ReadOutcome] = TypeAdapter(ReadOutcome)
