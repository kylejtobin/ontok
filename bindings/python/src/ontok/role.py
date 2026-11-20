"""Responsibilities and the distinct relationship of participation."""

from typing import Annotated

from pydantic import BaseModel, Field, RootModel

from .rule import Requirement
from .type import CONFIG


class Responsibility(RootModel[Requirement[object, object]], frozen=True):
    """A required obligation, potentially toward an end rather than a method."""


class Role(RootModel[Annotated[tuple[Responsibility, ...], Field(min_length=1)]], frozen=True):
    """A role exists independently of anyone occupying it."""


class Participation[Occupant, AssignedRole: Role](BaseModel, frozen=True):
    model_config = CONFIG
    occupant: Occupant
    role: AssignedRole
