"""Semantic constituents shared across Ontok's foundational concepts."""

from pydantic import BaseModel, RootModel


class State[Content](RootModel[Content]):
    """A condition; domains determine what content expresses it."""


class Need[Holder, Required](BaseModel):
    """A holder and the condition the holder requires."""

    holder: Holder
    required: State[Required]


class Interest[Holder, Concern](BaseModel):
    """A holder and the concern or stake of that holder."""

    holder: Holder
    concern: Concern
