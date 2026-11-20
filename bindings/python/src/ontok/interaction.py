"""Distinct forms of participant exchange."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from .role import Responsibility
from .type import CONFIG


class Communication[Sender, Recipients: tuple[object, ...], Content](BaseModel, frozen=True):
    model_config = CONFIG
    kind: Literal["communication"] = "communication"
    sender: Sender
    recipients: Annotated[Recipients, Field(min_length=1)]
    content: Content


class ResponsibilityTransfer[Source, Destination, Duty: Responsibility](BaseModel, frozen=True):
    model_config = CONFIG
    kind: Literal["responsibility_transfer"] = "responsibility_transfer"
    source: Source
    destination: Destination
    responsibility: Duty


class Coordination[Participants: tuple[object, ...], Work](BaseModel, frozen=True):
    model_config = CONFIG
    kind: Literal["coordination"] = "coordination"
    participants: Annotated[Participants, Field(min_length=2)]
    work: Work


class Interaction[
    Exchange: Communication[object, tuple[object, ...], object]
    | ResponsibilityTransfer[object, object, Responsibility]
    | Coordination[tuple[object, ...], object]
](RootModel[Exchange], frozen=True):
    """A concrete declaration selects a complete exchange form."""
