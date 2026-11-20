"""Formally established powers to act, decide, or create obligations."""

from pydantic import BaseModel, Field

from .activity import Activity
from .rule import Permission, Requirement


class ActionGrant[Context](Permission[Context, Activity]):
    """A Permission narrowed to the performance of an Activity."""

    target: Activity = Field(description="The organizational work permitted by the grant.")


class DecisionGrant[Scope](BaseModel):
    """Power to make Decisions within a scope, not an already made Decision."""

    scope: Scope = Field(description="The domain-defined scope of Decisions authorized.")


class Authority[Holder, Basis](BaseModel):
    """A holder, formal basis, and exactly one permission or power."""

    holder: Holder = Field(description="The holder of the permission or power.")
    established_by: Basis = Field(
        description="The formal basis that establishes the holder's authority."
    )
    grant: ActionGrant | DecisionGrant | Requirement = Field(
        description=(
            "Permission to perform work, power to decide within a scope, "
            "or power to create the stated required obligation."
        )
    )
