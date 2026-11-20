"""An intended or resulting state, produced or maintained through work."""

from pydantic import BaseModel, RootModel

from .type import State


class ProducedOutcome[Condition](BaseModel):
    """A state brought about through work."""

    state: State[Condition]


class MaintainedOutcome[Condition, Extent](BaseModel):
    """A state held throughout a specified extent."""

    state: State[Condition]
    extent: Extent


class Outcome[Form: ProducedOutcome | MaintainedOutcome](RootModel[Form]):
    """Exactly one outcome form, independent of intention or occurrence."""
