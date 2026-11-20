"""Units of work with correlated admitted inputs and defined outcomes."""

from pydantic import BaseModel

from .outcome import Outcome
from .purpose import Purpose
from .type import CONFIG, State


class Activity[Inputs, Results: Outcome[State[object]] | Purpose](BaseModel, frozen=True):
    """One whole admissible case; alternatives are unions of complete narrowings."""

    model_config = CONFIG
    inputs: Inputs
    outcomes: Results
