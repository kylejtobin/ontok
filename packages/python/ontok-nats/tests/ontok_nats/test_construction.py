"""A delivered message constructs the Delivery it is, without a server."""

from datetime import UTC, datetime

from ontok.core import Goal, Instant, NodeId, Role, Timestamp
from ontok.events import (
    Attempt,
    Delivery,
    DeliveryIdentity,
    Event,
    Occurrence,
    Position,
    Start,
    Subscription,
    Version,
)
from ontok.nats import ConsumerDelivery, DeliveredMessage, DeliveryRoute

STREAM = NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1c01")
OCCURRENCE = Occurrence(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1c02"),
    occurred=Instant(at=Timestamp(datetime(2026, 10, 3, 12, 0, tzinfo=UTC))),
)
SUBSCRIPTION = Subscription(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1c03"),
    role=Role(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1c04")),
    goal=Goal(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1c05")),
    begins=Start.BEGINNING,
)
OTHER_SUBSCRIPTION = Subscription(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1c06"),
    role=SUBSCRIPTION.role,
    goal=SUBSCRIPTION.goal,
    begins=Start.BEGINNING,
)
EVENT = Event(occurrence=OCCURRENCE, stream=STREAM, version=Version(3), position=Position(41))


def delivered(num_delivered: int) -> DeliveryRoute:
    return DeliveryRoute(
        message=DeliveredMessage.model_validate(
            {
                "reply": "$JS.ACK.EVENTS.consumer.2.41.7.1790000000000000000.0",
                "headers": {"Ontok-Stream": STREAM.root, "Ontok-Version": "3"},
                "metadata": {"sequence": {"stream": 41}, "num_delivered": num_delivered},
                "data": OCCURRENCE.model_dump_json().encode(),
            }
        )
    )


def test_the_route_exposes_the_event_and_the_attempt() -> None:
    route = delivered(2)
    assert route.event == EVENT
    assert route.attempt == Attempt(2)


def test_a_consumer_delivery_derives_the_delivery() -> None:
    delivery = ConsumerDelivery(route=delivered(2), subscription=SUBSCRIPTION).delivery
    assert delivery == Delivery(
        id=DeliveryIdentity(
            subscription=SUBSCRIPTION.id, event=OCCURRENCE.id, attempt=Attempt(2)
        ).id,
        action=SUBSCRIPTION,
        event=EVENT,
        attempt=Attempt(2),
    )


def test_the_same_message_to_the_same_subscription_is_the_same_delivery() -> None:
    assert (
        ConsumerDelivery(route=delivered(1), subscription=SUBSCRIPTION).delivery
        == ConsumerDelivery(route=delivered(1), subscription=SUBSCRIPTION).delivery
    )


def test_another_attempt_or_another_subscription_is_another_delivery() -> None:
    first = ConsumerDelivery(route=delivered(1), subscription=SUBSCRIPTION).delivery
    again = ConsumerDelivery(route=delivered(2), subscription=SUBSCRIPTION).delivery
    elsewhere = ConsumerDelivery(route=delivered(1), subscription=OTHER_SUBSCRIPTION).delivery
    assert len({first.id.root, again.id.root, elsewhere.id.root}) == 3
    assert first.event == again.event == elsewhere.event
