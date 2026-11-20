"""A state produced or maintained through organizational activity."""

from pydantic import BaseModel, Field, RootModel

from .type import State


class ProducedOutcome[Condition](BaseModel):
    """An outcome in which a state is brought about."""

    state: State[Condition] = Field(description="The state brought about through activity.")


class MaintainedOutcome[Condition, Extent](BaseModel):
    """An outcome in which a state holds throughout a stated extent."""

    state: State[Condition] = Field(description="The state maintained through activity.")
    extent: Extent = Field(description="The domain-defined extent throughout which the state holds.")


class Outcome(RootModel[ProducedOutcome | MaintainedOutcome]):
    """A produced or maintained state, regardless of intention or occurrence."""

    root: ProducedOutcome | MaintainedOutcome = Field(
        description="Exactly one produced or maintained form of the outcome."
    )
