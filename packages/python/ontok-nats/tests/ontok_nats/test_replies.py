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
    Ack,
    Acked,
    AckInterpreter,
    AckReply,
    ApiError,
    Bucket,
    ConsumerDelivery,
    ConsumerInterpreter,
    DeliveredMessage,
    EphemeralConsumerRequest,
    KeyLookup,
    MessageGetInterpreter,
    NatsConfig,
    NoEntry,
    NoMessages,
    NoResponders,
    Pull,
    PullConsumer,
    PullInterpreter,
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
    pulled = await PullInterpreter(
        action=pulling, wait=config.reply_wait, client=connection
    ).execute()
    assert pulled.pull == pulling
    assert [type(answer) for answer in pulled.answers.root] == [NoResponders]
    assert pulled.messages.root == ()


async def test_a_read_of_a_stream_with_no_events_is_a_pull_answered_with_no_messages(
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
    assert pulling.pending.root == 0
    pulled = await PullInterpreter(
        action=pulling, wait=config.reply_wait, client=connection
    ).execute()
    assert [type(answer) for answer in pulled.answers.root] == [NoMessages]
    assert pulled.messages.root == ()


async def test_the_ack_interpreter_returns_the_ack_with_its_confirmation_and_the_ending(
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
    returned: asyncio.Future[Acked] = asyncio.get_running_loop().create_future()

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
    acked = await asyncio.wait_for(returned, timeout=5.0)
    assert acked.ending == await given
    assert acked.ack.ack is Ack.ACK
    assert acked.ending.outcome is Outcome.COMPLETE
    assert acked.ending.delivery.event.position == landed


async def test_a_pull_is_answered_with_every_pending_message_then_no_messages(
    connection: Client, jetstream: JetStreamContext, config: NatsConfig
) -> None:
    account = mint()
    deposits = tuple(
        Deposited(id=mint(), occurred=NOW, amount=Amount(Decimal(n))) for n in (1, 2, 3)
    )
    landed = await append(
        connection,
        config,
        Append(
            id=mint(),
            role=TELLER,
            goal=BOOKS_BALANCED,
            stream=account,
            expected=Expectation.NO_STREAM,
            occurrences=Occurrences(deposits),
        ),
        Initial(id=mint(), stream=account),
    )
    assert isinstance(landed, Position)
    read = Read(id=mint(), role=TELLER, goal=BOOKS_BALANCED, stream=account, after=Start.BEGINNING)
    pulled = await PullInterpreter(
        action=ReadReply(
            read=read,
            creation=await ConsumerInterpreter(
                action=EphemeralConsumerRequest(
                    stream_name=config.stream, config=PullConsumer(read=read).config
                ),
                wait=config.reply_wait,
                client=connection,
            ).execute(),
        ).pulling,
        wait=config.reply_wait,
        client=connection,
    ).execute()
    assert [type(answer) for answer in pulled.answers.root] == [
        DeliveredMessage,
        DeliveredMessage,
        DeliveredMessage,
        NoMessages,
    ]
    assert [BankRoute(message=m).occurrence for m in pulled.messages.root] == list(deposits)
