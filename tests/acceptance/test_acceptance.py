"""The shop's composition root, and the five functions proven end to end against the server:
publish, handle, emit, read latest, replay."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
from uuid import uuid7  # pyright: ignore[reportAttributeAccessIssue, reportUnknownVariableType]

import nats.js.errors
import pytest
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js.api import ConsumerConfig
from pydantic import BaseModel, ConfigDict

from ontok.core import Instant, NodeId, Timestamp
from ontok.events import (
    Acknowledge,
    Append,
    ArrivalConstructor,
    ConjunctionConsultation,
    DeleteSubscription,
    Disposition,
    EnsureReadModel,
    EnsureSubscription,
    EveryType,
    ExpectAny,
    LogSequence,
    MintedOccasion,
    MintEmissionIdentities,
    Occasion,
    OfType,
    PolicyConsultation,
    ProjectionConsultation,
    ReadClock,
    Readings,
    ReadLatest,
    ReadModelEnsured,
    Retained,
    SubscriptionEnsured,
    Written,
)
from ontok.events.interpreter import ClockInterpreter, MintEmissionIdentitiesInterpreter
from ontok.nats import (
    AcknowledgeInterpreter,
    AppendInterpreter,
    DeleteSubscriptionInterpreter,
    EnsureReadModelInterpreter,
    EnsureSubscriptionInterpreter,
    ReadHistoryInterpreter,
    ReadLatestInterpreter,
    ResetReadModelInterpreter,
    SettleInterpreter,
    WriteStateInterpreter,
)
from ontok.nats.bucket import bucket_of
from ontok.nats.interpreter import DELIVER_PREFIX, STREAM

from .organization import (
    COUNT,
    COUNTING,
    INVOICE,
    INVOICING,
    SHIP,
    SHIPPING,
    CountResponseConstructor,
    Deleting,
    Effects,
    InvoiceResponseConstructor,
    Kind,
    OccurrenceConstructor,
    OrderPaid,
    OrderPlaced,
    OrderRoute,
    OrderStatus,
    Performed,
    Reset,
    ShipResponseConstructor,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")

# --- The composition root: one nested expression per responsibility ---


def clock() -> Timestamp:
    return ClockInterpreter(action=ReadClock(), clock=datetime).execute()


def minted() -> MintEmissionIdentitiesInterpreter:
    return MintEmissionIdentitiesInterpreter(action=MintEmissionIdentities(), mint=uuid7)  # pyright: ignore[reportUnknownArgumentType]


async def invoicing(client: Client, route: OrderRoute) -> None:
    await AcknowledgeInterpreter(
        action=Acknowledge(
            token=route.token,
            disposition=(
                await SettleInterpreter(
                    action=await AppendInterpreter(
                        action=InvoiceResponseConstructor.validate_python(
                            MintedOccasion(
                                consultation=PolicyConsultation(
                                    work=INVOICING,
                                    arrival=ArrivalConstructor.validate_python(
                                        route, from_attributes=True
                                    ),
                                ),
                                consulted=Readings(
                                    tuple(
                                        [
                                            await ReadHistoryInterpreter(
                                                action=read,
                                                client=client,
                                                constructor=OccurrenceConstructor.validate_json,
                                            ).execute()
                                            for read in PolicyConsultation(
                                                work=INVOICING,
                                                arrival=ArrivalConstructor.validate_python(
                                                    route, from_attributes=True
                                                ),
                                            ).reads
                                        ]
                                    )
                                ),
                                at=clock(),
                                emitted=minted().execute(),
                            ),
                            from_attributes=True,
                        ).append,
                        client=client,
                    ).execute(),
                    client=client,
                    constructor=OccurrenceConstructor.validate_json,
                ).execute()
            ).durability.disposition,
        ),
        client=client,
    ).execute()


async def shipping(client: Client, route: OrderRoute) -> None:
    await AcknowledgeInterpreter(
        action=Acknowledge(
            token=route.token,
            disposition=(
                await SettleInterpreter(
                    action=await AppendInterpreter(
                        action=ShipResponseConstructor.validate_python(
                            MintedOccasion(
                                consultation=ConjunctionConsultation(
                                    work=SHIPPING,
                                    arrival=ArrivalConstructor.validate_python(
                                        route, from_attributes=True
                                    ),
                                ),
                                consulted=Readings(
                                    tuple(
                                        [
                                            await ReadLatestInterpreter(
                                                action=read,
                                                client=client,
                                                constructor=OccurrenceConstructor.validate_json,
                                            ).execute()
                                            for read in ConjunctionConsultation(
                                                work=SHIPPING,
                                                arrival=ArrivalConstructor.validate_python(
                                                    route, from_attributes=True
                                                ),
                                            ).reads
                                        ]
                                    )
                                ),
                                at=clock(),
                                emitted=minted().execute(),
                            ),
                            from_attributes=True,
                        ).append,
                        client=client,
                    ).execute(),
                    client=client,
                    constructor=OccurrenceConstructor.validate_json,
                ).execute()
            ).durability.disposition,
        ),
        client=client,
    ).execute()


async def counting(client: Client, route: OrderRoute) -> None:
    await AcknowledgeInterpreter(
        action=Acknowledge(
            token=route.token,
            disposition=(
                await SettleInterpreter(
                    action=await AppendInterpreter(
                        action=(
                            await performed(
                                client,
                                Effects(
                                    response=CountResponseConstructor.validate_python(
                                        Occasion(
                                            consultation=ProjectionConsultation(
                                                work=COUNTING,
                                                arrival=ArrivalConstructor.validate_python(
                                                    route, from_attributes=True
                                                ),
                                            ),
                                            consulted=Readings(()),
                                            at=clock(),
                                        ),
                                        from_attributes=True,
                                    )
                                ),
                            )
                        ).completeness.append,
                        client=client,
                    ).execute(),
                    client=client,
                    constructor=OccurrenceConstructor.validate_json,
                ).execute()
            ).durability.disposition,
        ),
        client=client,
    ).execute()


async def performed(client: Client, effects: Effects) -> Performed:
    """The shop's effect interpreter for counting: every write, through the read model."""
    return Performed(
        effects=effects,
        outcomes=tuple(
            [
                await WriteStateInterpreter(action=write, client=client).execute()
                for write in effects.response.effects
            ]
        ),
    )


