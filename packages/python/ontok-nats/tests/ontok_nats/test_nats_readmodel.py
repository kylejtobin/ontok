"""A projection's read model behaves as the page states: a write lands when newer, is stale when
not, a reset empties it, and ensuring it twice is one bucket."""

import pytest
from nats.aio.client import Client

from ontok.core import State
from ontok.events import (
    EnsureReadModel,
    LogSequence,
    ReadModelEnsured,
    ReadModelReset,
    ResetReadModel,
    StateStale,
    StateWritten,
    WorkTypeName,
    WriteState,
)
from ontok.nats import EnsureReadModelInterpreter, ResetReadModelInterpreter, WriteStateInterpreter
from ontok.nats.bucket import Cell, bucket_of

from .nats_ontology import fresh

pytestmark = pytest.mark.asyncio(loop_scope="session")


class OrderCount(State):
    """How many orders an account has placed, as the projection sees it."""

    count: int


async def test_a_write_lands_when_newer_and_is_stale_when_not(
    program: Client, admin: Client
) -> None:
    work = WorkTypeName(f"shop-Count{fresh().root[-6:]}")
    ensured = await EnsureReadModelInterpreter(
        action=EnsureReadModel(work_type=work), client=program
    ).execute()
    assert isinstance(ensured, ReadModelEnsured)
    account = fresh()

    def write(sequence: int, count: int) -> WriteState:
        return WriteState(
            work_type=work,
            about=account,
            sequence=LogSequence(sequence),
            state=OrderCount(id=account, count=count),
        )

    first = await WriteStateInterpreter(action=write(5, 1), client=program).execute()
    assert isinstance(first, StateWritten)
    stale = await WriteStateInterpreter(action=write(3, 9), client=program).execute()
    assert isinstance(stale, StateStale)
    assert stale.recorded == LogSequence(5)
    newer = await WriteStateInterpreter(action=write(8, 2), client=program).execute()
    assert isinstance(newer, StateWritten)
    kept = await (await admin.jetstream().key_value(bucket_of(work.root))).get(account.root)  # pyright: ignore[reportUnknownMemberType]
    assert kept.value is not None
    assert Cell.model_validate_json(kept.value).sequence == LogSequence(8)


async def test_a_reset_empties_the_read_model_and_ensuring_twice_is_one_bucket(
    program: Client, admin: Client
) -> None:
    work = WorkTypeName(f"shop-Reset{fresh().root[-6:]}")
    for _ in range(2):
        ensured = await EnsureReadModelInterpreter(
            action=EnsureReadModel(work_type=work), client=program
        ).execute()
        assert isinstance(ensured, ReadModelEnsured)
    account = fresh()
    written = await WriteStateInterpreter(
        action=WriteState(
            work_type=work,
            about=account,
            sequence=LogSequence(1),
            state=OrderCount(id=account, count=1),
        ),
        client=program,
    ).execute()
    assert isinstance(written, StateWritten)
    reset = await ResetReadModelInterpreter(
        action=ResetReadModel(work_type=work), client=program
    ).execute()
    assert isinstance(reset, ReadModelReset)
    store = await admin.jetstream().key_value(bucket_of(work.root))  # pyright: ignore[reportUnknownMemberType]
    status = await store.status()
    assert status.values == 0
