from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import Action, NodeId
from ontok.events.event import Events, Occurrence
from ontok.events.value import ExpectedVersion, VersionMismatch


class Occurrences(BaseModel):
    """The occurrences of one Append, in order: those leading, and the last."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    leading: tuple[Occurrence, ...] = Field(
        description="The occurrences before the last, in order."
    )
    last: Occurrence = Field(description="The last occurrence.")


class Append(Action):
    """Occurrences declared for a Stream under an expected Version."""

    stream: NodeId = Field(description="The Stream the occurrences are for.")
    expected: ExpectedVersion = Field(description="What is asserted of the Stream.")
    occurrences: Occurrences = Field(description="The occurrences, in order.")


AppendOutcome = Events | VersionMismatch
AppendOutcomeConstructor: TypeAdapter[AppendOutcome] = TypeAdapter(AppendOutcome)
