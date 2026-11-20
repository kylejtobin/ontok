"""Decisions choose one complete admissible context/rule/outcome case."""

from pydantic import BaseModel, Field, RootModel

from .outcome import Outcome
from .rule import Rule


class DecisionCase[Context, Target](BaseModel):
    """A single applicable Rule with its resulting Outcome."""

    rule: Rule[Context, Target] = Field(
        description="The applicable Rule, which already carries its context and target."
    )
    outcome: Outcome = Field(
        description="The Outcome selected under that Rule in its stated context."
    )


class Decision[Case: DecisionCase](RootModel[Case]):
    """One selected complete case from the alternatives allowed by a declaration."""

    root: Case = Field(
        description="The selected Rule/Outcome case, never separately mixed alternatives."
    )
