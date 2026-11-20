"""Shared constituents; these do not add foundational Ontok concepts."""

from pydantic import BaseModel, RootModel


class State[Content](RootModel[Content]):
    """A condition; its content is supplied by a domain model."""


class Need[Holder, Requirement](BaseModel):
    """Something a holder requires."""

    holder: Holder
    required: Requirement


class Interest[Holder, Concern](BaseModel):
    """A holder's concern."""

    holder: Holder
    concern: Concern
