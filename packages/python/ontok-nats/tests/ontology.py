"""A test-owned ontology: kinds of occurrence about an order, their union, and its constructor."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated, Literal
from uuid import uuid7  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]

from pydantic import Field, TypeAdapter

from ontok.core import Event, Goal, Instant, NodeId, PositiveDuration, Role, Timestamp
from ontok.events import (
    ConjunctionProvenance,
    EventTypeName,
    Ordinal,
    PolicyProvenance,
    Responsibility,
    WorkTypeName,
)


class Kind(StrEnum):
    PLACED = "shop-OrderPlaced"
    PAID = "shop-OrderPaid"
    SHIPPED = "shop-OrderShipped"


class OrderPlaced(Event):
    event_type: Literal[Kind.PLACED]
    order: NodeId

    @property
    def about(self) -> NodeId:
        return self.order


class OrderPaid(Event):
    event_type: Literal[Kind.PAID]
    order: NodeId

    @property
    def about(self) -> NodeId:
        return self.order


class OrderShipped(Event):
    event_type: Literal[Kind.SHIPPED]
    order: NodeId
    provenance: PolicyProvenance | ConjunctionProvenance

    @property
    def about(self) -> NodeId:
        return self.order


Occurrence = Annotated[OrderPlaced | OrderPaid | OrderShipped, Field(discriminator="event_type")]
OccurrenceConstructor: TypeAdapter[OrderPlaced | OrderPaid | OrderShipped] = TypeAdapter(Occurrence)


def fresh() -> NodeId:
    return NodeId(str(uuid7()))  # pyright: ignore[reportUnknownArgumentType]


def now() -> Instant:
    return Instant(at=Timestamp(datetime.now(UTC)))


def placed(order: NodeId) -> OrderPlaced:
    return OrderPlaced(id=fresh(), occurred=now(), event_type=Kind.PLACED, order=order)


def paid(order: NodeId) -> OrderPaid:
    return OrderPaid(id=fresh(), occurred=now(), event_type=Kind.PAID, order=order)


def shipped(order: NodeId, cause: NodeId, position: int = 0) -> OrderShipped:
    return OrderShipped(
        id=fresh(),
        occurred=now(),
        event_type=Kind.SHIPPED,
        order=order,
        provenance=PolicyProvenance(
            work_type=WorkTypeName("shop-Shipping"), cause=cause, position=Ordinal(position)
        ),
    )


class Clerk(Role): ...


class OrderHandled(Goal): ...


def responsibility(work_type: str, *kinds: Kind) -> Responsibility:
    return Responsibility(
        id=fresh(),
        role=Clerk(id=fresh()),
        goal=OrderHandled(id=fresh()),
        work_type=WorkTypeName(work_type),
        consumes=tuple(EventTypeName(kind) for kind in kinds),
        patience=PositiveDuration(timedelta(seconds=2)),
    )
