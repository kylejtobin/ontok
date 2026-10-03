"""What NATS answers when it refuses, and what the Ack interpreter hands back."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext

from ontok.core import Instant, Timestamp
from ontok.events import (
    Append,
    Ending,
    Expectation,
    Initial,
    Occurrences,
    Outcome,
    Position,
    Read,
    ReadModelLookup,
    Start,
    StreamSubscription,
)
from ontok.nats import (
    AckInterpreter,
    AckReply,
    ApiError,
    Bucket,
    ConsumerDelivery,
    ConsumerInterpreter,
    EphemeralConsumerRequest,
    KeyLookup,
    MessageGetInterpreter,
    NatsConfig,
    NoEntry,
    Pull,
    PullConsumer,
    ReadRefusal,
    ReadReply,
    StreamName,
)

from .bank import Amount, BankRoute, Deposited
from .bank.main import append, mint, subscribe
from .world import BOOKS_BALANCED, TELLER

pytestmark = [pytest.mark.nats, pytest.mark.asyncio(loop_scope="session")]

NOW = Instant(at=Timestamp(datetime(2026, 10, 3, 9, 0, tzinfo=UTC)))


async def test_a_lookup_in_a_bucket_that_does_not_exist_is_answered_with_the_refusal(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    lookup = KeyLookup(bucket=Bucket("NOWHERE"), action=ReadModelLookup(id=mint()))
    answered = await MessageGetInterpreter(
        action=lookup, wait=config.reply_wait, client=connection
    ).execute()
    assert answered.lookup == lookup
    assert type(answered.reply) is ApiError


async def test_a_lookup_of_a_key_never_written_is_answered_with_no_entry(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    lookup = KeyLookup(bucket=config.bucket, action=ReadModelLookup(id=mint()))
    answered = await MessageGetInterpreter(
        action=lookup, wait=config.reply_wait, client=connection
    ).execute()
    assert answered.lookup == lookup
    assert type(answered.reply) is NoEntry


async def test_a_read_of_a_stream_nats_does_not_have_is_a_refusal_with_nothing_to_pull(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    read = Read(id=mint(), role=TELLER, goal=BOOKS_BALANCED, stream=mint(), after=Start.BEGINNING)
    reply = ReadReply(
        read=read,
        creation=await ConsumerInterpreter(
            action=EphemeralConsumerRequest(
                stream_name=StreamName("NOWHERE"), config=PullConsumer(read=read).config
            ),
            wait=config.reply_wait,
            client=connection,
        ).execute(),
    )
    assert type(reply.creation.reply) is ApiError
    pulling = reply.pulling
    assert type(pulling) is ReadRefusal
    assert pulling.read == read
    assert pulling.error == reply.creation.reply


async def test_a_read_of_the_stream_nats_has_is_a_pull(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    read = Read(id=mint(), role=TELLER, goal=BOOKS_BALANCED, stream=mint(), after=Start.BEGINNING)
    reply = ReadReply(
        read=read,
        creation=await ConsumerInterpreter(
            action=EphemeralConsumerRequest(
                stream_name=config.stream, config=PullConsumer(read=read).config
            ),
            wait=config.reply_wait,
            client=connection,
        ).execute(),
    )
    pulling = reply.pulling
    assert type(pulling) is Pull
    assert pulling.stream_name == config.stream
    assert pulling.batch.root == 0


async def test_the_ack_interpreter_returns_the_ending_it_was_given(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    landed = await append(
        connection,
        config,
        Append(
            id=mint(),
            role=TELLER,
            goal=BOOKS_BALANCED,
            stream=account,
            expected=Expectation.NO_STREAM,
            occurrences=Occurrences(
                (Deposited(id=mint(), occurred=NOW, amount=Amount(Decimal(4))),)
            ),
        ),
        Initial(id=mint(), stream=account),
    )
    assert isinstance(landed, Position)
    subscription = StreamSubscription(
        id=mint(), role=TELLER, goal=BOOKS_BALANCED, begins=Start.BEGINNING, stream=account
    )
    given: asyncio.Future[Ending] = asyncio.get_running_loop().create_future()
    returned: asyncio.Future[Ending] = asyncio.get_running_loop().create_future()

    async def receive(msg: Msg) -> None:
        route = BankRoute.receive(msg)
        ending = Ending(
            delivery=ConsumerDelivery(route=route, subscription=subscription).delivery,
            outcome=Outcome.COMPLETE,
        )
        given.set_result(ending)
        returned.set_result(
            await AckInterpreter(
                action=AckReply(ending=ending, reply=route.message.reply),
                wait=config.reply_wait,
                client=connection,
            ).execute()
        )

    await subscribe(connection, config, subscription, receive)
    ending = await asyncio.wait_for(returned, timeout=5.0)
    assert ending == await given
    assert ending.outcome is Outcome.COMPLETE
    assert ending.delivery.event.position == landed
