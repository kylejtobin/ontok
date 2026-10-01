from pydantic import Field

from ontok.core import Entity, States
from ontok.events.position import Position


class ReadModel(Entity):
    """Conditions held as of a Position in the log."""

    state: States = Field(description="The conditions held.")
    position: Position = Field(description="The Position the conditions are as of.")
