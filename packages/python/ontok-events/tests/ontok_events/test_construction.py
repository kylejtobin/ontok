"""Every union variant in ontok-events comes back from JSON as itself, the version is the fold's
count, and identity is a function of content."""

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import TypeAdapter

from ontok.core import Goal, Instant, NodeId, Role, Timestamp
from ontok.events import (
    AppendOutcome,
    AppendOutcomeConstructor,
    AtFrontier,
    Attempt,
    AtVersion,
    DeliveryIdentity,
    Empty,
    Event,
    Events,
    Expectation,
    ExpectedVersion,
    FromPosition,
    Frontier,
    Identity,
    Initial,
    LookupOutcome,
    LookupOutcomeConstructor,
    NoReadModel,
    NoStream,
    Occurrence,
    Page,
    Position,
    Positioned,
    PositionedConstructor,
    Read,
    Reading,
    ReadingConstructor,
    ReadModel,
    ReadOutcome,
    ReadOutcomeConstructor,
    Returned,
    Start,
    StartingPoint,
    State,
    StateIdentity,
    Version,
    VersionMismatch,
)

STREAM = NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b01")
OTHER_STREAM = NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b02")
SUBSCRIPTION = NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b03")
TELLER = Role(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b04"))
BOOKS_BALANCED = Goal(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b05"))
NOON = Instant(at=Timestamp(datetime(2026, 10, 3, 12, 0, tzinfo=UTC)))

FIRST = Occurrence(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b11"), occurred=NOON)
SECOND = Occurrence(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b12"), occurred=NOON)
THIRD = Occurrence(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b13"), occurred=NOON)

EVENTS = Events(
    (
        Event(occurrence=FIRST, stream=STREAM, version=Version(1), position=Position(4)),
        Event(occurrence=SECOND, stream=STREAM, version=Version(2), position=Position(7)),
        Event(occurrence=THIRD, stream=STREAM, version=Version(3), position=Position(9)),
    )
)

OPENING = Initial(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b21"), stream=STREAM)
AFTER_FIRST = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b22"), prior=OPENING, event=EVENTS.root[0]
)
AFTER_SECOND = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b23"), prior=AFTER_FIRST, event=EVENTS.root[1]
)
AFTER_THIRD = State(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b24"), prior=AFTER_SECOND, event=EVENTS.root[2]
)

READ_AFTER_SEVEN = Page(after=FromPosition(position=Position(7)), events=(EVENTS.root[2],))
READ_AT_FRONTIER = Page(after=FromPosition(position=Position(9)), events=())
READ_OF_NOTHING = Page(after=Start.BEGINNING, events=())

ExpectedVersionConstructor: TypeAdapter[ExpectedVersion] = TypeAdapter(ExpectedVersion)
StartingPointConstructor: TypeAdapter[StartingPoint] = TypeAdapter(StartingPoint)
IdentityConstructor: TypeAdapter[Identity] = TypeAdapter(Identity)
FoldConstructor: TypeAdapter[Initial | State] = TypeAdapter(Initial | State)

VARIANTS: list[tuple[str, TypeAdapter[Any], Any]] = [
    ("expected version: at a version", ExpectedVersionConstructor, AtVersion(version=Version(3))),
    ("expected version: no stream", ExpectedVersionConstructor, Expectation.NO_STREAM),
    ("expected version: any", ExpectedVersionConstructor, Expectation.ANY),
    ("append outcome: position", AppendOutcomeConstructor, Position(9)),
    (
        "append outcome: mismatch at a version",
        AppendOutcomeConstructor,
        VersionMismatch(expected=AtVersion(version=Version(3))),
    ),
    (
        "append outcome: mismatch at no stream",
        AppendOutcomeConstructor,
        VersionMismatch(expected=Expectation.NO_STREAM),
    ),
    ("read outcome: events", ReadOutcomeConstructor, EVENTS),
    ("read outcome: frontier", ReadOutcomeConstructor, Frontier(position=Position(9))),
    ("read outcome: no stream", ReadOutcomeConstructor, NoStream()),
    (
        "lookup outcome: read model",
        LookupOutcomeConstructor,
        ReadModel(id=STREAM, stream=STREAM, position=Position(9)),
    ),
    ("lookup outcome: no read model", LookupOutcomeConstructor, NoReadModel(id=STREAM)),
    (
        "starting point: from a position",
        StartingPointConstructor,
        FromPosition(position=Position(7)),
    ),
    ("starting point: beginning", StartingPointConstructor, Start.BEGINNING),
    ("starting point: now", StartingPointConstructor, Start.NOW),
    (
        "identity: state",
        IdentityConstructor,
        StateIdentity(stream=STREAM, version=Version(3)),
    ),
    (
        "identity: delivery",
        IdentityConstructor,
        DeliveryIdentity(subscription=SUBSCRIPTION, event=FIRST.id, attempt=Attempt(1)),
    ),
    ("fold: initial", FoldConstructor, OPENING),
    ("fold: state", FoldConstructor, AFTER_THIRD),
    ("reading: returned", ReadingConstructor, READ_AFTER_SEVEN.reading),
    ("reading: at frontier", ReadingConstructor, READ_AT_FRONTIER.reading),
    ("reading: empty", ReadingConstructor, READ_OF_NOTHING.reading),
    ("positioned: returned", PositionedConstructor, READ_AFTER_SEVEN.reading),
    ("positioned: at frontier", PositionedConstructor, READ_AT_FRONTIER.reading),
]


@pytest.mark.parametrize(
    ("constructor", "variant"), [(c, v) for _, c, v in VARIANTS], ids=[n for n, _, _ in VARIANTS]
)
def test_every_union_variant_round_trips_through_json_as_itself(
    constructor: TypeAdapter[Any], variant: Any
) -> None:
    back = constructor.validate_json(constructor.dump_json(variant))
    assert type(back) is type(variant)
    assert back == variant


def test_a_read_round_trips_with_each_place_it_can_begin() -> None:
    after = Read(
        id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b31"),
        role=TELLER,
        goal=BOOKS_BALANCED,
        stream=STREAM,
        after=FromPosition(position=Position(7)),
    )
    whole = Read(
        id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1b32"),
        role=TELLER,
        goal=BOOKS_BALANCED,
        stream=STREAM,
        after=Start.BEGINNING,
    )
    assert Read.model_validate_json(after.model_dump_json()) == after
    assert Read.model_validate_json(whole.model_dump_json()) == whole


def test_the_three_readings_of_a_page_are_the_three_read_outcomes() -> None:
    returned: Reading = READ_AFTER_SEVEN.reading
    at_frontier: Reading = READ_AT_FRONTIER.reading
    empty: Reading = READ_OF_NOTHING.reading
    assert type(returned) is Returned
    assert type(at_frontier) is AtFrontier
    assert type(empty) is Empty
    outcomes: tuple[ReadOutcome, ...] = (
        READ_AFTER_SEVEN.outcome,
        READ_AT_FRONTIER.outcome,
        READ_OF_NOTHING.outcome,
    )
    assert outcomes == (Events((EVENTS.root[2],)), Frontier(position=Position(9)), NoStream())


def test_a_page_with_a_position_has_a_last_and_a_page_of_nothing_has_none() -> None:
    positioned: Positioned = PositionedConstructor.validate_python(
        READ_AFTER_SEVEN, from_attributes=True
    )
    assert positioned.last == Position(9)
    assert READ_AFTER_SEVEN.last == Position(9)
    assert READ_AT_FRONTIER.last == Position(9)
    with pytest.raises(ValueError, match="validation error"):
        _ = READ_OF_NOTHING.last


def test_each_read_outcome_names_its_events_and_the_positioned_ones_their_last() -> None:
    assert EVENTS.events == EVENTS.root
    assert EVENTS.last == Position(9)
    assert Frontier(position=Position(9)).events == ()
    assert Frontier(position=Position(9)).last == Position(9)
    assert NoStream().events == ()


def test_a_read_model_and_its_absence_both_say_where_a_read_begins() -> None:
    held: LookupOutcome = ReadModel(id=STREAM, stream=STREAM, position=Position(7))
    absent: LookupOutcome = NoReadModel(id=STREAM)
    assert held.after == FromPosition(position=Position(7))
    assert absent.after is Start.BEGINNING


def test_an_append_outcome_is_a_position_or_a_mismatch_and_nothing_else() -> None:
    landed: AppendOutcome = AppendOutcomeConstructor.validate_json("9")
    refused: AppendOutcome = AppendOutcomeConstructor.validate_json('{"expected": {"version": 3}}')
    assert landed == Position(9)
    assert refused == VersionMismatch(expected=AtVersion(version=Version(3)))
    with pytest.raises(ValueError, match="validation error"):
        AppendOutcomeConstructor.validate_json('{"expected": {"version": 3}, "actual": "any"}')


def test_the_version_is_the_folds_count() -> None:
    assert OPENING.version == Version(0)
    assert AFTER_FIRST.version == Version(1)
    assert AFTER_SECOND.version == Version(2)
    assert AFTER_THIRD.version == Version(3)
    assert AFTER_THIRD.version.root == len(EVENTS.root)


def test_equal_content_gives_equal_identity() -> None:
    assert (
        StateIdentity(stream=STREAM, version=Version(3)).id
        == StateIdentity(stream=STREAM, version=Version(3)).id
    )
    assert (
        DeliveryIdentity(subscription=SUBSCRIPTION, event=FIRST.id, attempt=Attempt(1)).id
        == DeliveryIdentity(subscription=SUBSCRIPTION, event=FIRST.id, attempt=Attempt(1)).id
    )


def test_different_content_gives_different_identity() -> None:
    identities = [
        StateIdentity(stream=STREAM, version=Version(3)).id,
        StateIdentity(stream=STREAM, version=Version(4)).id,
        StateIdentity(stream=OTHER_STREAM, version=Version(3)).id,
        DeliveryIdentity(subscription=SUBSCRIPTION, event=FIRST.id, attempt=Attempt(1)).id,
        DeliveryIdentity(subscription=SUBSCRIPTION, event=FIRST.id, attempt=Attempt(2)).id,
        DeliveryIdentity(subscription=SUBSCRIPTION, event=SECOND.id, attempt=Attempt(1)).id,
        DeliveryIdentity(subscription=STREAM, event=FIRST.id, attempt=Attempt(1)).id,
    ]
    assert len(set(identities)) == len(identities)


def test_a_derived_identity_is_a_version_eight_node_id() -> None:
    identity = StateIdentity(stream=STREAM, version=Version(3)).id
    assert NodeId.model_validate_json(identity.model_dump_json()) == identity
    assert identity.root[14] == "8"
