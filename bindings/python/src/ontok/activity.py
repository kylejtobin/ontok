"""Admissible input/result relationships defining organizational work."""

from pydantic import BaseModel, RootModel

from .outcome import Outcome
from .purpose import Purpose, Together


class ActivityCase[Inputs, Results: Outcome | Together | Purpose](BaseModel):
    """Inputs and the results they admit are declared together."""

    inputs: Inputs | None = None
    outcomes: Results


class Activity[Case: ActivityCase](RootModel[Case]):
    """A whole case, or one of several complete cases in a narrowed declaration."""
