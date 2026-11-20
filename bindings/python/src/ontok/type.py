"""Semantic constituents shared across Ontok's foundational concepts."""

from pydantic import BaseModel, Field, RootModel


class State[Content](RootModel[Content]):
    """A condition, with its representation supplied by the organization."""

    root: Content = Field(description="The domain-defined condition represented by this state.")


class Need[Holder, Condition](BaseModel):
    """A condition required by a holder."""

    holder: Holder = Field(description="The person, organization, or other holder of the need.")
    required: State[Condition] = Field(
        description="The condition the holder requires, expressed as a State."
    )


class Interest[Holder, Concern](BaseModel):
    """A concern or stake held by a participant."""

    holder: Holder = Field(description="The holder of the concern or stake.")
    concern: Concern = Field(description="The subject matter in which the holder has an interest.")
