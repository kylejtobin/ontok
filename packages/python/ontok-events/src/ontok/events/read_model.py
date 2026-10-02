from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import Entity, NodeId
from ontok.events.position import Position
from ontok.events.subscription import FromPosition


class ReadModel(Entity):
    """The fold of one Stream as of a Position, held. A refinement adds the conditions it holds."""

    stream: NodeId = Field(description="The Stream this is the fold of.")
    position: Position = Field(description="The Position the fold is as of.")

    @property
    def after(self) -> FromPosition:
        return FromPosition(position=self.position)

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
