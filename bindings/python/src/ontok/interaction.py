"""Communication, transfer of responsibility, or coordination of work."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from .role import Responsibility


class Communication[Sender, Recipient, Message](BaseModel):
    kind: Literal["communication"] = "communication"
    sender: Sender
    recipient: Recipient
    content: Message


class ResponsibilityTransfer[Sender, Recipient, Duty: Responsibility](BaseModel):
    kind: Literal["responsibility_transfer"] = "responsibility_transfer"
    sender: Sender
    recipient: Recipient
    responsibility: Duty


class Coordination[Participant, Work](BaseModel):
    kind: Literal["coordination"] = "coordination"
    participants: Annotated[tuple[Participant, ...], Field(min_length=2)]
    work: Work


class Interaction[Exchange: Communication | ResponsibilityTransfer | Coordination](RootModel[Exchange]):
    """A selected, complete exchange; specialize Exchange to its actual alternatives."""
