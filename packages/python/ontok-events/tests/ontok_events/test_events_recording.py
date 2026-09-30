"""Durability is settled by the facts an answer and its readings carry, on each failure path."""

from ontok.events import (
    Absent,
    AlreadyPresent,
    Append,
    Appended,
    AppendUnavailable,
    ClaimRefusal,
    Conflict,
    Contested,
    Disposition,
    ExpectAny,
    FailureReason,
    LogSequence,
    NoLead,
    NotDurable,
    Readings,
    Retained,
    Settled,
    Unavailable,
    Unsettled,
    Written,
)

from .events_ontology import placed

REFUSED = ClaimRefusal("wrong last sequence: 42")


def batch() -> Append:
    return Append(expectation=ExpectAny(), events=(placed(),), disposition=Disposition.COMPLETE)


def test_a_contested_append_whose_address_holds_the_occurrence_is_already_present() -> None:
    existing = Retained(event=placed(), sequence=LogSequence(3))
    settled = Settled(
        answer=Contested(append=batch(), refusal=REFUSED), readings=Readings((existing,))
    )
    assert isinstance(settled.durability, AlreadyPresent)
    assert settled.durability.disposition is Disposition.COMPLETE


def test_a_contested_append_whose_address_is_empty_is_a_conflict() -> None:
    settled = Settled(
        answer=Contested(append=batch(), refusal=REFUSED),
        readings=Readings((Absent(about=placed().about),)),
    )
    assert isinstance(settled.durability, Conflict)
    assert settled.durability.disposition is Disposition.RETRY


def test_a_contested_append_whose_settling_read_failed_is_unsettled_not_a_conflict() -> None:
    settled = Settled(
        answer=Contested(append=batch(), refusal=REFUSED),
        readings=Readings((Unavailable(reason=FailureReason("timeout")),)),
    )
    assert isinstance(settled.durability, Unsettled)
    assert settled.durability.disposition is Disposition.RETRY


def test_an_append_the_provider_did_not_complete_is_not_durable() -> None:
    settled = Settled(
        answer=AppendUnavailable(append=batch(), reason=FailureReason("down")),
        readings=Readings(()),
    )
    assert isinstance(settled.durability, NotDurable)
    assert settled.durability.disposition is Disposition.RETRY


def test_a_written_append_of_nothing_carries_its_authors_disposition() -> None:
    rejected = Append(expectation=ExpectAny(), events=(), disposition=Disposition.REJECT)
    settled = Settled(answer=Written(append=rejected), readings=Readings(()))
    assert isinstance(settled.durability, Appended)
    assert settled.durability.disposition is Disposition.REJECT


def test_an_append_of_nothing_has_no_lead_and_settles_nothing() -> None:
    empty = Append(expectation=ExpectAny(), events=(), disposition=Disposition.COMPLETE)
    assert isinstance(empty.lead, NoLead)
    assert empty.reads == ()
