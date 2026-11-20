"""Selections of a complete admissible context, rule and result case."""

from pydantic import BaseModel, RootModel

from .outcome import Outcome
from .rule import Rule
from .type import CONFIG, State


class DecisionCase[Context, ApplicableRule: Rule[object, object], Result: Outcome[State[object]]](
    BaseModel, frozen=True
):
    """One inseparable admissible context, applicable rule and outcome."""

    model_config = CONFIG
    context: Context
    rule: ApplicableRule
    outcome: Result


class Decision[Cases: DecisionCase[object, Rule[object, object], Outcome[State[object]]]](
    RootModel[Cases], frozen=True
):
    """A concrete declaration supplies alternative complete cases; one is selected."""
