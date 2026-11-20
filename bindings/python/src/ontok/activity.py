"""Complete admissible input/result cases defining organizational work."""

from pydantic import BaseModel, Field, RootModel

from .outcome import Outcome
from .purpose import Outcomes, Purpose


class ActivityCase[Inputs, Results: Outcome | Outcomes | Purpose](BaseModel):
    """One permissible combination of inputs and their defined results."""

    inputs: Inputs | None = Field(
        default=None,
        description=(
            "The inputs admitted for this case, including preceding Activities or Events "
            "when they establish dependencies; absent when the activity needs no input."
        ),
    )
    outcomes: Results = Field(
        description="The Outcome, composition of Outcomes, or Purpose defined for these inputs."
    )


class Activity[Case: ActivityCase](RootModel[Case]):
    """A unit of work defined by one complete admissible case."""

    root: Case = Field(
        description=(
            "The admitted input/result case. An organization's specialization can "
            "admit alternatives by declaring a union of complete cases."
        )
    )
