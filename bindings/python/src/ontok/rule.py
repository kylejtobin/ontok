"""Contextual requirements, permissions, prohibitions, and validity."""

from typing import Literal

from pydantic import BaseModel

from .type import CONFIG


class Rule[Context, Target](BaseModel, frozen=True):
    model_config = CONFIG
    context: Context
    target: Target


class Validity[Context, Target](Rule[Context, Target], frozen=True):
    force: Literal["valid"] = "valid"


class Permission[Context, Target](Rule[Context, Target], frozen=True):
    force: Literal["permitted"] = "permitted"


class Requirement[Context, Target](Rule[Context, Target], frozen=True):
    force: Literal["required"] = "required"


class Prohibition[Context, Target](Rule[Context, Target], frozen=True):
    force: Literal["prohibited"] = "prohibited"
