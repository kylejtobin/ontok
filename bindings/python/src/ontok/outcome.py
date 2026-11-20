"""Outcomes classified by the two ways activity affects a state."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, RootModel

from .type import State


class OutcomeMode(StrEnum):
    """Whether organizational work produces or maintains a state."""

    PRODUCED = "produced"
    MAINTAINED = "maintained"


class ProducedOutcome[Condition](BaseModel):
    """An Outcome in which activity brings about a state."""

    mode: Literal[OutcomeMode.PRODUCED] = Field(
        default=OutcomeMode.PRODUCED,
        description="Identifies an Outcome that produces its state.",
    )
    state: State[Condition] = Field(description="The state brought about by activity.")


class MaintainedOutcome[Condition, Extent](BaseModel):
    """An Outcome in which activity keeps a state true through an extent."""

    mode: Literal[OutcomeMode.MAINTAINED] = Field(
        default=OutcomeMode.MAINTAINED,
        description="Identifies an Outcome that maintains its state.",
    )
    state: State[Condition] = Field(description="The state maintained by activity.")
    extent: Extent = Field(
        description="The domain-defined extent throughout which the state is maintained."
    )


class Outcome(RootModel[ProducedOutcome | MaintainedOutcome]):
    """An Outcome in exactly one produced or maintained form."""

    root: ProducedOutcome | MaintainedOutcome = Field(
        discriminator="mode",
        description="The produced or maintained state, independent of intent or occurrence.",
    )
