"""Grants conferred by a formal basis upon a holder."""

from typing import Literal

from pydantic import BaseModel

from .decision import Decision
from .rule import Permission, Requirement


class ActionGrant[Context, Action](Permission[Context, Action]):
    kind: Literal["action"] = "action"


class DecisionGrant[Choice: Decision](BaseModel):
    kind: Literal["decision"] = "decision"
    decisions: Choice


class ObligationGrant[Duty: Requirement](BaseModel):
    kind: Literal["obligation"] = "obligation"
    imposable: Duty


class Authority[Holder, FormalBasis, Grant: ActionGrant | DecisionGrant | ObligationGrant](BaseModel):
    holder: Holder
    established_by: FormalBasis
    grant: Grant
