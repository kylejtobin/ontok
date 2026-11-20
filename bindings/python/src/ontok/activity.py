"""Admissible work relating its inputs to defined outcomes."""

from pydantic import BaseModel, Field

from .outcome import Outcome
from .purpose import Outcomes, Purpose


class Activity[Inputs](BaseModel):
    """One complete admissible input/result relationship.

    Different permissible input/result relationships are different narrowed
    Activity models; alternatives are formed from those complete models.
    """

    inputs: Inputs | None = Field(
        default=None,
        description=(
            "Admitted inputs, including other work or an Event asserting its result "
            "when this activity depends on that work; absent when no inputs are required."
        ),
    )
    outcomes: Outcome | Outcomes | Purpose = Field(
        description="The Outcome, composition of Outcomes, or Purpose defined by this activity."
    )
