from pydantic import Field, SerializeAsAny

from ontok import core
from ontok.core import NodeId
from ontok.events.event import Event


class Initial(core.State):
    """The condition of an Entity before any Event."""

    stream: NodeId = Field(description="The Stream that holds no Event yet.")


class State(core.State):
    """The fold of a Stream: the prior condition and the Event folded into it."""

    prior: SerializeAsAny["Initial | State"] = Field(description="The condition before this Event.")
    event: Event = Field(description="The Event folded into the prior condition.")
