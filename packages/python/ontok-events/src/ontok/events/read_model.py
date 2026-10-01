from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import Entity, NodeId, States
from ontok.events.position import Position


class ReadModel(Entity):
    """Conditions held as of a Position in the log."""

    state: States = Field(description="The conditions held.")
    position: Position = Field(description="The Position the conditions are as of.")

    @property
    def persistence(self) -> "PersistReadModel":
        return PersistReadModel(read_model=self)


class PersistReadModel(BaseModel):
    """A ReadModel to be recorded."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    read_model: ReadModel = Field(description="The ReadModel to record.")


class ReadModelLookup(BaseModel):
    """A ReadModel asked for by identity."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    id: NodeId = Field(description="The identity of the ReadModel asked for.")


class NoReadModel(BaseModel):
    """No ReadModel is held under this identity."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    id: NodeId = Field(description="The identity nothing is held under.")


LookupOutcome = ReadModel | NoReadModel
LookupOutcomeConstructor: TypeAdapter[LookupOutcome] = TypeAdapter(LookupOutcome)
