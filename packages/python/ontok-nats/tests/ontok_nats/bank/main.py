"""The bank's composition root: its configuration, its connection, and the one expression each
of its callbacks returns."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from functools import partial

import nats
from nats.aio.client import Client
from nats.aio.msg import Msg

from ontok.core import Goal, NodeId, Role
from ontok.events import (
    Append,
    AppendOutcome,
    Ending,
    Initial,
    Page,
    Read,
    ReadModelLookup,
    ReadOutcome,
    Start,
    State,
    Subscription,
)
from ontok.nats import (
    AckInterpreter,
    AckReply,
    Batch,
    BatchInterpreter,
    ConsumerDelivery,
    ConsumerInterpreter,
    ConsumerReply,
    DuplicateMessage,
    DurableConsumerRequest,
    EntryInterpreter,
    EphemeralConsumerRequest,
    Keeping,
    KeyLookup,
    MessageGetInterpreter,
    NatsConfig,
    NewEntry,
    Prior,
    Pull,
    PullConsumer,
    PullInterpreter,
    PushConsumer,
    ReadReply,
)

from .account import Balance, Statement
from .clerk import RulingConstructor
from .config import BankConfig
from .route import BalanceRoute, BalanceRouteConstructor, BankRoute


def mint() -> NodeId:
    return NodeId(f"{uuid.uuid7()}")  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]


async def append(
    client: Client, config: NatsConfig, action: Append, prior: Initial | State
) -> AppendOutcome | DuplicateMessage:
    return (
        await BatchInterpreter(
            action=Batch(append=action, prior=prior), wait=config.reply_wait, client=client
        ).execute()
    ).outcome


async def page(client: Client, config: NatsConfig, action: Read) -> Page:
    return Page(
        after=action.after,
        events=tuple(
            BankRoute(message=message).event
            for message in (
                await PullInterpreter(
                    action=Pull.model_validate(
                        ReadReply(
                            read=action,
                            creation=await ConsumerInterpreter(
                                action=EphemeralConsumerRequest(
                                    stream_name=config.stream,
                                    config=PullConsumer(read=action).config,
                                ),
                                wait=config.reply_wait,
                                client=client,
                            ).execute(),
                        ).pulling
                    ),
                    wait=config.reply_wait,
                    client=client,
                ).execute()
            ).messages.root
        ),
    )


async def read(client: Client, config: NatsConfig, action: Read) -> ReadOutcome:
    return (await page(client, config, action)).outcome


async def lookup(client: Client, config: NatsConfig, action: ReadModelLookup) -> BalanceRoute:
    return BalanceRouteConstructor.validate_python(
        await MessageGetInterpreter(
            action=KeyLookup(bucket=config.bucket, action=action),
            wait=config.reply_wait,
            client=client,
        ).execute(),
        from_attributes=True,
    )


async def persist(client: Client, config: NatsConfig, balance: Balance, prior: Prior) -> Keeping:
    return (
        await EntryInterpreter(
            action=NewEntry(bucket=config.bucket, action=balance.persistence, prior=prior),
            wait=config.reply_wait,
            client=client,
        ).execute()
    ).keeping


async def rule(
    client: Client, config: NatsConfig, subscription: Subscription, route: BankRoute
) -> Ending:
    return await AckInterpreter(
        action=AckReply(
            ending=Ending(
                delivery=ConsumerDelivery(route=route, subscription=subscription).delivery,
                outcome=RulingConstructor.validate_python(route, from_attributes=True).outcome,
            ),
            reply=route.message.reply,
        ),
        wait=config.reply_wait,
        client=client,
    ).execute()


async def book(
    client: Client, config: NatsConfig, subscription: Subscription, route: BankRoute
) -> Ending:
    return await AckInterpreter(
        action=AckReply(
            ending=Ending(
                delivery=ConsumerDelivery(route=route, subscription=subscription).delivery,
                outcome=(
                    await persist(
                        client,
                        config,
                        Statement(
                            held=(
                                books := await lookup(
                                    client, config, ReadModelLookup(id=route.stream)
                                )
                            ).balance,
                            page=await page(
                                client,
                                config,
                                Read(
                                    id=mint(),
                                    role=subscription.role,
                                    goal=subscription.goal,
                                    stream=route.stream,
                                    after=books.balance.after,
                                ),
                            ),
                        ).balance,
                        books.prior,
                    )
                ).outcome,
            ),
            reply=route.message.reply,
        ),
        wait=config.reply_wait,
        client=client,
    ).execute()


async def subscribe(
    client: Client,
    config: NatsConfig,
    subscription: Subscription,
    callback: Callable[[Msg], Awaitable[None]],
) -> ConsumerReply:
    consumer = PushConsumer(
        subscription=subscription, ack_wait=config.ack_wait, max_deliver=config.max_deliver
    )
    creation = await ConsumerInterpreter(
        action=DurableConsumerRequest(stream_name=config.stream, config=consumer.config),
        wait=config.reply_wait,
        client=client,
    ).execute()
    await client.subscribe(  # pyright: ignore[reportUnknownMemberType]
        consumer.deliver_subject.root, queue=consumer.durable_name.root, cb=callback
    )
    return creation.reply


async def ruled(client: Client, config: NatsConfig, subscription: Subscription, msg: Msg) -> None:
    await rule(client, config, subscription, BankRoute.receive(msg))


async def booked(client: Client, config: NatsConfig, subscription: Subscription, msg: Msg) -> None:
    await book(client, config, subscription, BankRoute.receive(msg))


async def main() -> None:
    config = NatsConfig()  # pyright: ignore[reportCallIssue]
    bank = BankConfig()  # pyright: ignore[reportCallIssue]
    client = await nats.connect(  # pyright: ignore[reportUnknownMemberType]
        f"{config.url.root}",
        user=config.user.root,
        password=config.credentials.get_secret_value(),
    )
    teller = Role(id=bank.teller)
    books_balanced = Goal(id=bank.books_balanced)
    clerk = Subscription(id=bank.clerk, role=teller, goal=books_balanced, begins=Start.BEGINNING)
    bookkeeper = Subscription(
        id=bank.bookkeeper, role=teller, goal=books_balanced, begins=Start.BEGINNING
    )
    await subscribe(client, config, clerk, partial(ruled, client, config, clerk))
    await subscribe(client, config, bookkeeper, partial(booked, client, config, bookkeeper))
    await asyncio.Event().wait()


def run() -> None:
    asyncio.run(main())
