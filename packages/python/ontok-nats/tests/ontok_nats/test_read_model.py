"""Every attack on the read model: racing writers, stale priors, a deleted key."""

import asyncio
from decimal import Decimal

import pytest
from nats.aio.client import Client
from nats.js.client import JetStreamContext

from ontok.core import NodeId
from ontok.events import Position
from ontok.nats import Deleted, Entry, EntryAck, EntryRefusal, NatsConfig, NoEntry

from .acts import lookup, mint, persist
from .world import Amount, Balance

pytestmark = [pytest.mark.nats, pytest.mark.asyncio(loop_scope="session")]


def balance(identity: NodeId, amount: int, position: int) -> Balance:
    return Balance(
        id=identity, stream=identity, position=Position(position), amount=Amount(Decimal(amount))
    )


async def test_two_writers_with_the_same_prior_and_exactly_one_is_kept(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    identity = mint()
    none = NoEntry.model_validate(await lookup(connection, config, identity), from_attributes=True)
    outcomes = await asyncio.gather(
        persist(connection, config, balance(identity, 1, 1), none),
        persist(connection, config, balance(identity, 2, 1), none),
    )
    assert sorted(type(o).__name__ for o in outcomes) == ["EntryAck", "EntryRefusal"]


async def test_a_write_against_a_stale_prior_is_refused_and_the_old_balance_stands(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    identity = mint()
    none = NoEntry.model_validate(await lookup(connection, config, identity), from_attributes=True)
    assert isinstance(await persist(connection, config, balance(identity, 10, 1), none), EntryAck)
    first = await lookup(connection, config, identity)
    assert isinstance(first, Entry)
    assert isinstance(
        await persist(connection, config, balance(identity, 20, 2), none), EntryRefusal
    )
    assert await lookup(connection, config, identity) == first


async def test_a_deleted_key_is_written_against_its_deletion(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    identity = mint()
    none = NoEntry.model_validate(await lookup(connection, config, identity), from_attributes=True)
    assert isinstance(await persist(connection, config, balance(identity, 10, 1), none), EntryAck)
    bucket = await jetstream.key_value(config.bucket.root)  # pyright: ignore[reportUnknownMemberType]
    await bucket.delete(identity.root)  # pyright: ignore[reportUnknownMemberType]
    gone = await lookup(connection, config, identity)
    assert isinstance(gone, Deleted)
    assert isinstance(await persist(connection, config, balance(identity, 30, 3), gone), EntryAck)
    again = await lookup(connection, config, identity)
    assert isinstance(again, Entry) and again.seq.root > gone.seq.root
