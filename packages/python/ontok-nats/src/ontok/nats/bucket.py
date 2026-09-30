from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, RootModel, TypeAdapter

import nats.js.errors
from nats.aio.client import Client
from nats.js.api import KeyValueConfig, StorageType
from ontok.core import State
from ontok.events import (
    EnsureReadModel,
    FailureReason,
    LogSequence,
    ReadModelEnsured,
    ReadModelEnsuring,
    ReadModelReset,
    ReadModelResetting,
    ResetReadModel,
    StateStale,
    StateUnavailable,
    StateWriting,
    StateWritten,
    Unavailable,
    WriteState,
)
from ontok.nats.interpreter import INTERPRETER, STRICT, UNAVAILABLE

BUCKET_PREFIX = "READ_"


class Cell(BaseModel):
    """What a read model keeps at a key: an entity's condition and the sequence it is as of. It is
    serialized as the condition's own kind, not as `State`, so a refinement keeps its fields."""

    model_config = STRICT

    sequence: LogSequence
    state: State


class Kept(BaseModel):
    """A cell as the bucket returns it: its revision, and its value as text."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    revision: int
    value: bytes


class Advance(RootModel[int]):
    """How far a write moves a key forward; only a positive advance is one."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(gt=0)


class Newer(BaseModel):
    """The write is as of a later sequence than the cell it replaces."""

    model_config = STRICT

    advance: Advance
    revision: int


class Stale(BaseModel):
    """The cell is already as of this sequence or a later one."""

    model_config = STRICT

    recorded: LogSequence = Field(validation_alias=AliasPath("kept_sequence"))


Comparison = Annotated[Newer | Stale, Field(union_mode="left_to_right")]
ComparisonConstructor: TypeAdapter[Newer | Stale] = TypeAdapter(Comparison)


class Compared(BaseModel):
    """A write against the cell the bucket already keeps."""

    model_config = STRICT

    write: WriteState
    kept_sequence: LogSequence
    revision: int

    @property
    def advance(self) -> int:
        return self.write.sequence.root - self.kept_sequence.root

    @property
    def comparison(self) -> Comparison:
        return ComparisonConstructor.validate_python(self, from_attributes=True)


def bucket_of(work_type: str) -> str:
    return BUCKET_PREFIX + work_type.replace("-", "_")


class EnsureReadModelInterpreter(BaseModel):
    """Makes a projection's bucket exist: one value per key, kept on file."""

    model_config = INTERPRETER

    action: EnsureReadModel
    client: Client = Field(exclude=True, repr=False)

    async def execute(self) -> ReadModelEnsuring:
        try:
            await self.client.jetstream().create_key_value(  # pyright: ignore[reportUnknownMemberType]
                KeyValueConfig(
                    bucket=bucket_of(self.action.work_type.root),
                    history=1,
                    storage=StorageType.FILE,
                    direct=True,
                )
            )
        except (nats.js.errors.APIError, *UNAVAILABLE) as failure:
            return Unavailable(reason=FailureReason(repr(failure)))
        return ReadModelEnsured(work_type=self.action.work_type)


class ResetReadModelInterpreter(BaseModel):
    """Empties a projection's bucket by deleting it and making it exist again."""

    model_config = INTERPRETER

    action: ResetReadModel
    client: Client = Field(exclude=True, repr=False)

    async def execute(self) -> ReadModelResetting:
        bucket = bucket_of(self.action.work_type.root)
        try:
            await self.client.jetstream().delete_key_value(bucket)  # pyright: ignore[reportUnknownMemberType]
        except nats.js.errors.NotFoundError:
            pass
        except (nats.js.errors.APIError, *UNAVAILABLE) as failure:
            return Unavailable(reason=FailureReason(repr(failure)))
        try:
            await self.client.jetstream().create_key_value(  # pyright: ignore[reportUnknownMemberType]
                KeyValueConfig(bucket=bucket, history=1, storage=StorageType.FILE, direct=True)
            )
        except (nats.js.errors.APIError, *UNAVAILABLE) as failure:
            return Unavailable(reason=FailureReason(repr(failure)))
        return ReadModelReset(work_type=self.action.work_type)


class KeptSequence(BaseModel):
    """The sequence a kept cell is as of; the condition it keeps is not reconstructed here."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        extra="ignore",
    )

    sequence: LogSequence


class WriteStateInterpreter(BaseModel):
    """Records an entity's condition at its key when the write is newer than what is kept,
    through a compare-and-set on the key's revision."""

    model_config = INTERPRETER

    action: WriteState
    client: Client = Field(exclude=True, repr=False)

    async def execute(self) -> StateWriting:
        key = self.action.about.root
        value = Cell(sequence=self.action.sequence, state=self.action.state).model_dump_json(
            serialize_as_any=True
        )
        try:
            store = await self.client.jetstream().key_value(  # pyright: ignore[reportUnknownMemberType]
                bucket_of(self.action.work_type.root)
            )
            try:
                entry = await store.get(key)
            except nats.js.errors.KeyNotFoundError:
                await store.create(key, value.encode())
                return StateWritten(write=self.action)
            kept = Kept.model_validate(entry, from_attributes=True)
            compared = Compared(
                write=self.action,
                kept_sequence=KeptSequence.model_validate_json(kept.value).sequence,
                revision=kept.revision,
            )
            match compared.comparison:
                case Newer(revision=revision):
                    await store.update(key, value.encode(), last=revision)
                    return StateWritten(write=self.action)
                case Stale(recorded=recorded):
                    return StateStale(write=self.action, recorded=recorded)
        except (nats.js.errors.APIError, *UNAVAILABLE) as failure:
            return StateUnavailable(write=self.action, reason=FailureReason(repr(failure)))
