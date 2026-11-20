"""A determination selecting one complete admissible case."""

from pydantic import BaseModel, RootModel

from .outcome import Outcome
from .rule import Rule


class DecisionCase[Context, Target, Result: Outcome](BaseModel):
    """The applicable Rule supplies context; it is never copied separately."""

    rule: Rule[Context, Target]
    outcome: Result


class Decision[Selected: DecisionCase](RootModel[Selected]):
    """The declaration specifies alternatives; construction selects one case."""
