"""A response is selected by the facts an occasion carries, on the paths that are not the work's."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import AliasPath, Field, TypeAdapter

from ontok.core import Event, Goal, Instant, NodeId, PositiveDuration, Role, Timestamp
from ontok.events import (
    AddressConstructor,
    ArrivalConstructor,
    Conjunction,
    ConjunctionConsultation,
    ConjunctionProvenance,
    ConjunctionResponsibility,
    Deferred,
    DeferredSecond,
    Delivery,
    DeliveryToken,
    Disposition,
    EmittedIdentities,
    EmittingResponse,
    EventTypeName,
    FailureReason,
    LogSequence,
    MessageBody,
    MintedOccasion,
    Ordinal,
    Readings,
    Rejected,
    Retained,
    Unavailable,
    Unconstructible,
    WorkTypeName,
)

from .ontology import Kind, OrderPlaced, identifier, placed


class Kinds(StrEnum):
    PAID = "shop-OrderPaid"
    SHIPPED = "shop-OrderShipped"


class OrderPaid(Event):
    event_type: Literal[Kinds.PAID]
    order: NodeId

    @property
    def about(self) -> NodeId:
        return self.order


class OrderShipped(Event):
    event_type: Literal[Kinds.SHIPPED]
    order: NodeId
    provenance: ConjunctionProvenance

    @property
    def about(self) -> NodeId:
        return self.order


class Shipper(Role): ...


class OrderFulfilled(Goal): ...


class Shipping(EmittingResponse):
    """The work's response: both occurrences are remembered, so the order ships."""

    trigger: OrderPlaced | OrderPaid = Field(
        validation_alias=AliasPath("consultation", "arrival", "event")
    )
    placed: Retained = Field(validation_alias=AliasPath("consulted", "root", 0))
    paid: Retained = Field(validation_alias=AliasPath("consulted", "root", 1))

    @property
    def emissions(self) -> tuple[Event, ...]:
        return (
            OrderShipped(
                id=self.emitted.root[0],
                occurred=Instant(at=self.at),
                event_type=Kinds.SHIPPED,
                order=self.trigger.about,
                provenance=ConjunctionProvenance(
                    work_type=SHIP.work_type,
                    first=self.placed.event.id,
                    second=self.paid.event.id,
                    position=Ordinal(0),
                ),
            ),
        )


ShipResponse = Shipping | Deferred | DeferredSecond | Rejected
ShipResponseConstructor: TypeAdapter[Shipping | Deferred | DeferredSecond | Rejected] = TypeAdapter(
    ShipResponse
)

SHIP = ConjunctionResponsibility(
    id=identifier(20),
    role=Shipper(id=identifier(21)),
    goal=OrderFulfilled(id=identifier(22)),
    work_type=WorkTypeName("shop-Shipping"),
    first=EventTypeName(Kind.PLACED),
    second=EventTypeName(Kinds.PAID),
    patience=PositiveDuration(timedelta(seconds=30)),
)
WORK = Conjunction(id=identifier(23), action=SHIP)
TOKEN = DeliveryToken("$JS.ACK.EVENTS.shop-Shipping.1.7.1.0.0")


def paid() -> OrderPaid:
    return OrderPaid(
        id=identifier(3), occurred=placed().occurred, event_type=Kinds.PAID, order=placed().order
    )


def occasion(
    arrival: Delivery | Unconstructible, *readings: Retained | Unavailable, n: int
) -> MintedOccasion:
    return MintedOccasion(
        consultation=ConjunctionConsultation(work=WORK, arrival=arrival),
        consulted=Readings(readings),
        at=Timestamp(datetime.now(UTC)),
        emitted=EmittedIdentities(tuple(identifier(0x40 + n) for _ in range(1000))),
    )


def test_a_lagging_conjunction_emits_the_same_publication_at_both_arrivals() -> None:
    both = (
        Retained(event=placed(), sequence=LogSequence(1)),
        Retained(event=paid(), sequence=LogSequence(2)),
    )
    at_placed = ShipResponseConstructor.validate_python(
        occasion(Delivery(token=TOKEN, event=placed(), sequence=LogSequence(1)), *both, n=1),
        from_attributes=True,
    )
    at_paid = ShipResponseConstructor.validate_python(
        occasion(Delivery(token=TOKEN, event=paid(), sequence=LogSequence(2)), *both, n=2),
        from_attributes=True,
    )
    addresses = [
        AddressConstructor.validate_python(r.emissions[0], from_attributes=True)
        for r in (at_placed, at_paid)
    ]
    assert addresses[0] == addresses[1]
    assert at_placed.emissions[0].id != at_paid.emissions[0].id


def test_an_unavailable_second_read_defers_rather_than_responding() -> None:
    response = ShipResponseConstructor.validate_python(
        occasion(
            Delivery(token=TOKEN, event=placed(), sequence=LogSequence(1)),
            Retained(event=placed(), sequence=LogSequence(1)),
            Unavailable(reason=FailureReason("timeout")),
            n=3,
        ),
        from_attributes=True,
    )
    assert isinstance(response, DeferredSecond)
    assert response.append.disposition is Disposition.RETRY
    assert response.append.events == ()


class Route:
    """An object shaped like the application's delivery route after the body refused to be ours."""

    token = TOKEN
    event = MessageBody(b"\x00not json")
    sequence = LogSequence(9)


def test_a_body_that_is_not_ours_arrives_unconstructible_and_is_rejected() -> None:
    arrival = ArrivalConstructor.validate_python(Route(), from_attributes=True)
    assert isinstance(arrival, Unconstructible)
    response = ShipResponseConstructor.validate_python(occasion(arrival, n=4), from_attributes=True)
    assert isinstance(response, Rejected)
    assert response.append.disposition is Disposition.REJECT
