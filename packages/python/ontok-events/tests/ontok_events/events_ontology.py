"""A test-owned ontology: one kind of occurrence, enough to construct the module's claims."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from ontok.core import Event, Instant, NodeId, Timestamp


class Kind(StrEnum):
    PLACED = "shop-OrderPlaced"


class OrderPlaced(Event):
    event_type: Literal[Kind.PLACED]
    order: NodeId

    @property
    def about(self) -> NodeId:
        return self.order


def identifier(n: int) -> NodeId:
    return NodeId(f"0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a{n:02x}")


def placed() -> OrderPlaced:
    return OrderPlaced(
        id=identifier(1),
        occurred=Instant(at=Timestamp(datetime.now(UTC))),
        event_type=Kind.PLACED,
        order=identifier(9),
    )
