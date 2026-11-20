"""Exchanges that communicate, transfer responsibility, or coordinate work."""

from typing import Annotated

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .role import Responsibility


class Communication[Sender, Recipient, Content](BaseModel):
    sender: Sender
    recipients: Annotated[tuple[Recipient, ...], Field(min_length=1)]
    content: Content


class ResponsibilityTransfer[Source, Destination, Duty: Responsibility](BaseModel):
    source: Source
    destination: Destination
    responsibility: Duty


class Coordination[Participant, Work: Activity](BaseModel):
    participants: Annotated[tuple[Participant, ...], Field(min_length=2)]
    work: Work


class Interaction[Exchange: Communication | ResponsibilityTransfer | Coordination](
    RootModel[Exchange]
):
    """One exchange, independently of whether it actually occurred."""
