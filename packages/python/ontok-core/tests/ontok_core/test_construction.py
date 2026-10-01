from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from ontok.core import (
    Connection,
    Context,
    Entity,
    Interval,
    NodeId,
    PositiveDuration,
    States,
    Timestamp,
)


class Customer(Entity):
    """A kind that adds a field Core does not declare."""

    owner: NodeId


def test_a_kind_adds_a_field_and_constructs() -> None:
    customer = Customer(
        id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2b"),
        owner=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2c"),
    )
    assert customer.owner == NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2c")


def test_an_undeclared_field_is_refused() -> None:
    with pytest.raises(ValidationError):
        Entity.model_validate_json('{"id": "0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2b", "name": "x"}')


def test_assignment_to_a_constructed_fact_is_refused() -> None:
    entity = Entity(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2b"))
    with pytest.raises(ValidationError):
        entity.id = NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2c")  # pyright: ignore[reportAttributeAccessIssue]


def test_a_node_id_that_is_not_a_canonical_uuid_is_refused() -> None:
    with pytest.raises(ValidationError):
        NodeId("not an identifier")


def test_a_node_id_of_another_version_is_refused() -> None:
    with pytest.raises(ValidationError):
        NodeId("0192a1b2-c3d4-4e5f-8a6b-7c8d9e0f1a2b")


def test_an_uppercase_node_id_is_refused() -> None:
    with pytest.raises(ValidationError):
        NodeId("0192A1B2-C3D4-7E5F-8A6B-7C8D9E0F1A2B")


def test_a_timestamp_without_a_timezone_is_refused() -> None:
    with pytest.raises(ValidationError):
        Timestamp(datetime(2026, 1, 1, 0, 0, 0))


def test_a_node_id_field_given_an_int_is_refused() -> None:
    with pytest.raises(ValidationError):
        Entity.model_validate_json('{"id": 5}')


def test_a_connection_given_a_node_as_an_endpoint_is_refused() -> None:
    with pytest.raises(ValidationError):
        Connection.model_validate_json(
            '{"source": {"id": "0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2b"},'
            ' "target": "0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2c"}'
        )


def test_an_interval_with_zero_duration_is_refused() -> None:
    with pytest.raises(ValidationError):
        Interval(
            begins_at=Timestamp(datetime(2026, 1, 1, tzinfo=UTC)),
            duration=PositiveDuration(timedelta(0)),
        )


def test_a_context_with_no_state_is_refused() -> None:
    with pytest.raises(ValidationError):
        Context(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2b"), state=States(()))
