from pydantic import BaseModel, ConfigDict, Field, RootModel

from ontok.core import Event, NodeId
from ontok.events.type import LogSequence
from ontok.events.value import Absent, Address, ReadScope, Unavailable


class Retained(BaseModel):
    """An occurrence that is remembered, at this position in memory."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    event: Event
    sequence: LogSequence


class History(RootModel[tuple[Retained, ...]]):
    """An entity's remembered occurrences in log order."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: tuple[Retained, ...] = Field(min_length=1)

    @property
    def latest(self) -> Retained:
        return self.root[-1]


class ReadHistory(BaseModel):
    """The effect of reading an entity's whole history."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId


class ReadLatest(BaseModel):
    """The effect of reading the latest remembered occurrence about an entity, in a scope."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId
    scope: ReadScope


class ReadAddress(BaseModel):
    """The effect of reading the occurrence at one address."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    address: Address


LatestReading = Retained | Absent | Unavailable
HistoryReading = History | Absent | Unavailable
Reading = Retained | History | Absent | Unavailable


class Readings(RootModel[tuple[Reading, ...]]):
    """The outcomes of a consultation's reads, in the declared order of the reads."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )
