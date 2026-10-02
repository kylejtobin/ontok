"""The test program's composition root, spread over the acts a test performs: each act is one
constructed fact whose construction is the effect."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable

from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext

from ontok.core import NodeId
from ontok.events import (
    Append,
    AppendOutcome,
    Delivery,
    DeliveryIdentity,
    Expectation,
    IdentityInterpreter,
    Initial,
    Read,
    ReadModel,
    ReadOutcome,
    State,
    Subscription,
)
from ontok.nats import (
    AckInterpreter,
    AckReply,
    ApiError,
    Batch,
    BatchInterpreter,
    BatchReply,
    Bucket,
    ConsumerInfo,
    ConsumerInterpreter,
    ConsumerReply,
    DuplicateMessage,
    DurableConsumerRequest,
    EntryInterpreter,
    EntryReply,
    EphemeralConsumerRequest,
    Keeping,
    KeyLookup,
    KvReply,
    MessageGetInterpreter,
    NatsConfig,
    NewEntry,
    NothingPending,
    Prior,
    Pull,
    PullConsumer,
    PullInterpreter,
    PullOrNothingConstructor,
    PushConsumer,
)

from .program import BankRoute, Page, RulingConstructor


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
            stream_name=config.stream,
            config=PullConsumer.model_validate(action, from_attributes=True).config,
        ),
        wait=config.reply_wait,
        client=client,
    ).execute()
    assert isinstance(info, ConsumerInfo), info
    pull = PullOrNothingConstructor.validate_python(info, from_attributes=True)
    if isinstance(pull, NothingPending):
        return Expectation.NO_STREAM
    assert isinstance(pull, Pull)
    return Page(
        messages=await PullInterpreter(action=pull, wait=config.reply_wait, client=js).execute()
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
