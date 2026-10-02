"""Every attack on the append: races, broken batches, misplaced expectations, duplicates, and
stale folds."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from nats.aio.client import Client
from nats.js.client import JetStreamContext

from ontok.core import Instant, NodeId, Timestamp
from ontok.events import (
    Append,
    AtVersion,
    Event,
    Events,
    Expectation,
    Initial,
    Occurrences,
    Position,
    Read,
    ReadOutcome,
    Start,
    State,
    Version,
    VersionMismatch,
)
from ontok.nats import Batch, DuplicateMessage, NatsConfig, PubAck, PublishReplyConstructor

from .acts import append, mint, read
from .world import BOOKS_BALANCED, TELLER, Amount, Deposited, Withdrawn

pytestmark = [pytest.mark.nats, pytest.mark.asyncio(loop_scope="session")]

NOW = Instant(at=Timestamp(datetime(2026, 10, 2, 12, 0, tzinfo=UTC)))


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


def a_read(stream: NodeId) -> Read:
    return Read(id=mint(), role=TELLER, goal=BOOKS_BALANCED, stream=stream, after=Start.BEGINNING)


async def test_two_tellers_race_the_same_fold_and_exactly_one_wins(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    opening = Initial(id=mint(), stream=account)
    left, right = (
        an_append(account, Expectation.NO_STREAM, deposit(1), deposit(2)),
        an_append(account, Expectation.NO_STREAM, deposit(3)),
    )
    outcomes = await asyncio.gather(
        append(connection, config, left, opening), append(connection, config, right, opening)
    )
    positions = [o for o in outcomes if isinstance(o, Position)]
    refusals = [o for o in outcomes if isinstance(o, VersionMismatch)]
    assert len(positions) == 1 and len(refusals) == 1
    held = await read(connection, jetstream, config, a_read(account))
    assert isinstance(held, Events)
    winner = left if len(held.root) == 2 else right
    assert tuple(e.occurrence for e in held.root) == winner.occurrences.root
    assert held.root[-1].position == positions[0]


async def test_a_batch_with_a_gap_lands_nothing(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    batch = Batch(
        append=an_append(account, Expectation.NO_STREAM, deposit(1), deposit(2), deposit(3)),
        prior=Initial(id=mint(), stream=account),
    )
    opening, _skipped = batch.messages
    await connection.publish(
        opening.subject.root,
        opening.payload.model_dump_json().encode(),
        headers=opening.headers.model_dump(by_alias=True),
    )
    reply = PublishReplyConstructor.validate_json(
        (
            await connection.request(
                batch.closing.subject.root,
                batch.closing.payload.model_dump_json().encode(),
                headers=batch.closing.headers.model_dump(by_alias=True),
            )
        ).data
    )
    assert not isinstance(reply, PubAck)
    assert await read(connection, jetstream, config, a_read(account)) is Expectation.NO_STREAM


async def test_a_batch_never_committed_is_abandoned_and_the_stream_stays_free(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    opening_fold = Initial(id=mint(), stream=account)
    stalled = Batch(
        append=an_append(account, Expectation.NO_STREAM, deposit(1), deposit(2)), prior=opening_fold
    )
    opening = stalled.messages[0]
    await connection.publish(
        opening.subject.root,
        opening.payload.model_dump_json().encode(),
        headers=opening.headers.model_dump(by_alias=True),
    )
    await connection.flush()
    assert await read(connection, jetstream, config, a_read(account)) is Expectation.NO_STREAM
    await asyncio.sleep(11)
    fresh = an_append(account, Expectation.NO_STREAM, deposit(9))
    assert await append(connection, config, fresh, opening_fold) == Position(
        await_position_of(await read(connection, jetstream, config, a_read(account)))
    )
    held = await read(connection, jetstream, config, a_read(account))
    assert (
        isinstance(held, Events)
        and tuple(e.occurrence for e in held.root) == fresh.occurrences.root
    )


def await_position_of(outcome: ReadOutcome) -> int:
    assert isinstance(outcome, Events)
    return outcome.root[-1].position.root


async def test_an_expectation_on_a_following_message_kills_the_batch(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    batch = Batch(
        append=an_append(account, Expectation.NO_STREAM, deposit(1), deposit(2), deposit(3)),
        prior=Initial(id=mint(), stream=account),
    )
    opening, following = batch.messages
    await connection.publish(
        opening.subject.root,
        opening.payload.model_dump_json().encode(),
        headers=opening.headers.model_dump(by_alias=True),
    )
    misplaced = following.headers.model_dump(by_alias=True) | {
        "Nats-Expected-Last-Subject-Sequence": "0"
    }
    await connection.publish(
        following.subject.root, following.payload.model_dump_json().encode(), headers=misplaced
    )
    reply = PublishReplyConstructor.validate_json(
        (
            await connection.request(
                batch.closing.subject.root,
                batch.closing.payload.model_dump_json().encode(),
                headers=batch.closing.headers.model_dump(by_alias=True),
            )
        ).data
    )
    assert not isinstance(reply, PubAck)
    assert await read(connection, jetstream, config, a_read(account)) is Expectation.NO_STREAM


async def test_the_same_occurrence_appended_twice_is_refused_and_held_once(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    opening_fold = Initial(id=mint(), stream=account)
    once = deposit(42)
    first = await append(
        connection, config, an_append(account, Expectation.NO_STREAM, once), opening_fold
    )
    assert isinstance(first, Position)
    after_first = State(
        id=mint(),
        prior=opening_fold,
        event=Event(occurrence=once, stream=account, version=Version(1), position=first),
    )
    second = await append(
        connection, config, an_append(account, AtVersion(version=Version(1)), once), after_first
    )
    assert isinstance(second, DuplicateMessage)
    held = await read(connection, jetstream, config, a_read(account))
    assert isinstance(held, Events)
    assert [e.occurrence.id for e in held.root] == [once.id]


async def test_an_append_from_a_stale_fold_is_refused_and_from_the_current_fold_lands(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    opening_fold = Initial(id=mint(), stream=account)
    first_occurrence = withdrawal(5)
    first = await append(
        connection,
        config,
        an_append(account, Expectation.NO_STREAM, first_occurrence),
        opening_fold,
    )
    assert isinstance(first, Position)
    after_first = State(
        id=mint(),
        prior=opening_fold,
        event=Event(
            occurrence=first_occurrence, stream=account, version=Version(1), position=first
        ),
    )
    second_occurrence = deposit(1)
    second = await append(
        connection,
        config,
        an_append(account, AtVersion(version=Version(1)), second_occurrence),
        after_first,
    )
    assert isinstance(second, Position)
    stale = await append(
        connection,
        config,
        an_append(account, AtVersion(version=Version(1)), deposit(2)),
        after_first,
    )
    assert isinstance(stale, VersionMismatch)
    current = State(
        id=mint(),
        prior=after_first,
        event=Event(
            occurrence=second_occurrence, stream=account, version=Version(2), position=second
        ),
    )
    landed = await append(
        connection, config, an_append(account, AtVersion(version=Version(2)), deposit(2)), current
    )
    assert isinstance(landed, Position) and landed.root > second.root


async def test_a_stream_of_three_hundred_reads_back_whole_in_one_pull(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    many = an_append(account, Expectation.NO_STREAM, *(withdrawal(i + 1) for i in range(300)))
    landed = await append(connection, config, many, Initial(id=mint(), stream=account))
    assert isinstance(landed, Position)
    held = await read(connection, jetstream, config, a_read(account))
    assert isinstance(held, Events)
    assert len(held.root) == 300
    first = landed.root - 300 + 1
    assert [e.position.root for e in held.root] == list(range(first, first + 300))
    assert tuple(e.occurrence for e in held.root) == many.occurrences.root
    assert [e.version.root for e in held.root] == list(range(1, 301))
