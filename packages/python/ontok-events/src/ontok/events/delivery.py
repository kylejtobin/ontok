from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, RootModel, TypeAdapter

from ontok.core import Action, Event, NodeId, Timestamp
from ontok.events.memory import ReadHistory, Readings, ReadLatest, Retained
from ontok.events.recording import Append
from ontok.events.type import DeliveryToken, Disposition, LogSequence
from ontok.events.value import (
    Address,
    AddressConstructor,
    ExpectAny,
    Expectation,
    MessageBody,
    OfType,
    Unavailable,
)
from ontok.events.work import Conjunction, Policy, Projection


class Delivery(BaseModel):
    """Memory handing a remembered occurrence to a responsibility, with its token."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    token: DeliveryToken
    event: Event
    sequence: LogSequence

    @property
    def retained(self) -> Retained:
        return Retained(event=self.event, sequence=self.sequence)

    @property
    def address(self) -> Address:
        return AddressConstructor.validate_python(self.event, from_attributes=True)

    @property
    def abouts(self) -> tuple[NodeId, ...]:
        return (self.address.about,)


class Unconstructible(BaseModel):
    """What arrived is not one of this program's occurrences; its body is the witness."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    token: DeliveryToken
    body: MessageBody = Field(validation_alias=AliasPath("event"))

    @property
    def abouts(self) -> tuple[NodeId, ...]:
        return ()


Arrival = Annotated[Delivery | Unconstructible, Field(union_mode="left_to_right")]
ArrivalConstructor: TypeAdapter[Delivery | Unconstructible] = TypeAdapter(Arrival)


class PolicyConsultation(BaseModel):
    """What memory a policy consults for an arrival: the entity's history."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work: Policy
    arrival: Arrival

    @property
    def reads(self) -> tuple[ReadHistory, ...]:
        return tuple(ReadHistory(about=about) for about in self.arrival.abouts)


class ConjunctionConsultation(BaseModel):
    """What memory a conjunction consults for an arrival: the latest of each of its two kinds."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work: Conjunction
    arrival: Arrival

    @property
    def reads(self) -> tuple[ReadLatest, ...]:
        return tuple(
            ReadLatest(about=about, scope=OfType(event_type=event_type))
            for about in self.arrival.abouts
            for event_type in self.work.responsibility.event_types
        )


class ProjectionConsultation(BaseModel):
    """What memory a projection consults for an arrival: nothing."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work: Projection
    arrival: Arrival

    @property
    def reads(self) -> tuple[()]:
        return ()


Consultation = PolicyConsultation | ConjunctionConsultation | ProjectionConsultation


class EmittedIdentities(RootModel[tuple[NodeId, ...]]):
    """Exactly one identity for each position an emission can take."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: tuple[NodeId, ...] = Field(min_length=1000, max_length=1000)


class ReadClock(BaseModel):
    """The effect of reading the present instant."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )


class MintEmissionIdentities(BaseModel):
    """The effect of minting an identity for every position an emission can take."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )


class Occasion(BaseModel):
    """The situation work faces: what was asked of memory, what memory answered, and when."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    consultation: Consultation
    consulted: Readings
    at: Timestamp

    @property
    def work(self) -> Policy | Conjunction | Projection:
        return self.consultation.work

    @property
    def action(self) -> Action:
        return self.work.action


class MintedOccasion(Occasion):
    """An occasion for work that emits, with the identities its emissions may take."""

    emitted: EmittedIdentities


class Response(BaseModel):
    """Work responded to an occasion; the application's variants add what they respond to."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    at: Timestamp

    @property
    def disposition(self) -> Disposition:
        return Disposition.COMPLETE


class EmittingResponse(Response):
    """Work that emits responded to an occasion, holding the identities its emissions take."""

    emitted: EmittedIdentities


class Deferred(BaseModel):
    """The first read did not complete; the delivery is attempted again."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    unavailable: Unavailable = Field(validation_alias=AliasPath("consulted", "root", 0))

    @property
    def emissions(self) -> tuple[Event, ...]:
        return ()

    @property
    def expectation(self) -> Expectation:
        return ExpectAny()

    @property
    def effects(self) -> tuple[()]:
        return ()

    @property
    def disposition(self) -> Disposition:
        return Disposition.RETRY

    @property
    def append(self) -> Append:
        return Append(
            expectation=self.expectation, events=self.emissions, disposition=self.disposition
        )


class DeferredSecond(BaseModel):
    """The second read did not complete; the delivery is attempted again."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    unavailable: Unavailable = Field(validation_alias=AliasPath("consulted", "root", 1))

    @property
    def emissions(self) -> tuple[Event, ...]:
        return ()

    @property
    def expectation(self) -> Expectation:
        return ExpectAny()

    @property
    def effects(self) -> tuple[()]:
        return ()

    @property
    def disposition(self) -> Disposition:
        return Disposition.RETRY

    @property
    def append(self) -> Append:
        return Append(
            expectation=self.expectation, events=self.emissions, disposition=self.disposition
        )


class Rejected(BaseModel):
    """Nothing of this program's arrived; the delivery is terminal."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    arrival: Unconstructible = Field(validation_alias=AliasPath("consultation", "arrival"))

    @property
    def emissions(self) -> tuple[Event, ...]:
        return ()

    @property
    def expectation(self) -> Expectation:
        return ExpectAny()

    @property
    def effects(self) -> tuple[()]:
        return ()

    @property
    def disposition(self) -> Disposition:
        return Disposition.REJECT

    @property
    def append(self) -> Append:
        return Append(
            expectation=self.expectation, events=self.emissions, disposition=self.disposition
        )


class Acknowledge(BaseModel):
    """The effect of telling memory what became of a delivery."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    token: DeliveryToken
    disposition: Disposition


class Acknowledged(BaseModel):
    """Memory has been told what became of the delivery."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )


Acknowledgement = Acknowledged | Unavailable
