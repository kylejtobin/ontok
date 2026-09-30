from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel, TypeAdapter

from ontok.core import NodeId
from ontok.events.type import EventTypeName, FailureReason, LogSequence, Ordinal, WorkTypeName


class PolicyProvenance(BaseModel):
    """How a policy's emission came to be: the responsibility, its one cause, and its position."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work_type: WorkTypeName
    cause: NodeId
    position: Ordinal

    @property
    def causes(self) -> tuple[NodeId, ...]:
        return (self.cause,)


class ConjunctionProvenance(BaseModel):
    """A conjunction's emission: its responsibility, both causes in order, and its position."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work_type: WorkTypeName
    first: NodeId
    second: NodeId
    position: Ordinal

    @property
    def causes(self) -> tuple[NodeId, ...]:
        return (self.first, self.second)


Provenance = PolicyProvenance | ConjunctionProvenance


class OriginAddress(BaseModel):
    """Where an originating occurrence lives in memory."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId
    event_type: EventTypeName
    id: NodeId


class EmissionAddress(BaseModel):
    """Where a derived occurrence lives in memory."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId
    event_type: EventTypeName
    provenance: Provenance


Address = Annotated[EmissionAddress | OriginAddress, Field(union_mode="left_to_right")]
AddressConstructor: TypeAdapter[EmissionAddress | OriginAddress] = TypeAdapter(Address)


class ExpectAny(BaseModel):
    """The claim that nothing is at the occurrence's own address."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )


class ExpectSequence(BaseModel):
    """The claim that the latest remembered occurrence about the entity has this sequence."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    sequence: LogSequence


Expectation = ExpectAny | ExpectSequence


class OfType(BaseModel):
    """The scope of a latest read: occurrences of one kind."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    event_type: EventTypeName


class EveryType(BaseModel):
    """The scope of a latest read: occurrences of every kind."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )


ReadScope = OfType | EveryType


class MessageBody(RootModel[bytes]):
    """The body of an arrival that is not one of this program's occurrences; never read."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )


class Absent(BaseModel):
    """Memory holds nothing in the scope read about this entity."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId


class Unavailable(BaseModel):
    """The provider or the capability did not complete the effect."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    reason: FailureReason
