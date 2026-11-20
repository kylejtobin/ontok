"""Complete forms of communication, responsibility transfer, and coordination."""

from typing import Annotated

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .role import Responsibility


class Communication[Sender, Recipient, Content](BaseModel):
    """Content conveyed by a sender to one or more recipients."""

    sender: Sender = Field(description="The participant sending the communication.")
    recipients: Annotated[
        tuple[Recipient, ...],
        Field(min_length=1, description="The one or more recipients of the communication."),
    ]
    content: Content = Field(description="The information communicated.")


class ResponsibilityTransfer[Source, Destination](BaseModel):
    """A responsibility transferred from its source to its destination."""

    source: Source = Field(description="The participant transferring the responsibility.")
    destination: Destination = Field(
        description="The participant receiving the responsibility."
    )
    responsibility: Responsibility = Field(
        description="The single Responsibility being transferred."
    )


class Coordination[Participant](BaseModel):
    """The coordination of work among two or more participants."""

    participants: Annotated[
        tuple[Participant, ...],
        Field(min_length=2, description="The participants coordinating the work."),
    ]
    work: Activity = Field(description="The Activity whose work the participants coordinate.")


class Interaction(RootModel[Communication | ResponsibilityTransfer | Coordination]):
    """An exchange, regardless of whether an Event has asserted its occurrence."""

    root: Communication | ResponsibilityTransfer | Coordination = Field(
        description="Exactly one complete communication, responsibility transfer, or coordination."
    )
