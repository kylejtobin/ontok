"""Every attack that takes the server down: kills after acknowledgement, mid-batch, and between
delivery and ending. Runs last."""

import asyncio
import shutil
import subprocess
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from nats.aio.client import Client
from nats.js.client import JetStreamContext
from testcontainers.compose import DockerCompose

from ontok.core import Instant, NodeId, Timestamp
from ontok.events import (
    Append,
    Event,
    Events,
    Expectation,
    Initial,
    NoStream,
    Occurrences,
    Position,
    Read,
    ReadModelLookup,
    Start,
    StreamSubscription,
    Version,
)
from ontok.nats import Batch, NatsConfig

from .acts import Bookkeeper, Clerk, Silent, balance_of
from .bank import Amount, Deposited, HeldBalance, Withdrawn
from .bank.main import append, lookup, mint, read, subscribe
from .world import BOOKS_BALANCED, TELLER

pytestmark = [pytest.mark.nats, pytest.mark.asyncio(loop_scope="session")]

NOW = Instant(at=Timestamp(datetime(2026, 10, 2, 17, 0, tzinfo=UTC)))
CONTAINER = "ontok-nats-conformance-nats-1"


def withdrawal(amount: int) -> Withdrawn:
    return Withdrawn(id=mint(), occurred=NOW, amount=Amount(Decimal(amount)))


def deposit(amount: int) -> Deposited:
    return Deposited(id=mint(), occurred=NOW, amount=Amount(Decimal(amount)))


def an_append(stream: NodeId, *occurrences: Deposited | Withdrawn) -> Append:
    return Append(
        id=mint(),
        role=TELLER,
        goal=BOOKS_BALANCED,
        stream=stream,
        expected=Expectation.NO_STREAM,
        occurrences=Occurrences(occurrences),
    )


def a_read(stream: NodeId) -> Read:
    return Read(id=mint(), role=TELLER, goal=BOOKS_BALANCED, stream=stream, after=Start.BEGINNING)


async def kill_and_restart(server: DockerCompose, connection: Client) -> None:
    docker = shutil.which("docker")
    assert docker is not None
    subprocess.run([docker, "kill", CONTAINER], check=True, capture_output=True)  # noqa: S603
    server.start()
    deadline = asyncio.get_running_loop().time() + 15
    while not connection.is_connected and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.1)
    assert connection.is_connected
    await asyncio.sleep(0.5)


async def test_an_acknowledged_append_survives_a_kill(
    server: DockerCompose, connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    w = withdrawal(1)
    landed = await append(
        connection, config, an_append(account, w), Initial(id=mint(), stream=account)
    )
    assert isinstance(landed, Position)
    await kill_and_restart(server, connection)
    assert await read(connection, config, a_read(account)) == Events(
        (Event(occurrence=w, stream=account, version=Version(1), position=landed),)
    )


async def test_a_batch_cut_by_a_kill_lands_nothing_and_the_stream_stays_free(
    server: DockerCompose, connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    opening_fold = Initial(id=mint(), stream=account)
    cut = Batch(append=an_append(account, deposit(1), deposit(2), deposit(3)), prior=opening_fold)
    for message in cut.messages:
        await connection.publish(
            message.subject.root,
            message.payload.model_dump_json().encode(),
            headers=message.headers.model_dump(by_alias=True),
        )
    await connection.flush()
    await kill_and_restart(server, connection)
    assert await read(connection, config, a_read(account)) == NoStream()
    fresh = an_append(account, deposit(4))
    landed = await append(connection, config, fresh, opening_fold)
    assert isinstance(landed, Position)
    assert await read(connection, config, a_read(account)) == Events(
        (
            Event(
                occurrence=fresh.occurrences.root[0],
                stream=account,
                version=Version(1),
                position=landed,
            ),
        )
    )


async def test_a_delivery_open_across_a_restart_is_delivered_once_more(
    server: DockerCompose, connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    landed = await append(
        connection, config, an_append(account, withdrawal(2)), Initial(id=mint(), stream=account)
    )
    assert isinstance(landed, Position)
    silent = Silent(
        connection,
        StreamSubscription(
            id=mint(), role=TELLER, goal=BOOKS_BALANCED, begins=Start.BEGINNING, stream=account
        ),
        config,
    )
    await subscribe(connection, config, silent.subscription, silent.receive)
    assert [d.attempt.root for d in await silent.until(1)] == [1]
    await kill_and_restart(server, connection)
    deliveries = await silent.until(2, timeout=config.ack_wait.root.total_seconds() * 3)
    assert [d.attempt.root for d in deliveries][:2] == [1, 2]
    assert deliveries[1].event == deliveries[0].event


async def test_a_kill_may_replay_endings_not_yet_persisted_but_never_as_a_first_attempt(
    server: DockerCompose, connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    opening_fold = Initial(id=mint(), stream=account)
    first = an_append(account, withdrawal(5), withdrawal(6))
    landed = await append(connection, config, first, opening_fold)
    assert isinstance(landed, Position)
    clerk = Clerk(
        connection,
        StreamSubscription(
            id=mint(), role=TELLER, goal=BOOKS_BALANCED, begins=Start.BEGINNING, stream=account
        ),
        config,
    )
    await subscribe(connection, config, clerk.subscription, clerk.receive)
    before = await clerk.until(2)
    assert [d.attempt.root for d in before] == [1, 1]
    await kill_and_restart(server, connection)
    await asyncio.sleep(config.ack_wait.root.total_seconds() + 0.5)
    replayed = clerk.deliveries[len(before) :]
    assert all(d.attempt.root == 2 for d in replayed), replayed
    assert {d.event.position.root for d in replayed} <= {d.event.position.root for d in before}
    later = Append(
        id=mint(),
        role=TELLER,
        goal=BOOKS_BALANCED,
        stream=account,
        expected=Expectation.ANY,
        occurrences=Occurrences((withdrawal(7),)),
    )
    assert isinstance(await append(connection, config, later, opening_fold), Position)
    after = await clerk.until(len(clerk.deliveries) + 1)
    assert after[-1].event.occurrence.id == later.occurrences.root[0].id
    assert after[-1].attempt.root == 1


async def test_the_books_balance_across_a_kill_in_the_middle_of_the_day(
    server: DockerCompose, connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    opening_fold = Initial(id=mint(), stream=account)
    books = Bookkeeper(
        connection,
        StreamSubscription(
            id=mint(), role=TELLER, goal=BOOKS_BALANCED, begins=Start.BEGINNING, stream=account
        ),
        config,
    )
    await subscribe(connection, config, books.subscription, books.receive)
    first = an_append(account, deposit(10), deposit(20), withdrawal(5))
    assert isinstance(await append(connection, config, first, opening_fold), Position)
    await books.until(1)
    await kill_and_restart(server, connection)
    later = Append(
        id=mint(),
        role=TELLER,
        goal=BOOKS_BALANCED,
        stream=account,
        expected=Expectation.ANY,
        occurrences=Occurrences((deposit(7),)),
    )
    assert isinstance(await append(connection, config, later, opening_fold), Position)
    await books.until(len(books.deliveries) + 1)
    await asyncio.sleep(config.ack_wait.root.total_seconds() + 0.5)
    held = await lookup(connection, config, ReadModelLookup(id=account))
    assert isinstance(held, HeldBalance)
    whole = await read(connection, config, a_read(account))
    assert isinstance(whole, Events)
    assert held.balance == balance_of(whole)
