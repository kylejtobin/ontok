"""Resulting or intended states, independent of whether they have occurred."""

from typing import Literal

from pydantic import BaseModel

from .type import CONFIG, State


class Outcome[Condition: State[object]](BaseModel, frozen=True):
    model_config = CONFIG
    state: Condition


class ProducedOutcome[Condition: State[object]](Outcome[Condition], frozen=True):
    """Work brings about the specified state."""

    kind: Literal["produced"] = "produced"


class MaintainedOutcome[Condition: State[object]](Outcome[Condition], frozen=True):
    """Work maintains the specified state; duration is not universally required."""

    kind: Literal["maintained"] = "maintained"
