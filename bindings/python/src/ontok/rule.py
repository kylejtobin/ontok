"""Normative force governing a target in a stated context."""

from typing import Literal

from pydantic import BaseModel, Field


class Rule[Context, Target](BaseModel):
    """What is valid, permitted, required, or prohibited in a context."""

    context: Context = Field(description="The context in which this rule applies.")
    target: Target = Field(description="The matter governed by this rule.")
    force: Literal["valid", "permitted", "required", "prohibited"] = Field(
        description="The normative effect of this rule upon its target."
    )


class Validity[Context, Target](Rule[Context, Target]):
    """A declaration of what is valid."""

    force: Literal["valid"] = Field(default="valid", description="Declares the target valid.")


class Permission[Context, Target](Rule[Context, Target]):
    """A declaration of what is permitted."""

    force: Literal["permitted"] = Field(
        default="permitted", description="Permits the target in the stated context."
    )


class Requirement[Context, Target](Rule[Context, Target]):
    """A declaration of what is required."""

    force: Literal["required"] = Field(
        default="required", description="Requires the target in the stated context."
    )


class Prohibition[Context, Target](Rule[Context, Target]):
    """A declaration of what is prohibited."""

    force: Literal["prohibited"] = Field(
        default="prohibited", description="Prohibits the target in the stated context."
    )
