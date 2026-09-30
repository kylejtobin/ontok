"""Delivery behaves as the page states: routing, order, one instance per occurrence, durability,
the three dispositions, a binding that outlives its consumer, and the identity's limits."""

import asyncio
from collections.abc import AsyncIterator

import nats
import nats.errors
import pytest
import pytest_asyncio
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js.api import ConsumerConfig, StreamConfig
from pydantic import AliasPath, BaseModel, ConfigDict, Field, Json
from testcontainers.core.container import DockerContainer

from ontok.core import Event
from ontok.events import (
    Acknowledge,
    Acknowledged,
    Append,
    DeleteSubscription,
    DeliveryToken,
    Disposition,
    EnsureSubscription,
    ExpectAny,
    LogSequence,
    MessageBody,
    Subscription,
    SubscriptionDeleted,
    SubscriptionEnsured,
    Written,
)
from ontok.nats import (
    AcknowledgeInterpreter,
    AppendInterpreter,
    DeleteSubscriptionInterpreter,
    EnsureSubscriptionInterpreter,
)
from ontok.nats.interpreter import DELIVER_PREFIX, STREAM

from .ontology import (
    Kind,
    OrderPaid,
    OrderPlaced,
    OrderShipped,
    fresh,
    paid,
    placed,
    responsibility,
    shipped,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


class DeliveryRoute(BaseModel):
    """The application's route: the provider's message, lifted whole."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    token: DeliveryToken = Field(validation_alias="reply")
    sequence: LogSequence = Field(validation_alias=AliasPath("metadata", "sequence", "stream"))
    delivered: int = Field(validation_alias=AliasPath("metadata", "num_delivered"))
    event: Json[OrderPlaced | OrderPaid | OrderShipped] | MessageBody = Field(
        validation_alias="data", union_mode="left_to_right"
    )


async def commit(client: Client, *events: Event) -> None:
    answer = await AppendInterpreter(
        action=Append(expectation=ExpectAny(), events=events, disposition=Disposition.COMPLETE),
        client=client,
    ).execute()
    assert isinstance(answer, Written)


async def ensure(client: Client, subscription: Subscription) -> None:
    ensured = await EnsureSubscriptionInterpreter(
        action=EnsureSubscription(subscription=subscription), client=client
    ).execute()
    assert isinstance(ensured, SubscriptionEnsured)


async def bind(client: Client, subscription: Subscription) -> asyncio.Queue[DeliveryRoute]:
    inbox: asyncio.Queue[DeliveryRoute] = asyncio.Queue()

    async def callback(msg: Msg) -> None:
        await inbox.put(DeliveryRoute.model_validate(msg, from_attributes=True))

    name = subscription.work_type.root
    await client.jetstream().subscribe_bind(  # pyright: ignore[reportUnknownMemberType]
        stream=STREAM,
        config=ConsumerConfig(deliver_subject=DELIVER_PREFIX + name, deliver_group=name),
        consumer=name,
        cb=callback,
        manual_ack=True,
    )
    return inbox


async def acknowledge(client: Client, route: DeliveryRoute, disposition: Disposition) -> None:
    done = await AcknowledgeInterpreter(
        action=Acknowledge(token=route.token, disposition=disposition), client=client
    ).execute()
    assert isinstance(done, Acknowledged)


async def next_delivery(inbox: asyncio.Queue[DeliveryRoute]) -> DeliveryRoute:
    return await asyncio.wait_for(inbox.get(), timeout=5)


async def delivery_of(
    client: Client, inbox: asyncio.Queue[DeliveryRoute], event: Event
) -> DeliveryRoute:
    """The delivery of this occurrence; every earlier occurrence of the kind, remembered by other
    tests, is delivered first and completed on the way."""
    while True:
        route = await next_delivery(inbox)
        if isinstance(route.event, Event) and route.event.id == event.id:
            return route
        await acknowledge(client, route, Disposition.COMPLETE)


@pytest_asyncio.fixture(loop_scope="session")
async def second_program(server: str, stream: None) -> AsyncIterator[Client]:
    client = await nats.connect(server, user="program", password="program")  # pyright: ignore[reportUnknownMemberType]
    yield client
    await client.close()


async def test_a_subscription_receives_only_its_kinds_in_log_order(program: Client) -> None:
    order = fresh()
    duty = responsibility(f"shop-Order{order.root[-6:]}", Kind.PLACED, Kind.PAID)
    await ensure(program, duty.subscription)
    inbox = await bind(program, duty.subscription)
    first, second, third = placed(order), paid(order), paid(order)
    await commit(program, first)
    await commit(program, shipped(order, first.id))
    await commit(program, second)
    await commit(program, third)
    received: list[DeliveryRoute] = [await delivery_of(program, inbox, first)]
    await acknowledge(program, received[0], Disposition.COMPLETE)
    for _ in range(2):
        route = await next_delivery(inbox)
        received.append(route)
        await acknowledge(program, route, Disposition.COMPLETE)
    assert [r.event.id for r in received if isinstance(r.event, Event)] == [
        first.id,
        second.id,
        third.id,
    ]
    assert [r.sequence.root for r in received] == sorted(r.sequence.root for r in received)


async def test_ensuring_a_subscription_twice_is_the_same_subscription(program: Client) -> None:
    duty = responsibility(f"shop-Twice{fresh().root[-6:]}", Kind.PLACED)
    await ensure(program, duty.subscription)
    await ensure(program, duty.subscription)


async def test_each_occurrence_reaches_exactly_one_of_two_instances(
    program: Client, second_program: Client
) -> None:
    order = fresh()
    duty = responsibility(f"shop-Group{order.root[-6:]}", Kind.PAID)
    await ensure(program, duty.subscription)
    one = await bind(program, duty.subscription)
    two = await bind(second_program, duty.subscription)
    events = [paid(order) for _ in range(6)]
    for event in events:
        await commit(program, event)
    ours = {event.id.root for event in events}
    seen: list[DeliveryRoute] = []
    merged: asyncio.Queue[DeliveryRoute] = asyncio.Queue()

    async def drain(inbox: asyncio.Queue[DeliveryRoute]) -> None:
        while True:
            await merged.put(await inbox.get())

    drains = [asyncio.create_task(drain(one)), asyncio.create_task(drain(two))]
    try:
        while len(seen) < len(events):
            route = await asyncio.wait_for(merged.get(), timeout=5)
            await acknowledge(program, route, Disposition.COMPLETE)
            if isinstance(route.event, Event) and route.event.id.root in ours:
                seen.append(route)
    finally:
        for task in drains:
            task.cancel()
    assert sorted(r.sequence.root for r in seen) == sorted({r.sequence.root for r in seen})
    assert len(seen) == len(events)


async def test_retry_redelivers_and_reject_terminates(program: Client) -> None:
    order = fresh()
    duty = responsibility(f"shop-Dispose{order.root[-6:]}", Kind.PLACED)
    await ensure(program, duty.subscription)
    inbox = await bind(program, duty.subscription)
    event = placed(order)
    await commit(program, event)
    first = await delivery_of(program, inbox, event)
    await acknowledge(program, first, Disposition.RETRY)
    again = await next_delivery(inbox)
    assert again.sequence == first.sequence
    assert again.delivered == first.delivered + 1
    await acknowledge(program, again, Disposition.REJECT)
    try:
        extra = await asyncio.wait_for(inbox.get(), timeout=duty.patience.root.total_seconds() + 1)
    except TimeoutError:
        return
    pytest.fail(f"delivered after terminate: {extra.token.root}, delivered {extra.delivered}")


async def test_a_binding_outlives_its_consumers_deletion_and_recreation(program: Client) -> None:
    order = fresh()
    duty = responsibility(f"shop-Rebind{order.root[-6:]}", Kind.PLACED)
    await ensure(program, duty.subscription)
    inbox = await bind(program, duty.subscription)
    deleted = await DeleteSubscriptionInterpreter(
        action=DeleteSubscription(subscription=duty.subscription), client=program
    ).execute()
    assert isinstance(deleted, SubscriptionDeleted)
    await ensure(program, duty.subscription)
    event = placed(order)
    await commit(program, event)
    route = await delivery_of(program, inbox, event)
    await acknowledge(program, route, Disposition.COMPLETE)


async def test_deleting_a_subscription_that_is_gone_is_gone(program: Client) -> None:
    duty = responsibility(f"shop-Gone{fresh().root[-6:]}", Kind.PLACED)
    deleted = await DeleteSubscriptionInterpreter(
        action=DeleteSubscription(subscription=duty.subscription), client=program
    ).execute()
    assert isinstance(deleted, SubscriptionDeleted)


async def test_the_program_identity_cannot_administer_streams(program: Client) -> None:
    with pytest.raises(nats.errors.Error):
        await program.jetstream().add_stream(  # pyright: ignore[reportUnknownMemberType]
            StreamConfig(name="ROGUE", subjects=["rogue.>"])
        )


async def test_memory_and_progress_survive_a_server_restart(
    program: Client, container: DockerContainer
) -> None:
    order = fresh()
    duty = responsibility(f"shop-Restart{order.root[-6:]}", Kind.PLACED)
    await ensure(program, duty.subscription)
    inbox = await bind(program, duty.subscription)
    before, after = placed(order), placed(order)
    await commit(program, before)
    route = await delivery_of(program, inbox, before)
    await acknowledge(program, route, Disposition.COMPLETE)
    container.get_wrapped_container().restart()
    for _ in range(100):
        try:
            await program.jetstream().account_info()  # pyright: ignore[reportUnknownMemberType]
            break
        except (nats.errors.Error, OSError):
            await asyncio.sleep(0.2)
    assert program.is_connected
    await commit(program, after)
    route = await delivery_of(program, inbox, after)
    await acknowledge(program, route, Disposition.COMPLETE)
