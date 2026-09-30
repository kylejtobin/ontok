"""An application's simplest declarations prove the module's chain without a provider."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import Event, Goal, Instant, NodeId, PositiveDuration, Role, Timestamp
from ontok.events import (
    Acknowledge,
    Append,
    Appended,
    Deferred,
    Delivery,
    DeliveryToken,
    Disposition,
    EmittedIdentities,
    EmittingResponse,
    EventTypeName,
    ExpectAny,
    Expectation,
    ExpectSequence,
    FailureReason,
    History,
    LogSequence,
    MintedOccasion,
    Occasion,
    Policy,
    PolicyConsultation,
    Projection,
    ProjectionConsultation,
    Readings,
    Rejected,
    Response,
    Responsibility,
    Retained,
    Settled,
    Unavailable,
    WorkTypeName,
    Written,
)

from .ontology import Kind, OrderPlaced, identifier, placed

STRICT = ConfigDict(
    frozen=True, extra="forbid", strict=True, validate_default=True, revalidate_instances="never"
)
TOKEN = DeliveryToken("$JS.ACK.EVENTS.shop-Invoicing.1.7.1.0.0")


class Clerk(Role): ...


class OrderInvoiced(Goal): ...


class Invoicing(EmittingResponse):
    """A policy's response: an order placed is invoiced, expecting the entity's latest."""

    trigger: OrderPlaced = Field(validation_alias=AliasPath("consultation", "arrival", "event"))
    history: History = Field(validation_alias=AliasPath("consulted", "root", 0))

    @property
    def expectation(self) -> Expectation:
        return ExpectSequence(sequence=self.history.latest.sequence)

    @property
    def emissions(self) -> tuple[Event, ...]:
        return (
            OrderPlaced(
                id=self.emitted.root[0],
                occurred=Instant(at=self.at),
                event_type=Kind.PLACED,
                order=self.trigger.about,
            ),
        )

    @property
    def append(self) -> Append:
        return Append(
            expectation=self.expectation, events=self.emissions, disposition=self.disposition
        )


InvoiceResponse = Invoicing | Deferred | Rejected
InvoiceResponseConstructor: TypeAdapter[Invoicing | Deferred | Rejected] = TypeAdapter(
    InvoiceResponse
)
INVOICE = Responsibility(
    id=identifier(30),
    role=Clerk(id=identifier(31)),
    goal=OrderInvoiced(id=identifier(32)),
    work_type=WorkTypeName("shop-Invoicing"),
    consumes=(EventTypeName(Kind.PLACED),),
    patience=PositiveDuration(timedelta(seconds=30)),
)
INVOICING = Policy(id=identifier(33), action=INVOICE)


def invoicing_occasion(*readings: History | Unavailable) -> MintedOccasion:
    return MintedOccasion(
        consultation=PolicyConsultation(
            work=INVOICING, arrival=Delivery(token=TOKEN, event=placed(), sequence=LogSequence(7))
        ),
        consulted=Readings(readings),
        at=Timestamp(datetime.now(UTC)),
        emitted=EmittedIdentities(tuple(identifier(0x50) for _ in range(1000))),
    )


def test_a_policys_emission_claims_the_sequence_of_its_historys_latest() -> None:
    history = History((Retained(event=placed(), sequence=LogSequence(7)),))
    response = InvoiceResponseConstructor.validate_python(
        invoicing_occasion(history), from_attributes=True
    )
    assert response.append.expectation == ExpectSequence(sequence=LogSequence(7))
    assert response.append.disposition is Disposition.COMPLETE


def test_a_written_policy_append_concludes_in_a_complete_acknowledgement() -> None:
    history = History((Retained(event=placed(), sequence=LogSequence(7)),))
    response = InvoiceResponseConstructor.validate_python(
        invoicing_occasion(history), from_attributes=True
    )
    settled = Settled(answer=Written(append=response.append), readings=Readings(()))
    acknowledgement = Acknowledge(token=TOKEN, disposition=settled.durability.disposition)
    assert isinstance(settled.durability, Appended)
    assert acknowledgement.disposition is Disposition.COMPLETE


# --- A projection with effects on one external system --------------------------------------------


class Counted(BaseModel):
    """The read model counted the order at this sequence."""

    model_config = STRICT

    sequence: LogSequence


class Count(BaseModel):
    """The effect of counting an order in the read model, idempotent by sequence."""

    model_config = STRICT

    order: NodeId
    sequence: LogSequence


CountOutcome = Counted | Unavailable


class Counting(Response):
    """A projection's response: the placed order is counted."""

    trigger: OrderPlaced = Field(validation_alias=AliasPath("consultation", "arrival", "event"))
    sequence: LogSequence = Field(validation_alias=AliasPath("consultation", "arrival", "sequence"))

    @property
    def effects(self) -> tuple[Count, ...]:
        return (Count(order=self.trigger.about, sequence=self.sequence),)

    @property
    def emissions(self) -> tuple[Event, ...]:
        return ()

    @property
    def expectation(self) -> Expectation:
        return ExpectAny()

    @property
    def append(self) -> Append:
        return Append(
            expectation=self.expectation, events=self.emissions, disposition=self.disposition
        )


