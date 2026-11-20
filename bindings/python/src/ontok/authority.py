"""Formally established grants held by an actor or organizational position."""

from typing import Literal

from pydantic import BaseModel

from .decision import Decision
from .rule import Permission, Requirement
from .type import CONFIG


class ActionPermission[Context, Action](Permission[Context, Action], frozen=True):
    kind: Literal["action_permission"] = "action_permission"


class DecisionPower[Scope: Decision[object]](BaseModel, frozen=True):
    model_config = CONFIG
    kind: Literal["decision_power"] = "decision_power"
    scope: Scope


class ObligationPower[Duty: Requirement[object, object]](BaseModel, frozen=True):
    model_config = CONFIG
    kind: Literal["obligation_power"] = "obligation_power"
    imposable: Duty


class Authority[
    Holder,
    Basis,
    Grant: ActionPermission[object, object] | DecisionPower[Decision[object]] | ObligationPower[Requirement[object, object]],
](BaseModel, frozen=True):
    """States a grant and its formal basis; construction does not prove conferment."""

    model_config = CONFIG
    holder: Holder
    established_by: Basis
    grant: Grant
