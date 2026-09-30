"""A shop, written as software: its occurrences, its responsibilities, the work that undertakes
them, what each work responds with, and the facts its replay is made of."""

from datetime import timedelta
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, Json, TypeAdapter

from ontok.core import Event, Goal, Instant, NodeId, PositiveDuration, Role, State
from ontok.events import (
    Absent,
    Append,
    Conjunction,
    ConjunctionProvenance,
    ConjunctionResponsibility,
    Deferred,
    DeferredSecond,
    Deleted,
    DeliveryRoute,
    Disposition,
    EmittingResponse,
    EnsureSubscription,
    EventTypeName,
    ExpectAny,
    Expectation,
    ExpectSequence,
    History,
    LogSequence,
    MessageBody,
    Ordinal,
    Policy,
    PolicyProvenance,
    Projection,
    ReadModelReset,
    ReadModelResetting,
    Rejected,
    ResetReadModel,
    Response,
    Responsibility,
    Retained,
    StateStale,
    StateWriting,
    StateWritten,
    SubscriptionDeleted,
    WorkTypeName,
    WriteState,
)

STRICT = ConfigDict(
    frozen=True, extra="forbid", strict=True, validate_default=True, revalidate_instances="never"
)
PATIENCE = PositiveDuration(timedelta(seconds=5))


def fixed(n: int) -> NodeId:
    return NodeId(f"0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a{n:02x}")


# --- Occurrences -------------------------------------------------------------------------------


class Kind(StrEnum):
    PLACED = "shop-OrderPlaced"
    INVOICED = "shop-OrderInvoiced"
    PAID = "shop-OrderPaid"
    SHIPPED = "shop-OrderShipped"


class OrderPlaced(Event):
    event_type: Literal[Kind.PLACED]
    order: NodeId

    @property
    def about(self) -> NodeId:
        return self.order


class OrderInvoiced(Event):
    event_type: Literal[Kind.INVOICED]
    order: NodeId
    provenance: PolicyProvenance

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
    provenance: ConjunctionProvenance

    @property
    def about(self) -> NodeId:
        return self.order


Occurrence = Annotated[
    OrderPlaced | OrderInvoiced | OrderPaid | OrderShipped, Field(discriminator="event_type")
]
OccurrenceConstructor: TypeAdapter[OrderPlaced | OrderInvoiced | OrderPaid | OrderShipped] = (
    TypeAdapter(Occurrence)
)


class OrderRoute(DeliveryRoute):
    """The shop's delivery route: the provider's message with the body as one of its occurrences."""

    event: Json[Occurrence] | MessageBody = Field(
        validation_alias="data", union_mode="left_to_right"
    )


# --- Agency ---------------------------------------------------------------------------------------


class Accountant(Role): ...


class Shipper(Role): ...


class Clerk(Role): ...


class Invoiced(Goal): ...


class Fulfilled(Goal): ...


class Counted(Goal): ...


INVOICE = Responsibility(
    id=fixed(0x10),
    role=Accountant(id=fixed(0x11)),
    goal=Invoiced(id=fixed(0x12)),
    work_type=WorkTypeName("shop-Invoicing"),
    consumes=(EventTypeName(Kind.PLACED),),
    patience=PATIENCE,
)
SHIP = ConjunctionResponsibility(
    id=fixed(0x20),
    role=Shipper(id=fixed(0x21)),
    goal=Fulfilled(id=fixed(0x22)),
    work_type=WorkTypeName("shop-Shipping"),
    first=EventTypeName(Kind.PLACED),
    second=EventTypeName(Kind.PAID),
    patience=PATIENCE,
)
COUNT = Responsibility(
    id=fixed(0x30),
    role=Clerk(id=fixed(0x31)),
    goal=Counted(id=fixed(0x32)),
    work_type=WorkTypeName("shop-Counting"),
    consumes=(
        EventTypeName(Kind.PLACED),
        EventTypeName(Kind.INVOICED),
        EventTypeName(Kind.SHIPPED),
    ),
    patience=PATIENCE,
)

