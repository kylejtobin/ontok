from pydantic import BaseModel, ConfigDict, Field

from ontok.core import Action, NodeId
from ontok.events.position import Position


class Subscription(Action):
    """A Role's standing interest in every Event, toward a Goal."""


class StreamSubscription(Subscription):
    """A Role's standing interest in the Events of one Stream, toward a Goal."""

    stream: NodeId = Field(description="The Stream this interest is in.")


class Checkpoint(BaseModel):
    """The Position a Subscription has reached."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subscription: Subscription = Field(description="The Subscription that has reached it.")
    position: Position = Field(description="The Position reached.")
