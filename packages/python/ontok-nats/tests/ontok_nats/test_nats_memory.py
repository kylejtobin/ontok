"""Memory behaves as the page states: claims, contests, settlement, and reads, on the server."""

import pytest
from nats.aio.client import Client

from ontok.core import Event
from ontok.events import (
    Absent,
    AlreadyPresent,
    Answer,
    Append,
    Appended,
    Conflict,
    Contested,
    Disposition,
    EventTypeName,
    EveryType,
    ExpectAny,
    Expectation,
    ExpectSequence,
    History,
    LogSequence,
    OfType,
    ReadHistory,
    ReadLatest,
    Retained,
    Settled,
    Written,
)
from ontok.nats import (
    EVENTS,
    AppendInterpreter,
    ReadHistoryInterpreter,
    ReadLatestInterpreter,
    SettleInterpreter,
)
from ontok.nats.subject import EntitySubject

from .nats_ontology import Kind, OccurrenceConstructor, fresh, paid, placed, shipped

pytestmark = pytest.mark.asyncio(loop_scope="session")


def append(*events: Event, expectation: Expectation = ExpectAny()) -> Append:  # noqa: B008
    return Append(expectation=expectation, events=events, disposition=Disposition.COMPLETE)


async def commit(client: Client, *events: Event, expectation: Expectation = ExpectAny()) -> Answer:  # noqa: B008
    return await AppendInterpreter(
        action=append(*events, expectation=expectation), client=client
    ).execute()


async def settle(client: Client, answer: Answer) -> Settled:
    return await SettleInterpreter(
        action=answer, client=client, constructor=OccurrenceConstructor.validate_json
    ).execute()


async def test_the_deployed_stream_conforms_to_the_specification(admin: Client) -> None:
    info = await admin.jetstream().stream_info("EVENTS")  # pyright: ignore[reportUnknownMemberType]
    config = info.config
    assert (config.name, tuple(config.subjects or ()), config.storage, config.retention) == (
        EVENTS.name,
        EVENTS.subjects,
        EVENTS.storage,
        EVENTS.retention,
    )
    assert (config.deny_delete, config.deny_purge, config.allow_direct, config.allow_atomic) == (
        True,
        True,
        True,
        True,
    )


async def test_an_occurrence_lands_and_is_the_entitys_latest(program: Client) -> None:
    order = fresh()
    first = placed(order)
    answer = await commit(program, first)
    assert isinstance(answer, Written)
    latest = await ReadLatestInterpreter(
        action=ReadLatest(about=order, scope=EveryType()),
        client=program,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    assert isinstance(latest, Retained)
    assert latest.event == first


async def test_the_same_publication_after_another_landed_is_already_present(
    program: Client,
) -> None:
    order = fresh()
    first = placed(order)
    assert isinstance(await commit(program, first), Written)
    assert isinstance(await commit(program, paid(order)), Written)
    again = await commit(program, first)
    assert isinstance(again, Contested)
    settled = await settle(program, again)
    assert isinstance(settled.durability, AlreadyPresent)
    assert settled.durability.disposition is Disposition.COMPLETE


async def test_a_claim_on_a_sequence_the_entity_has_passed_is_a_conflict(program: Client) -> None:
    order = fresh()
    first = await commit(program, placed(order))
    assert isinstance(first, Written)
    latest = await ReadLatestInterpreter(
        action=ReadLatest(about=order, scope=EveryType()),
        client=program,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    assert isinstance(latest, Retained)
    assert isinstance(await commit(program, paid(order)), Written)
    stale = await commit(
        program,
        shipped(order, latest.event.id),
        expectation=ExpectSequence(sequence=latest.sequence),
    )
    assert isinstance(stale, Contested)
    settled = await settle(program, stale)
    assert isinstance(settled.durability, Conflict)
    assert settled.durability.disposition is Disposition.RETRY


async def test_a_batch_whose_claim_fails_lands_nothing(program: Client) -> None:
    order = fresh()
    first = placed(order)
    assert isinstance(await commit(program, first), Written)
    contested = await commit(
        program,
        shipped(order, fresh(), 0),
        shipped(order, fresh(), 1),
        expectation=ExpectSequence(sequence=LogSequence(1)),
    )
    assert isinstance(contested, Contested)
    history = await ReadHistoryInterpreter(
        action=ReadHistory(about=order),
        client=program,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    assert isinstance(history, History)
    assert [r.event.id for r in history.root] == [first.id]


async def test_a_batch_lands_whole_and_a_contested_batch_settles_from_its_lead(
    program: Client,
) -> None:
    order = fresh()
    trigger = placed(order)
    assert isinstance(await commit(program, trigger), Written)
    batch = (shipped(order, trigger.id, 0), shipped(order, trigger.id, 1))
    assert isinstance(await commit(program, *batch), Written)
    again = await commit(program, *batch)
    assert isinstance(again, Contested)
    settled = await settle(program, again)
    assert isinstance(settled.durability, AlreadyPresent)
    history = await ReadHistoryInterpreter(
        action=ReadHistory(about=order),
        client=program,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    assert isinstance(history, History)
    assert len(history.root) == 3


async def test_reads_by_kind_by_every_kind_by_address_and_absent(program: Client) -> None:
    order = fresh()
    first, second = placed(order), paid(order)
    assert isinstance(await commit(program, first), Written)
    assert isinstance(await commit(program, second), Written)
    read = ReadLatestInterpreter
    by_kind = await read(
        action=ReadLatest(about=order, scope=OfType(event_type=EventTypeName(Kind.PLACED))),
        client=program,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    every = await read(
        action=ReadLatest(about=order, scope=EveryType()),
        client=program,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    nothing = await read(
        action=ReadLatest(about=fresh(), scope=EveryType()),
        client=program,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    assert isinstance(by_kind, Retained) and by_kind.event == first
    assert isinstance(every, Retained) and every.event == second
    assert isinstance(nothing, Absent)


async def test_a_history_is_read_across_pages_in_order_and_nothing_twice(program: Client) -> None:
    order = fresh()
    events = [placed(order)] + [paid(order) for _ in range(6)]
    for event in events:
        assert isinstance(await commit(program, event), Written)
    history = await ReadHistoryInterpreter(
        action=ReadHistory(about=order),
        client=program,
        constructor=OccurrenceConstructor.validate_json,
    ).execute()
    assert isinstance(history, History)
    assert [r.event.id for r in history.root] == [e.id for e in events]
    assert [r.sequence.root for r in history.root] == sorted(r.sequence.root for r in history.root)


async def test_an_empty_append_is_written_without_a_call(program: Client) -> None:
    answer = await commit(program)
    assert isinstance(answer, Written)
    settled = await settle(program, answer)
    assert isinstance(settled.durability, Appended)


async def test_the_entity_subject_is_what_a_claim_checks() -> None:
    order = fresh()
    assert EntitySubject(about=order).text == f"event.{order.root}.>"
