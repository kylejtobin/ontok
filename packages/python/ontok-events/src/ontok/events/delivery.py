from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, RootModel

from ontok import core
from ontok.core import Work
from ontok.events.event import Event


class Attempt(RootModel[int]):
    """Which delivery of an Event to a Subscription this is. The first is 1."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class Delivery(Work):
    """A Subscription's undertaking of one Event."""

    event: Event = Field(description="The Event handed to the Subscription.")
    attempt: Attempt = Field(description="Which delivery of this Event this is.")


class Outcome(StrEnum):
    """The condition a Delivery is in once ended: complete, returned to be handed again, or
    parked."""

    COMPLETE = "complete"
    RETURNED = "returned"
    PARKED = "parked"


class Ending(BaseModel):
    """A Delivery to be ended, in the condition it is to be in."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    delivery: Delivery = Field(description="The Delivery to end.")
    outcome: Outcome = Field(description="The condition it is to be in.")


class Disposition(core.State):
    """The condition a Delivery is in once ended."""

    delivery: Delivery = Field(description="The Delivery this condition goes on.")
    outcome: Outcome = Field(description="The condition it is in.")
