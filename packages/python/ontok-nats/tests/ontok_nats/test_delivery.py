"""Every attack on delivery: silence, slowness, garbage, lies on the wire, interleaving, and two
clerks."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import nats
import pytest
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext

from ontok.core import Instant, NodeId, Timestamp
from ontok.events import (
    Append,
    AtVersion,
    Event,
    Expectation,
    Initial,
    Occurrences,
    Outcome,
    Position,
    Start,
    State,
    StreamSubscription,
    Subscription,
    Version,
)
from ontok.nats import (
    AckInterpreter,
    AckReply,
    EventSubject,
    MaxDeliveriesAdvisory,
    NatsConfig,
    Sequence,
)

from .acts import Clerk, Silent, Slow, delivered
from .bank import Amount, BankRoute, Deposited, Withdrawn
from .bank.main import append, mint, subscribe
from .world import BOOKS_BALANCED, TELLER

pytestmark = [pytest.mark.nats, pytest.mark.asyncio(loop_scope="session")]

NOW = Instant(at=Timestamp(datetime(2026, 10, 2, 13, 0, tzinfo=UTC)))


def deposit(amount: int) -> Deposited:
    return Deposited(id=mint(), occurred=NOW, amount=Amount(Decimal(amount)))


def withdrawal(amount: int) -> Withdrawn:
    return Withdrawn(id=mint(), occurred=NOW, amount=Amount(Decimal(amount)))


def an_append(
    stream: NodeId, expected: AtVersion | Expectation, *occurrences: Deposited | Withdrawn
) -> Append:
    return Append(
        id=mint(),
        role=TELLER,
        goal=BOOKS_BALANCED,
        stream=stream,
        expected=expected,
        occurrences=Occurrences(occurrences),
    )


def watching(stream: NodeId) -> StreamSubscription:
    return StreamSubscription(
        id=mint(), role=TELLER, goal=BOOKS_BALANCED, begins=Start.BEGINNING, stream=stream
    )


class Advisories:
    def __init__(self) -> None:
        self.seen: list[MaxDeliveriesAdvisory] = []

    async def receive(self, msg: Msg) -> None:
        self.seen.append(MaxDeliveriesAdvisory.model_validate_json(msg.data))


class Completer(Clerk):
    """A subscriber that completes everything."""

    async def receive(self, msg: Msg) -> None:
        route = BankRoute.receive(msg)
        self.deliveries.append(delivered(self.subscription, route))
        await AckInterpreter(
            action=AckReply(reply=route.message.reply, outcome=Outcome.COMPLETE),
            wait=self.config.reply_wait,
            client=self.client,
        ).execute()


async def test_a_delivery_never_ended_climbs_to_max_deliver_then_the_server_says_so(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    advisories = Advisories()
    await connection.subscribe(  # pyright: ignore[reportUnknownMemberType]
        "$JS.EVENT.ADVISORY.CONSUMER.MAX_DELIVERIES.>", cb=advisories.receive
    )  # pyright: ignore[reportUnknownMemberType]
    landed = await append(
        connection,
        config,
        an_append(account, Expectation.NO_STREAM, withdrawal(1)),
        Initial(id=mint(), stream=account),
    )
    assert isinstance(landed, Position)
    silent = Silent(connection, watching(account), config)
    await subscribe(connection, config, silent.subscription, silent.receive)
    deliveries = await silent.until(
        config.max_deliver.root,
        timeout=config.max_deliver.root * config.ack_wait.root.total_seconds() + 3,
    )
    assert [d.attempt.root for d in deliveries] == [1, 2, 3]
    await asyncio.sleep(2 * config.ack_wait.root.total_seconds() + 0.5)
    assert len(silent.deliveries) == 3
    assert [
        a.stream_seq for a in advisories.seen if a.consumer.root == silent.subscription.id.root
    ] == [Sequence(landed.root)]


async def test_a_slow_clerk_receives_the_duplicate_and_the_fold_moves_once(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    landed = await append(
        connection,
        config,
        an_append(account, Expectation.NO_STREAM, withdrawal(1)),
        Initial(id=mint(), stream=account),
    )
    assert isinstance(landed, Position)
    slow = Slow(
        connection, watching(account), config, delay=config.ack_wait.root.total_seconds() + 0.6
    )
    await subscribe(connection, config, slow.subscription, slow.receive)
    deliveries = await slow.until(2, timeout=config.ack_wait.root.total_seconds() * 3)
    assert [d.attempt.root for d in deliveries] == [1, 2]
    assert len({d.event.position.root for d in deliveries}) == 1
    fold = State(id=mint(), prior=Initial(id=mint(), stream=account), event=deliveries[0].event)
    assert fold.version == Version(1)


async def test_garbage_on_the_stream_is_refused_at_the_route_and_the_fold_does_not_move(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    subject = EventSubject(stream=account).subject.root
    await connection.publish(
        subject,
        b'{"this": "is not a transaction"}',
        headers={"Ontok-Stream": account.root, "Ontok-Version": "1", "Nats-Msg-Id": mint().root},
    )
    await connection.flush()
    clerk = Clerk(connection, watching(account), config)
    await subscribe(connection, config, clerk.subscription, clerk.receive)
    await asyncio.sleep(config.ack_wait.root.total_seconds() * (config.max_deliver.root + 1))
    assert clerk.deliveries == []
    assert len(clerk.refused) == config.max_deliver.root


async def test_a_forged_stream_header_lands_where_it_claims_and_nowhere_else(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account_a, account_b = mint(), mint()
    liar = deposit(99)
    await connection.publish(
        EventSubject(stream=account_b).subject.root,
        liar.model_dump_json().encode(),
        headers={"Ontok-Stream": account_a.root, "Ontok-Version": "1", "Nats-Msg-Id": liar.id.root},
    )
    await connection.flush()
    everything = Completer(
        connection,
        Subscription(id=mint(), role=TELLER, goal=BOOKS_BALANCED, begins=Start.BEGINNING),
        config,
    )
    await subscribe(connection, config, everything.subscription, everything.receive)
    deliveries = await everything.until_seen(liar.id, timeout=10.0)
    assert len(deliveries) == 1
    assert deliveries[0].event.stream == account_a
    watcher_b = Completer(connection, watching(account_b), config)
    await subscribe(connection, config, watcher_b.subscription, watcher_b.receive)
    assert [d.event.stream for d in await watcher_b.until(1, timeout=2.0)] == [account_a]


async def test_twenty_interleaved_events_fold_correctly_per_stream_from_deliveries_alone(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account_a, account_b = mint(), mint()
    fold_a: Initial | State = Initial(id=mint(), stream=account_a)
    fold_b: Initial | State = Initial(id=mint(), stream=account_b)
    for i in range(10):
        wa, wb = withdrawal(i + 1), withdrawal(i + 1)
        pa = await append(
            connection,
            config,
            an_append(
                account_a,
                Expectation.NO_STREAM if i == 0 else AtVersion(version=fold_a.version),
                wa,
            ),
            fold_a,
        )
        pb = await append(
            connection,
            config,
            an_append(
                account_b,
                Expectation.NO_STREAM if i == 0 else AtVersion(version=fold_b.version),
                wb,
            ),
            fold_b,
        )
        assert isinstance(pa, Position) and isinstance(pb, Position)
        fold_a = State(
            id=mint(),
            prior=fold_a,
            event=Event(occurrence=wa, stream=account_a, version=Version(i + 1), position=pa),
        )
        fold_b = State(
            id=mint(),
            prior=fold_b,
            event=Event(occurrence=wb, stream=account_b, version=Version(i + 1), position=pb),
        )
    clerk_a, clerk_b = (
        Clerk(connection, watching(account_a), config),
        Clerk(connection, watching(account_b), config),
    )
    await subscribe(connection, config, clerk_a.subscription, clerk_a.receive)
    await subscribe(connection, config, clerk_b.subscription, clerk_b.receive)
    da, db = await clerk_a.until(10), await clerk_b.until(10)
    assert [d.event.position.root for d in da] == sorted(d.event.position.root for d in da)
    assert [d.event.position.root for d in db] == sorted(d.event.position.root for d in db)
    refold_a: Initial | State = Initial(id=mint(), stream=account_a)
    for d in da:
        refold_a = State(id=mint(), prior=refold_a, event=d.event)
    assert (
        isinstance(refold_a, State)
        and isinstance(fold_a, State)
        and refold_a.version == Version(10)
        and refold_a.event == fold_a.event
    )


async def test_two_copies_of_the_same_subscriber_do_not_both_end_the_same_delivery(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    subscription = watching(account)
    first, second = (
        Completer(connection, subscription, config),
        Completer(connection, subscription, config),
    )
    other = await nats.connect(  # pyright: ignore[reportUnknownMemberType]
        f"{config.url.root}", user=config.user.root, password=config.credentials.get_secret_value()
    )
    second.client = other
    await subscribe(connection, config, subscription, first.receive)
    await subscribe(other, config, subscription, second.receive)
    landed = await append(
        connection,
        config,
        an_append(account, Expectation.NO_STREAM, withdrawal(3)),
        Initial(id=mint(), stream=account),
    )
    assert isinstance(landed, Position)
    await asyncio.sleep(1.0)
    await other.close()
    assert len(first.deliveries) + len(second.deliveries) == 1, (
        len(first.deliveries),
        len(second.deliveries),
    )


async def test_one_event_delivered_to_two_subscriptions_ends_independently(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    opening_fold = Initial(id=mint(), stream=account)
    w = withdrawal(8)
    landed = await append(
        connection, config, an_append(account, Expectation.NO_STREAM, w), opening_fold
    )
    assert isinstance(landed, Position)
    parker, completer = (
        Clerk(connection, watching(account), config),
        Completer(connection, watching(account), config),
    )
    await subscribe(connection, config, parker.subscription, parker.receive)
    await subscribe(connection, config, completer.subscription, completer.receive)
    assert [d.attempt.root for d in await parker.until(1)] == [1]
    assert [d.attempt.root for d in await completer.until(1)] == [1]
    fold = State(
        id=mint(),
        prior=opening_fold,
        event=Event(occurrence=w, stream=account, version=Version(1), position=landed),
    )
    later = await append(
        connection, config, an_append(account, AtVersion(version=Version(1)), withdrawal(9)), fold
    )
    assert isinstance(later, Position)
    assert [d.event.position for d in await parker.until(2)] == [landed, later]
    assert [d.event.position for d in await completer.until(2)] == [landed, later]
    await asyncio.sleep(config.ack_wait.root.total_seconds() + 0.5)
    assert len(parker.deliveries) == 2 and len(completer.deliveries) == 2
