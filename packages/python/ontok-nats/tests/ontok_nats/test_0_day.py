"""One business day at the bank, every step a round trip through the module."""

import pytest
from nats.aio.client import Client
from nats.js.client import JetStreamContext

from ontok.events import Expectation, VersionMismatch
from ontok.nats import Deleted, Entry, EntryAck, EntryRefusal, NatsConfig, NoEntry

from . import world as w
from .acts import Clerk, append, lookup, persist, read, subscribe
from .program import TransactionConstructor

pytestmark = [pytest.mark.nats, pytest.mark.asyncio(loop_scope="session")]


async def test_the_morning_opens_both_accounts(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    assert await append(connection, config, w.MORNING_A, w.A_OPENING) == w.MORNING_A_LANDS_AT
    assert await append(connection, config, w.MORNING_B, w.B_OPENING) == w.MORNING_B_LANDS_AT


async def test_the_transfer_moves_money_under_the_fold(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    assert await append(connection, config, w.TRANSFER_OUT, w.A_AFTER_30) == w.TRANSFER_OUT_LANDS_AT
    assert await append(connection, config, w.TRANSFER_IN, w.B_AFTER_10) == w.TRANSFER_IN_LANDS_AT


async def test_a_stale_screen_is_refused_and_nothing_lands(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    outcome = await append(connection, config, w.STALE_DEPOSIT, w.A_AFTER_30)
    assert outcome == w.STALE_DEPOSIT_REFUSED
    assert isinstance(outcome, VersionMismatch)


async def test_the_cash_machine_asserts_nothing(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    assert await append(connection, config, w.CASH_MACHINE, w.B_AFTER_5B) == w.CASH_MACHINE_LANDS_AT


async def test_both_streams_read_back_whole(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    assert await read(connection, jetstream, config, w.READ_A) == w.A_EVENTS
    assert await read(connection, jetstream, config, w.READ_B) == w.B_EVENTS


async def test_an_unknown_stream_reads_as_no_stream(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    assert await read(connection, jetstream, config, w.READ_NOWHERE) is Expectation.NO_STREAM


async def test_the_clerk_sees_everything_once_each_except_what_she_returns(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    clerk = Clerk(connection, w.CLERK, config)
    await subscribe(connection, config, w.CLERK, clerk.receive)
    deliveries = await clerk.until(13, timeout=8.0)
    assert sorted(d.event.position.root for d in deliveries) == [
        1,
        1,
        2,
        2,
        3,
        4,
        4,
        5,
        6,
        6,
        7,
        7,
        8,
    ]
    assert sorted(d.event.position.root for d in deliveries if d.attempt.root == 2) == [
        1,
        2,
        4,
        6,
        7,
    ]
    assert all(
        TransactionConstructor.validate_json(d.event.occurrence.model_dump_json()).kind
        == "deposited"
        for d in deliveries
        if d.attempt.root == 2
    )
    assert await clerk.until(14, timeout=1.5) == deliveries


async def test_the_fraud_analyst_sees_only_what_happens_after_she_sits_down(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    analyst = Clerk(connection, w.FRAUD_ANALYST, config)
    await subscribe(connection, config, w.FRAUD_ANALYST, analyst.receive)
    assert await analyst.until(1, timeout=1.0) == []
    assert await append(connection, config, w.LATE_DEPOSIT, w.A_AFTER_20) == w.LATE_DEPOSIT_LANDS_AT
    deliveries = await analyst.until(2)
    assert [d.event for d in deliveries] == [w.LATE_EVENT, w.LATE_EVENT]
    assert [d.attempt.root for d in deliveries] == [1, 2]


async def test_the_auditor_begins_after_the_second_event_on_b(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    auditor = Clerk(connection, w.AUDITOR, config)
    await subscribe(connection, config, w.AUDITOR, auditor.receive)
    deliveries = await auditor.until(3)
    assert sorted((d.event.position.root, d.attempt.root) for d in deliveries) == [
        (7, 1),
        (7, 2),
        (8, 1),
    ]


async def test_the_statement_is_written_only_against_what_was_read(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    none = await lookup(connection, config, w.BALANCE_A)
    first = await persist(
        connection, config, w.BALANCE_A_MORNING, NoEntry.model_validate(none, from_attributes=True)
    )
    assert isinstance(first, EntryAck)
    held = await lookup(connection, config, w.BALANCE_A)
    assert isinstance(held, Entry)
    assert w.Balance.model_validate_json(held.data) == w.BALANCE_A_MORNING
    stale = await persist(
        connection,
        config,
        w.BALANCE_A_AFTER_TRANSFER,
        NoEntry.model_validate(none, from_attributes=True),
    )
    assert isinstance(stale, EntryRefusal)
    second = await persist(connection, config, w.BALANCE_A_AFTER_TRANSFER, held)
    assert isinstance(second, EntryAck)
    now = await lookup(connection, config, w.BALANCE_A)
    assert isinstance(now, Entry)
    assert w.Balance.model_validate_json(now.data) == w.BALANCE_A_AFTER_TRANSFER
    assert not isinstance(now, Deleted)
