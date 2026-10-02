"""The test program's composition root, spread over the acts a test performs: each act is one
constructed fact whose construction is the effect."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from decimal import Decimal

from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext

from ontok.core import NodeId
from ontok.events import (
    Append,
    AppendOutcome,
    Delivery,
    DeliveryIdentity,
    Events,
    Expectation,
    IdentityInterpreter,
    Initial,
    Outcome,
    Read,
    ReadModel,
    ReadOutcome,
    Start,
    State,
    Subscription,
)
from ontok.nats import (
    AckInterpreter,
    AckReply,
    ApiError,
    AtFrontier,
    Batch,
    BatchInterpreter,
    BatchReply,
    Bucket,
    ConsumerInfo,
    ConsumerInterpreter,
    ConsumerReply,
    Deleted,
    DuplicateMessage,
    DurableConsumerRequest,
    Entry,
    EntryInterpreter,
    EntryReply,
    EphemeralConsumerRequest,
    Keeping,
    KeyLookup,
    KvReply,
    MessageGetInterpreter,
    NatsConfig,
    NewEntry,
    NoEntry,
    NoStream,
    Prior,
    PullConsumer,
    PullInterpreter,
    PushConsumer,
    ReadReply,
)

from .program import BankRoute, Page, RulingConstructor, TransactionConstructor
from .world import Amount, Balance


def mint() -> NodeId:
    return NodeId(str(uuid.uuid7()))  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownArgumentType]


def delivered(subscription: Subscription, route: BankRoute) -> Delivery:
    return Delivery(
        id=IdentityInterpreter(
            action=DeliveryIdentity(
                subscription=subscription.id, event=route.event.occurrence.id, attempt=route.attempt
            ),
            uuid5=uuid.uuid5,
        ).execute(),
        action=subscription,
        event=route.event,
        attempt=route.attempt,
    )


async def append(
    client: Client, config: NatsConfig, action: Append, prior: Initial | State
) -> AppendOutcome | DuplicateMessage | ApiError:
    batch = Batch(append=action, prior=prior)
    return BatchReply(
        batch=batch,
        reply=await BatchInterpreter(action=batch, wait=config.reply_wait, client=client).execute(),
    ).outcome


async def read(
    client: Client, js: JetStreamContext, config: NatsConfig, action: Read
) -> ReadOutcome:
    info = await ConsumerInterpreter(
        action=EphemeralConsumerRequest(
            stream_name=config.stream, config=PullConsumer(read=action).config
        ),
        wait=config.reply_wait,
        client=client,
    ).execute()
    assert isinstance(info, ConsumerInfo), info
    pending = ReadReply(read=action, info=info).pending
    if isinstance(pending, NoStream):
        return Expectation.NO_STREAM
    if isinstance(pending, AtFrontier):
        return pending.frontier
    return Page(
        messages=await PullInterpreter(action=pending, wait=config.reply_wait, client=js).execute()
    ).events


async def subscribe(
    client: Client,
    config: NatsConfig,
    subscription: Subscription,
    callback: Callable[[Msg], Awaitable[None]],
) -> ConsumerReply:
    consumer = PushConsumer(
        subscription=subscription, ack_wait=config.ack_wait, max_deliver=config.max_deliver
    )
    reply = await ConsumerInterpreter(
        action=DurableConsumerRequest(stream_name=config.stream, config=consumer.config),
        wait=config.reply_wait,
        client=client,
    ).execute()
    await client.subscribe(  # pyright: ignore[reportUnknownMemberType]
        consumer.deliver_subject.root, queue=consumer.durable_name.root, cb=callback
    )
    return reply


class Clerk:
    """A subscriber that records every Delivery it receives and ends each one as the Ruling says."""

    def __init__(self, client: Client, subscription: Subscription, config: NatsConfig) -> None:
        self.client = client
        self.subscription = subscription
        self.config = config
        self.deliveries: list[Delivery] = []
        self.refused: list[bytes] = []

    async def receive(self, msg: Msg) -> None:
        route = BankRoute.receive(msg)
        try:
            delivery = delivered(self.subscription, route)
        except Exception:
            self.refused.append(route.message.payload.root)
            return
        self.deliveries.append(delivery)
        ruling = RulingConstructor.validate_python(route, from_attributes=True)
        await AckInterpreter(
            wait=self.config.reply_wait,
            action=AckReply(reply=route.message.reply, outcome=ruling.outcome),
            client=self.client,
        ).execute()

    async def until(self, count: int, timeout: float = 5.0) -> list[Delivery]:
        deadline = asyncio.get_running_loop().time() + timeout
        while len(self.deliveries) < count and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.05)
        return list(self.deliveries)


class Silent(Clerk):
    """A subscriber that records every Delivery and never ends any of them."""

    async def receive(self, msg: Msg) -> None:
        route = BankRoute.receive(msg)
        self.deliveries.append(delivered(self.subscription, route))


class Slow(Clerk):
    """A subscriber that ends every Delivery only after a delay longer than the ack wait."""

    def __init__(
        self, client: Client, subscription: Subscription, config: NatsConfig, delay: float
    ) -> None:
        super().__init__(client, subscription, config)
        self.delay = delay

    async def receive(self, msg: Msg) -> None:
        route = BankRoute.receive(msg)
        self.deliveries.append(delivered(self.subscription, route))
        await asyncio.sleep(self.delay)
        await AckInterpreter(
            wait=self.config.reply_wait,
            action=AckReply(
                reply=route.message.reply,
                outcome=RulingConstructor.validate_python(route, from_attributes=True).outcome,
            ),
            client=self.client,
        ).execute()


async def lookup(client: Client, config: NatsConfig, identity: NodeId) -> KvReply:
    return await MessageGetInterpreter(
        action=KeyLookup(bucket=config.bucket, id=identity), wait=config.reply_wait, client=client
    ).execute()


async def persist(
    client: Client, config: NatsConfig, read_model: ReadModel, prior: Prior
) -> Keeping:
    entry = NewEntry(bucket=Bucket(config.bucket.root), read_model=read_model, prior=prior)
    return EntryReply(
        entry=entry,
        reply=await EntryInterpreter(action=entry, wait=config.reply_wait, client=client).execute(),
    ).keeping


class Bookkeeper(Clerk):
    """A subscriber whose delivery is only a trigger: it looks up the account's balance, reads
    the stream after it, folds what the store returns, writes the balance against the entry
    it read, and completes the delivery."""

    def __init__(
        self,
        client: Client,
        js: JetStreamContext,
        subscription: Subscription,
        config: NatsConfig,
    ) -> None:
        super().__init__(client, subscription, config)
        self.js = js
        self.kept: list[Keeping] = []

    async def receive(self, msg: Msg) -> None:
        route = BankRoute.receive(msg)
        self.deliveries.append(delivered(self.subscription, route))
        held = await lookup(self.client, self.config, route.stream)
        opening = Amount(Decimal(0))
        before = Balance.model_validate_json(held.data) if isinstance(held, Entry) else None
        prior = (
            held
            if isinstance(held, Entry | Deleted)
            else NoEntry.model_validate(held, from_attributes=True)
        )
        outcome = await read(
            self.client,
            self.js,
            self.config,
            Read(
                id=mint(),
                role=self.subscription.role,
                goal=self.subscription.goal,
                stream=route.stream,
                after=before.after if before is not None else Start.BEGINNING,
            ),
        )
        if isinstance(outcome, Events):
            self.kept.append(
                await persist(
                    self.client,
                    self.config,
                    Balance(
                        id=route.stream,
                        stream=route.stream,
                        position=outcome.root[-1].position,
                        amount=Amount(
                            (before.amount.root if before is not None else opening.root)
                            + sum(
                                TransactionConstructor.validate_json(
                                    e.occurrence.model_dump_json()
                                ).signed.root
                                for e in outcome.root
                            )
                        ),
                    ),
                    prior,
                )
            )
        await AckInterpreter(
            action=AckReply(reply=route.message.reply, outcome=Outcome.COMPLETE),
            wait=self.config.reply_wait,
            client=self.client,
        ).execute()


def balance_of(events: Events) -> Balance:
    return Balance(
        id=events.root[0].stream,
        stream=events.root[0].stream,
        position=events.root[-1].position,
        amount=Amount(
            sum(
                (
                    TransactionConstructor.validate_json(e.occurrence.model_dump_json()).signed.root
                    for e in events.root
                ),
                Decimal(0),
            )
        ),
    )
