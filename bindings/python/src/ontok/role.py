"""Responsibilities defining Roles, independently of their occupants."""

from typing import Annotated

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .outcome import Outcome
from .rule import Requirement


class Responsibility[Context](Requirement[Context, Activity | Outcome]):
    """A required work action or result, without prescribing an unnecessary method."""

    target: Activity | Outcome = Field(
        description="The required Activity or Outcome, including a maintained state."
    )


class Role(RootModel[tuple[Responsibility, ...]]):
    """A nonempty composition of responsibilities, not an assignment to an occupant."""

    root: Annotated[
        tuple[Responsibility, ...],
        Field(min_length=1, description="The responsibilities associated with this Role."),
    ]


class Participation[Occupant](BaseModel):
    """An occupant's association with a Role; the Role itself remains unchanged."""

    occupant: Occupant = Field(
        description="The person, program, or other participant occupying the Role."
    )
    role: Role = Field(description="The Role occupied by this participant.")
