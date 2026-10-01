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


class Acknowledge(BaseModel):
    """A Delivery to be ended as taken."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    delivery: Delivery = Field(description="The Delivery to end.")


class Reject(BaseModel):
    """A Delivery to be ended as not taken, its Event to be handed again."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    delivery: Delivery = Field(description="The Delivery to end.")


class Park(BaseModel):
    """A Delivery to be ended with its Event set aside."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    delivery: Delivery = Field(description="The Delivery to end.")


Ending = Acknowledge | Reject | Park


class Acknowledgement(core.Event):
    """The Delivery ended: the Event was taken."""

    delivery: Delivery = Field(description="The Delivery this ends.")


class Rejection(core.Event):
    """The Delivery ended: the Event was not taken and is to be handed again."""

    delivery: Delivery = Field(description="The Delivery this ends.")


class Parking(core.Event):
    """The Delivery ended: the Event was set aside."""

    delivery: Delivery = Field(description="The Delivery this ends.")


Disposition = Acknowledgement | Rejection | Parking
