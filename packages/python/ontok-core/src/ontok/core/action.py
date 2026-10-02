from pydantic import Field, SerializeAsAny

from ontok.core.goal import Goal
from ontok.core.role import Role
from ontok.core.structure import Node


class Action(Node):
    """Declared work."""

    role: SerializeAsAny[Role] = Field(description="The office through which this doing is taken.")
    goal: SerializeAsAny[Goal] = Field(description="The end this doing is toward.")
