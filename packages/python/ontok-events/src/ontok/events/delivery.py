from pydantic import ConfigDict, Field, RootModel

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
