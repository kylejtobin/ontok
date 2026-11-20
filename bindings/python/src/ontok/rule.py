"""Contextual normative constraints."""

from typing import Literal

from pydantic import BaseModel


class Rule[Context, Target](BaseModel):
    context: Context
    target: Target
    force: Literal["valid", "permitted", "required", "prohibited"]


class Validity[Context, Target](Rule[Context, Target]):
    force: Literal["valid"] = "valid"


class Permission[Context, Target](Rule[Context, Target]):
    force: Literal["permitted"] = "permitted"


class Requirement[Context, Target](Rule[Context, Target]):
    force: Literal["required"] = "required"


class Prohibition[Context, Target](Rule[Context, Target]):
    force: Literal["prohibited"] = "prohibited"
