"""Formally established powers granted to a holder."""

from pydantic import BaseModel

from .activity import Activity
from .outcome import Outcome
from .rule import Permission, Requirement


class ActionGrant[Context, Work: Activity](Permission[Context, Work]):
    """Permission to perform work, not an assertion that it was performed."""


class DecisionGrant[Scope](BaseModel):
    """Power to decide within a scope, not a Decision already made."""

    scope: Scope


class ObligationGrant[Context, End: Activity | Outcome](BaseModel):
    """Power to create the specified required obligation."""

    obligation: Requirement[Context, End]


class Authority[Holder, Basis, Grant: ActionGrant | DecisionGrant | ObligationGrant](BaseModel):
    holder: Holder
    established_by: Basis
    grant: Grant
