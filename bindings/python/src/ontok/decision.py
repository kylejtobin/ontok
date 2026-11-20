"""A determination constructed as one complete admissible case."""

from pydantic import BaseModel, Field, RootModel

from .outcome import Outcome
from .rule import Rule


class DecisionCase[Context, Target](BaseModel):
    """An applicable Rule and its resulting Outcome, bound as a complete case."""

    rule: Rule[Context, Target] = Field(
        description="The applicable Rule, including the context in which it governs this case."
    )
    outcome: Outcome = Field(
        description="The resulting Outcome associated with this Rule and its context."
    )


class Decision(RootModel[DecisionCase]):
    """One selected case; alternative complete cases belong to the domain declaration."""

    root: DecisionCase = Field(
        description="The single admissible DecisionCase selected by this Decision."
    )
