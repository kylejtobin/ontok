from pydantic import ConfigDict, Field, RootModel, TypeAdapter

from ontok.core import Action, NodeId
from ontok.events.event import Occurrence
from ontok.events.position import Position
from ontok.events.value import ExpectedVersion, VersionMismatch


class Occurrences(RootModel[tuple[Occurrence, ...]]):
    """The occurrences of one Append, in order."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: tuple[Occurrence, ...] = Field(min_length=1)


class Append(Action):
    """Occurrences declared for a Stream under an expected Version."""

    stream: NodeId = Field(description="The Stream the occurrences are for.")
    expected: ExpectedVersion = Field(description="What is asserted of the Stream.")
    occurrences: Occurrences = Field(description="The occurrences, in order.")


AppendOutcome = Position | VersionMismatch
AppendOutcomeConstructor: TypeAdapter[AppendOutcome] = TypeAdapter(AppendOutcome)
