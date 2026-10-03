"""What a test watches: subscribers that record every Delivery they receive before handing it to
the bank's callback, and the balance a test computes for itself from a whole read."""

import asyncio
from decimal import Decimal

from nats.aio.client import Client
from nats.aio.msg import Msg
from pydantic import ValidationError

from ontok.core import NodeId
from ontok.events import Delivery, Events, Subscription
from ontok.nats import ConsumerDelivery, NatsConfig

from .bank import Amount, Balance, BankRoute, TransactionConstructor
from .bank.main import book, rule


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
            delivery = ConsumerDelivery(route=route, subscription=self.subscription).delivery
        except ValidationError:
            self.refused.append(route.message.payload.root)
            return
        self.deliveries.append(delivery)
        await rule(self.client, self.config, self.subscription, route)

    async def until(self, count: int, timeout: float = 5.0) -> list[Delivery]:
        deadline = asyncio.get_running_loop().time() + timeout
        while len(self.deliveries) < count and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.05)
        return list(self.deliveries)

    def of(self, occurrence: NodeId) -> list[Delivery]:
        return [d for d in self.deliveries if d.event.occurrence.id == occurrence]

    async def until_seen(self, occurrence: NodeId, timeout: float = 5.0) -> list[Delivery]:
        deadline = asyncio.get_running_loop().time() + timeout
        while not self.of(occurrence) and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.05)
        return self.of(occurrence)


class Silent(Clerk):
    """A subscriber that records every Delivery and never ends any of them."""

    async def receive(self, msg: Msg) -> None:
        route = BankRoute.receive(msg)
        self.deliveries.append(
            ConsumerDelivery(route=route, subscription=self.subscription).delivery
        )


class Slow(Clerk):
    """A subscriber that ends every Delivery only after a delay longer than the ack wait."""

    def __init__(
        self, client: Client, subscription: Subscription, config: NatsConfig, delay: float
    ) -> None:
        super().__init__(client, subscription, config)
        self.delay = delay

    async def receive(self, msg: Msg) -> None:
        route = BankRoute.receive(msg)
        self.deliveries.append(
            ConsumerDelivery(route=route, subscription=self.subscription).delivery
        )
        await asyncio.sleep(self.delay)
        await rule(self.client, self.config, self.subscription, route)


class Bookkeeper(Clerk):
    """A subscriber that records every Delivery and hands it to the bank's bookkeeper."""

    async def receive(self, msg: Msg) -> None:
        route = BankRoute.receive(msg)
        self.deliveries.append(
            ConsumerDelivery(route=route, subscription=self.subscription).delivery
        )
        await book(self.client, self.config, self.subscription, route)


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
