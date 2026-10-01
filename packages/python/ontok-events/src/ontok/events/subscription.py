from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from ontok.core import Action, NodeId
from ontok.events.position import Position


class Start(StrEnum):
    """Where a Subscription begins when no Position is named."""

    BEGINNING = "beginning"
    NOW = "now"


class FromPosition(BaseModel):
    """The Subscription begins after this Position."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    position: Position = Field(description="The Position the Subscription begins after.")


StartingPoint = FromPosition | Start


class Subscription(Action):
    """A Role's standing interest in every Event, toward a Goal."""

    begins: StartingPoint = Field(description="Where this interest begins.")


class StreamSubscription(Subscription):
    """A Role's standing interest in the Events of one Stream, toward a Goal."""

    stream: NodeId = Field(description="The Stream this interest is in.")