async def bind(
    client: Client, work_type: str, respond: Callable[[Client, OrderRoute], Awaitable[None]]
) -> None:
    async def deliver(msg: Msg) -> None:
        await respond(client, OrderRoute.model_validate(msg, from_attributes=True))

    await client.jetstream().subscribe_bind(  # pyright: ignore[reportUnknownMemberType]
        stream=STREAM,
        config=ConsumerConfig(deliver_subject=DELIVER_PREFIX + work_type, deliver_group=work_type),
        consumer=work_type,
        cb=deliver,
        manual_ack=True,
    )


# --- Helpers that read memory and the read model as a client ---


async def latest(client: Client, order: NodeId, kind: Kind | None = None) -> Retained | None:
    reading = await ReadLatestInterpreter(
        action=ReadLatest(
            about=order,
            scope=EveryType()
            if kind is None
            else OfType(event_type=__import__("ontok.events").events.EventTypeName(kind)),
        ),
        client=client,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    return reading if isinstance(reading, Retained) else None


async def eventually[T](check: Callable[[], Awaitable[T | None]], timeout: float = 10.0) -> T:
    """The fact the check returns, once memory or the read model shows it."""
    for _ in range(int(timeout / 0.1)):
        result = await check()
        if result:
            return result
        await asyncio.sleep(0.1)
    message = "the fact did not appear"
    raise TimeoutError(message)


class OrderCell(BaseModel):
    """What the counting read model keeps, read back as the shop's own kind."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    sequence: LogSequence
    state: OrderStatus


async def status(admin: Client, order: NodeId) -> str | None:
    store = await admin.jetstream().key_value(bucket_of(COUNT.work_type.root))  # pyright: ignore[reportUnknownMemberType]
    try:
        entry = await store.get(order.root)
    except Exception:
        return None
    assert entry.value is not None
    return OrderCell.model_validate_json(entry.value).state.stage


async def snapshot(admin: Client) -> dict[str, str]:
    store = await admin.jetstream().key_value(bucket_of(COUNT.work_type.root))  # pyright: ignore[reportUnknownMemberType]
    try:
        keys = await store.keys()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    except nats.js.errors.NoKeysError:
        return {}
    cells: dict[str, str] = {}
    for key in keys:
        entry = await store.get(key)
        assert entry.value is not None
        cells[key] = entry.value.decode()
    return cells


# --- The five functions ---


async def test_the_shop_publishes_handles_emits_reads_and_replays(
    program: Client, admin: Client
) -> None:
    # Startup: read model, subscriptions, callbacks.
    assert isinstance(
        await EnsureReadModelInterpreter(
            action=EnsureReadModel(work_type=COUNT.work_type), client=program
        ).execute(),
        ReadModelEnsured,
    )
    for duty in (INVOICE, SHIP, COUNT):
        assert isinstance(
            await EnsureSubscriptionInterpreter(
                action=EnsureSubscription(subscription=duty.subscription), client=program
            ).execute(),
            SubscriptionEnsured,
        )
    await bind(program, INVOICE.work_type.root, invoicing)
    await bind(program, SHIP.work_type.root, shipping)
    await bind(program, COUNT.work_type.root, counting)

    # 1. Publish: a source commits an originating occurrence.
    order = NodeId(str(uuid7()))  # pyright: ignore[reportUnknownArgumentType]
    placed = OrderPlaced(
        id=NodeId(str(uuid7())),  # pyright: ignore[reportUnknownArgumentType]
        occurred=Instant(at=clock()),
        event_type=Kind.PLACED,
        order=order,
    )
    answer = await AppendInterpreter(
        action=Append(expectation=ExpectAny(), events=(placed,), disposition=Disposition.COMPLETE),
        client=program,
    ).execute()
    assert isinstance(answer, Written)

    # 4. Read latest: the occurrence is the order's latest.
    retained = await latest(program, order)
    assert retained is not None and retained.event == placed

    # 2. Handle, and 3. Emit: the policy invoiced the order, and the projection saw the invoice.
    invoiced = await eventually(lambda: latest(program, order, Kind.INVOICED))
    assert isinstance(invoiced, Retained)
    assert await eventually(lambda: status(admin, order)) == "invoiced"

    # The conjunction: paid after placed ships, caused by both.
    paid = OrderPaid(
        id=NodeId(str(uuid7())),  # pyright: ignore[reportUnknownArgumentType]
        occurred=Instant(at=clock()),
        event_type=Kind.PAID,
        order=order,
    )
    assert isinstance(
        await AppendInterpreter(
            action=Append(
                expectation=ExpectAny(), events=(paid,), disposition=Disposition.COMPLETE
            ),
            client=program,
        ).execute(),
        Written,
    )
    shipped = await eventually(lambda: latest(program, order, Kind.SHIPPED))
    assert isinstance(shipped, Retained)
    stage = await eventually(lambda: status(admin, order))
    assert stage == "shipped"
    assert (await latest(program, order)) == shipped

    # 5. Replay: delete the subscription, reset the read model, ensure again; the read model
    # rebuilt from the beginning of memory is identical.
    before = await snapshot(admin)
    assert before
    rebuilt = tuple(
        [
            await EnsureSubscriptionInterpreter(action=ensure, client=program).execute()
            for ensure in Reset(
                outcomes=tuple(
                    [
                        await ResetReadModelInterpreter(action=reset, client=program).execute()
                        for reset in Deleting(
                            outcome=await DeleteSubscriptionInterpreter(
                                action=DeleteSubscription(subscription=COUNT.subscription),
                                client=program,
                            ).execute()
                        ).resets
                    ]
                )
            ).ensures
        ]
    )
    assert len(rebuilt) == 1 and isinstance(rebuilt[0], SubscriptionEnsured)

    async def identical() -> bool:
        return await snapshot(admin) == before

    assert await eventually(identical)
