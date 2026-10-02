from pydantic import Field, SerializeAsAny

from ontok import core
from ontok.core import NodeId
from ontok.events.event import Event
from ontok.events.position import Version


class Initial(core.State):
    """The condition of an Entity before any Event."""

    stream: NodeId = Field(description="The Stream that holds no Event yet.")

    @property
    def version(self) -> Version:
        return Version(0)


class State(core.State):
    """The fold of a Stream: the prior condition and the Event folded into it."""

    prior: SerializeAsAny["Initial | State"] = Field(description="The condition before this Event.")
    event: Event = Field(description="The Event folded into the prior condition.")

    @property
    def version(self) -> Version:
        return Version(self.prior.version.root + 1)
