from pydantic import Field, SerializeAsAny

from ontok.core.action import Action
from ontok.core.entity import Entity


class Work(Entity):
    """A persistent undertaking of a declared Action."""

    action: SerializeAsAny[Action] = Field(description="The declared doing being undertaken.")
