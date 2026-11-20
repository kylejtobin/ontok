"""States produced or maintained through organizational work."""

from typing import Literal

from pydantic import BaseModel

from .type import State


class Outcome[Condition](BaseModel):
    state: State[Condition]
    mode: Literal["produced", "maintained"]


class ProducedOutcome[Condition](Outcome[Condition]):
    mode: Literal["produced"] = "produced"


class MaintainedOutcome[Condition](Outcome[Condition]):
    mode: Literal["maintained"] = "maintained"
