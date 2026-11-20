"""Selection of a complete admissible rule-and-result case."""

from pydantic import BaseModel, RootModel

from .outcome import Outcome
from .rule import Rule


class DecisionCase[Applicable: Rule, Result: Outcome](BaseModel):
    """Context is already present in the rule; never copy it independently."""

    rule: Applicable
    outcome: Result


class Decision[Case: DecisionCase](RootModel[Case]):
    """Declared Case may be a union of complete cases; construction selects one."""
