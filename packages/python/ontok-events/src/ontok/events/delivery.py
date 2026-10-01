from pydantic import Field

from ontok import core
from ontok.core import Work
from ontok.events.event import Event


class Delivery(Work):
    """A Subscription's undertaking of one Event."""

    event: Event = Field(description="The Event handed to the Subscription.")


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
