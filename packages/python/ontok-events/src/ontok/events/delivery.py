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


class End(StrEnum):
    """How a Delivery ends: taken, not taken and to be handed again, or set aside."""

    ACKNOWLEDGE = "acknowledge"
    REJECT = "reject"
    PARK = "park"


class Ending(BaseModel):
    """A Delivery to be ended."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    delivery: Delivery = Field(description="The Delivery to end.")
    end: End = Field(description="How it is to end.")


class Disposition(core.Event):
    """The Delivery ended."""

    delivery: Delivery = Field(description="The Delivery this ended.")
    end: End = Field(description="How it ended.")
