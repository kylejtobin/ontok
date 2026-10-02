from pydantic import BaseModel, ConfigDict, Field

from ontok.events.position import Position
from ontok.events.subscription import Subscription


class NoCheckpoint(BaseModel):
    """A Subscription that has reached no Position."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subscription: Subscription = Field(description="The Subscription that has reached none.")


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