CountResponse = Counting | Deferred | Rejected
CountResponseConstructor: TypeAdapter[Counting | Deferred | Rejected] = TypeAdapter(CountResponse)


class Effects(BaseModel):
    """What a response asks of the read model."""

    model_config = STRICT

    response: CountResponse


class EffectsHeld(BaseModel):
    """Every effect held; the response's append is authorized."""

    model_config = STRICT

    effects: Effects
    outcomes: tuple[Counted, ...]

    @property
    def append(self) -> Append:
        return self.effects.response.append


class EffectsUnavailable(BaseModel):
    """Some effect did not hold; nothing is appended and the delivery is attempted again."""

    model_config = STRICT

    @property
    def append(self) -> Append:
        return Append(expectation=ExpectAny(), events=(), disposition=Disposition.RETRY)


Completeness = Annotated[EffectsHeld | EffectsUnavailable, Field(union_mode="left_to_right")]
CompletenessConstructor: TypeAdapter[EffectsHeld | EffectsUnavailable] = TypeAdapter(Completeness)


class Performed(BaseModel):
    """The effects were performed, with these outcomes."""

    model_config = STRICT

    effects: Effects
    outcomes: tuple[CountOutcome, ...]

    @property
    def completeness(self) -> Completeness:
        return CompletenessConstructor.validate_python(self, from_attributes=True)


COUNT = Responsibility(
    id=identifier(40),
    role=Clerk(id=identifier(41)),
    goal=OrderInvoiced(id=identifier(42)),
    work_type=WorkTypeName("shop-Counting"),
    consumes=(EventTypeName(Kind.PLACED),),
    patience=PositiveDuration(timedelta(seconds=30)),
)
COUNTING = Projection(id=identifier(43), action=COUNT)


def counting_response() -> CountResponse:
    return CountResponseConstructor.validate_python(
        Occasion(
            consultation=ProjectionConsultation(
                work=COUNTING,
                arrival=Delivery(token=TOKEN, event=placed(), sequence=LogSequence(7)),
            ),
            consulted=Readings(()),
            at=Timestamp(datetime.now(UTC)),
        ),
        from_attributes=True,
    )


def test_an_effect_that_did_not_hold_appends_nothing_and_retries() -> None:
    performed = Performed(
        effects=Effects(response=counting_response()),
        outcomes=(Unavailable(reason=FailureReason("locked")),),
    )
    assert isinstance(performed.completeness, EffectsUnavailable)
    assert performed.completeness.append.events == ()
    assert performed.completeness.append.disposition is Disposition.RETRY


def test_effects_that_held_authorize_the_responses_append() -> None:
    performed = Performed(
        effects=Effects(response=counting_response()), outcomes=(Counted(sequence=LogSequence(7)),)
    )
    assert performed.completeness.append.disposition is Disposition.COMPLETE
    assert performed.effects.response.effects == (
        Count(order=placed().about, sequence=LogSequence(7)),
    )