INVOICING = Policy(id=fixed(0x13), action=INVOICE)
SHIPPING = Conjunction(id=fixed(0x23), action=SHIP)
COUNTING = Projection(id=fixed(0x33), action=COUNT)


# --- The policy's response ------------------------------------------------------------------------


class Invoicing(EmittingResponse):
    """An order was placed, so it is invoiced, claiming the order's latest."""

    trigger: OrderPlaced = Field(validation_alias=AliasPath("consultation", "arrival", "event"))
    history: History = Field(validation_alias=AliasPath("consulted", "root", 0))

    @property
    def expectation(self) -> Expectation:
        return ExpectSequence(sequence=self.history.latest.sequence)

    @property
    def emissions(self) -> tuple[Event, ...]:
        return (
            OrderInvoiced(
                id=self.emitted.root[0],
                occurred=Instant(at=self.at),
                event_type=Kind.INVOICED,
                order=self.trigger.order,
                provenance=PolicyProvenance(
                    work_type=INVOICE.work_type, cause=self.trigger.id, position=Ordinal(0)
                ),
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


# --- The conjunction's responses ------------------------------------------------------------------


class Shipped(EmittingResponse):
    """The order was placed and paid, so it ships, caused by both."""

    trigger: OrderPlaced | OrderPaid = Field(
        validation_alias=AliasPath("consultation", "arrival", "event")
    )
    placed: Retained = Field(validation_alias=AliasPath("consulted", "root", 0))
    paid: Retained = Field(validation_alias=AliasPath("consulted", "root", 1))

    @property
    def expectation(self) -> Expectation:
        return ExpectAny()

    @property
    def emissions(self) -> tuple[Event, ...]:
        return (
            OrderShipped(
                id=self.emitted.root[0],
                occurred=Instant(at=self.at),
                event_type=Kind.SHIPPED,
                order=self.trigger.order,
                provenance=ConjunctionProvenance(
                    work_type=SHIP.work_type,
                    first=self.placed.event.id,
                    second=self.paid.event.id,
                    position=Ordinal(0),
                ),
            ),
        )

    @property
    def append(self) -> Append:
        return Append(
            expectation=self.expectation, events=self.emissions, disposition=self.disposition
        )


class AwaitingPayment(Response):
    """The order was placed but not yet paid; nothing ships."""

    placed: Retained = Field(validation_alias=AliasPath("consulted", "root", 0))
    unpaid: Absent = Field(validation_alias=AliasPath("consulted", "root", 1))

    @property
    def emissions(self) -> tuple[Event, ...]:
        return ()

    @property
    def append(self) -> Append:
        return Append(expectation=ExpectAny(), events=(), disposition=self.disposition)


class AwaitingOrder(Response):
    """Payment arrived before the order was placed; nothing ships."""

    unplaced: Absent = Field(validation_alias=AliasPath("consulted", "root", 0))
    paid: Retained = Field(validation_alias=AliasPath("consulted", "root", 1))

    @property
    def emissions(self) -> tuple[Event, ...]:
        return ()

    @property
    def append(self) -> Append:
        return Append(expectation=ExpectAny(), events=(), disposition=self.disposition)


ShipResponse = Shipped | AwaitingPayment | AwaitingOrder | Deferred | DeferredSecond | Rejected
ShipResponseConstructor: TypeAdapter[
    Shipped | AwaitingPayment | AwaitingOrder | Deferred | DeferredSecond | Rejected
] = TypeAdapter(ShipResponse)


# --- The projection's response and its effects ----------------------------------------------------


class OrderStatus(State):
    """Where an order stands, as the counting projection sees it."""

    stage: Literal["placed", "invoiced", "shipped"]


STAGE: dict[Kind, Literal["placed", "invoiced", "shipped"]] = {
    Kind.PLACED: "placed",
    Kind.INVOICED: "invoiced",
    Kind.SHIPPED: "shipped",
}


class Counting(Response):
    """An order's occurrence moved it to a stage; the read model records that stage."""

    trigger: OrderPlaced | OrderInvoiced | OrderShipped = Field(
        validation_alias=AliasPath("consultation", "arrival", "event")
    )
    sequence: LogSequence = Field(validation_alias=AliasPath("consultation", "arrival", "sequence"))

    @property
    def effects(self) -> tuple[WriteState, ...]:
        return (
            WriteState(
                work_type=COUNT.work_type,
                about=self.trigger.order,
                sequence=self.sequence,
                state=OrderStatus(id=self.trigger.order, stage=STAGE[self.trigger.event_type]),
            ),
        )

    @property
    def emissions(self) -> tuple[Event, ...]:
        return ()

    @property
    def append(self) -> Append:
        return Append(expectation=ExpectAny(), events=(), disposition=self.disposition)


CountResponse = Counting | Rejected
CountResponseConstructor: TypeAdapter[Counting | Rejected] = TypeAdapter(CountResponse)


class Effects(BaseModel):
    """What a counting response asks of the read model."""

    model_config = STRICT

    response: CountResponse


class EffectsHeld(BaseModel):
    """Every write held, so the response's append is authorized."""

    model_config = STRICT

    effects: Effects
    outcomes: tuple[StateWritten | StateStale, ...]

    @property
    def append(self) -> Append:
        return self.effects.response.append


class EffectsUnavailable(BaseModel):
    """A write did not hold; nothing is appended and the delivery is attempted again."""

    model_config = STRICT

    @property
    def append(self) -> Append:
        return Append(expectation=ExpectAny(), events=(), disposition=Disposition.RETRY)


Completeness = Annotated[EffectsHeld | EffectsUnavailable, Field(union_mode="left_to_right")]
CompletenessConstructor: TypeAdapter[EffectsHeld | EffectsUnavailable] = TypeAdapter(Completeness)


class Performed(BaseModel):
    """The writes were performed, with these outcomes."""

    model_config = STRICT

    effects: Effects
    outcomes: tuple[StateWriting, ...]

    @property
    def completeness(self) -> Completeness:
        return CompletenessConstructor.validate_python(self, from_attributes=True)


# --- Replay: each step authorized by the last ---------------------------------------------------


class ResetAuthorized(BaseModel):
    """The subscription is gone, so the read model may be reset."""

    model_config = STRICT

    deleted: SubscriptionDeleted = Field(validation_alias=AliasPath("outcome"))

    @property
    def resets(self) -> tuple[ResetReadModel, ...]:
        return (ResetReadModel(work_type=self.deleted.subscription.work_type),)


class ResetRefused(BaseModel):
    """The subscription could not be deleted; nothing further is authorized."""

    model_config = STRICT

    @property
    def resets(self) -> tuple[ResetReadModel, ...]:
        return ()


Deletion = Annotated[ResetAuthorized | ResetRefused, Field(union_mode="left_to_right")]
DeletionConstructor: TypeAdapter[ResetAuthorized | ResetRefused] = TypeAdapter(Deletion)


class Deleting(BaseModel):
    """What deleting the subscription came to."""

    model_config = STRICT

    outcome: Deleted

    @property
    def resets(self) -> tuple[ResetReadModel, ...]:
        return DeletionConstructor.validate_python(self, from_attributes=True).resets


class EnsureAuthorized(BaseModel):
    """The read model is empty, so the subscription may be made again from the beginning."""

    model_config = STRICT

    reset: ReadModelReset = Field(validation_alias=AliasPath("outcomes", 0))

    @property
    def ensures(self) -> tuple[EnsureSubscription, ...]:
        return (EnsureSubscription(subscription=COUNT.subscription),)


class EnsureRefused(BaseModel):
    """The read model was not reset; nothing further is authorized."""

    model_config = STRICT

    @property
    def ensures(self) -> tuple[EnsureSubscription, ...]:
        return ()


Resetting = Annotated[EnsureAuthorized | EnsureRefused, Field(union_mode="left_to_right")]
ResettingConstructor: TypeAdapter[EnsureAuthorized | EnsureRefused] = TypeAdapter(Resetting)


class Reset(BaseModel):
    """What resetting the read model came to."""

    model_config = STRICT

    outcomes: tuple[ReadModelResetting, ...]

    @property
    def ensures(self) -> tuple[EnsureSubscription, ...]:
        return ResettingConstructor.validate_python(self, from_attributes=True).ensures
