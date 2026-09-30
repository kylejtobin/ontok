from pydantic import BaseModel, ConfigDict

from ontok.core import NodeId, State
from ontok.events.type import FailureReason, LogSequence, WorkTypeName
from ontok.events.value import Unavailable


class EnsureReadModel(BaseModel):
    """The effect of making a projection's read model exist, idempotently."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work_type: WorkTypeName


class ResetReadModel(BaseModel):
    """The effect of emptying a projection's read model so replay rebuilds it."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work_type: WorkTypeName


class WriteState(BaseModel):
    """The effect of recording an entity's condition as of a sequence in a projection's read
    model; it applies only when that sequence is newer than the one recorded."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work_type: WorkTypeName
    about: NodeId
    sequence: LogSequence
    state: State


class ReadModelEnsured(BaseModel):
    """The read model exists."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work_type: WorkTypeName


class ReadModelReset(BaseModel):
    """The read model is empty."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work_type: WorkTypeName


class StateWritten(BaseModel):
    """The entity's condition as of the sequence is recorded."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    write: WriteState


class StateStale(BaseModel):
    """The read model already records this entity as of a later sequence; nothing changed, and
    that is success."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    write: WriteState
    recorded: LogSequence


class StateUnavailable(BaseModel):
    """The read model did not complete the write."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    write: WriteState
    reason: FailureReason


ReadModelEnsuring = ReadModelEnsured | Unavailable
ReadModelResetting = ReadModelReset | Unavailable
StateWriting = StateWritten | StateStale | StateUnavailable
