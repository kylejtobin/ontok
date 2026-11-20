"""Duties associated with participation, independent of occupancy."""

from typing import Annotated

from pydantic import BaseModel, Field, RootModel

from .rule import Requirement


class Responsibility[Context, Obligation](RootModel[Requirement[Context, Obligation]]):
    """A duty derived from a requirement, not a mandated performance method."""


class Role(RootModel[Annotated[tuple[Responsibility, ...], Field(min_length=1)]]):
    """One or more responsibilities; occupancy is a separate assertion."""


class Participation[Occupant, Assigned: Role](BaseModel):
    occupant: Occupant
    role: Assigned
