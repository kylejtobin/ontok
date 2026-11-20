"""Three structurally distinct forms of organizational exchange."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .role import Responsibility


class InteractionKind(StrEnum):
    """The three forms of exchange defined by Ontok."""

    COMMUNICATION = "communication"
    RESPONSIBILITY_TRANSFER = "responsibility_transfer"
    COORDINATION = "coordination"


class Communication[Sender, Recipient, Content](BaseModel):
    """An exchange communicating content to one or more recipients."""

    kind: Literal[InteractionKind.COMMUNICATION] = Field(
        default=InteractionKind.COMMUNICATION,
        description="Identifies a communication exchange.",
    )
    sender: Sender = Field(description="The participant conveying the content.")
    recipients: Annotated[
        tuple[Recipient, ...],
        Field(min_length=1, description="The participants receiving the content."),
    ]
    content: Content = Field(description="The information conveyed.")


class ResponsibilityTransfer[Source, Destination](BaseModel):
    """An exchange transferring one Responsibility."""

    kind: Literal[InteractionKind.RESPONSIBILITY_TRANSFER] = Field(
        default=InteractionKind.RESPONSIBILITY_TRANSFER,
        description="Identifies a responsibility-transfer exchange.",
    )
    source: Source = Field(description="The participant from whom responsibility passes.")
    destination: Destination = Field(
        description="The participant to whom responsibility passes."
    )
    responsibility: Responsibility = Field(
        description="The Responsibility transferred, stated exactly once."
    )


class Coordination[Participant](BaseModel):
    """An exchange coordinating work between two or more participants."""

    kind: Literal[InteractionKind.COORDINATION] = Field(
        default=InteractionKind.COORDINATION,
        description="Identifies a coordination exchange.",
    )
    participants: Annotated[
        tuple[Participant, ...],
        Field(min_length=2, description="The participants coordinating work."),
    ]
    work: Activity = Field(description="The Activity whose work is coordinated.")


class Interaction(RootModel[Communication | ResponsibilityTransfer | Coordination]):
    """One complete exchange, without asserting that it occurred."""

    root: Communication | ResponsibilityTransfer | Coordination = Field(
        discriminator="kind",
        description="Communication, ResponsibilityTransfer, or Coordination.",
    )
