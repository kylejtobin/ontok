"""An asserted occurrence, without a universal time or proof obligation."""

from pydantic import BaseModel, Field


class Event[Occurrence](BaseModel):
    """A claim that something occurred; construction does not establish truth."""

    occurred: Occurrence = Field(
        description="The asserted occurrence, which may be an Outcome, Interaction, or other event."
    )
