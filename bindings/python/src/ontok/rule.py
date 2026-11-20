"""Rules and their closed set of normative forces."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class RuleForce(StrEnum):
    """The four universally defined ways a Rule can govern a target."""

    VALID = "valid"
    PERMITTED = "permitted"
    REQUIRED = "required"
    PROHIBITED = "prohibited"


class Rule[Context, Target](BaseModel):
    """A constraint or requirement governing a target in a context."""

    context: Context = Field(description="The context in which this rule applies.")
    target: Target = Field(description="The matter governed by this rule.")
    force: RuleForce = Field(description="What the rule declares about its target.")


class Validity[Context, Target](Rule[Context, Target]):
    """A Rule declaring its target valid."""

    force: Literal[RuleForce.VALID] = Field(
        default=RuleForce.VALID, description="The rule's valid force."
    )


class Permission[Context, Target](Rule[Context, Target]):
    """A Rule permitting its target."""

    force: Literal[RuleForce.PERMITTED] = Field(
        default=RuleForce.PERMITTED, description="The rule's permitted force."
    )


class Requirement[Context, Target](Rule[Context, Target]):
    """A Rule requiring its target."""

    force: Literal[RuleForce.REQUIRED] = Field(
        default=RuleForce.REQUIRED, description="The rule's required force."
    )


class Prohibition[Context, Target](Rule[Context, Target]):
    """A Rule prohibiting its target."""

    force: Literal[RuleForce.PROHIBITED] = Field(
        default=RuleForce.PROHIBITED, description="The rule's prohibited force."
    )
