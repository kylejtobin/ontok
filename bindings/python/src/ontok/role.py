"""Required work or results, and roles composed of those responsibilities."""

from typing import Annotated

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .outcome import Outcome
from .rule import Requirement


class Responsibility[Context, End: Activity | Outcome](Requirement[Context, End]):
    """A requirement to perform work or attain an Outcome."""


class Role[Duties: tuple](RootModel[Duties]):
    """Joint responsibilities, independently of their occupant."""

    root: Annotated[Duties, Field(min_length=1)]


class Participation[Occupant, Assigned: Role](BaseModel):
    """Occupancy is a fact separate from the Role definition."""

    occupant: Occupant
    role: Assigned
