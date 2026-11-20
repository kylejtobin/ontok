"""Formally established permissions and powers held by an organizational participant."""

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .rule import Permission, Requirement


class ActionGrant[Context](Permission[Context, Activity]):
    """Permission to perform work; it does not assert performance."""

    target: Activity = Field(description="The Activity that the holder is permitted to perform.")


class DecisionGrant[Scope](BaseModel):
    """Permission to make decisions within a scope, not an already made Decision."""

    scope: Scope = Field(description="The domain-defined scope of decisions this grant authorizes.")


class ObligationGrant[Context, Target](RootModel[Requirement[Context, Target]]):
    """Power to create an obligation expressed as a required Rule."""

    root: Requirement[Context, Target] = Field(
        description="The requirement that the holder has the power to impose."
    )


class Authority[Holder, Basis](BaseModel):
    """A formal basis, holder, and exactly one grant."""

    holder: Holder = Field(description="The person, program, or position holding the Authority.")
    established_by: Basis = Field(
        description="The formal basis by which this permission or power is established."
    )
    grant: ActionGrant | DecisionGrant | ObligationGrant = Field(
        description="One permission to act, power to decide, or power to create obligations."
    )
