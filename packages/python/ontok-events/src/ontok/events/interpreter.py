from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel

from ontok.core import NodeId, Timestamp
from ontok.events.delivery import EmittedIdentities, MintEmissionIdentities, ReadClock


class Uuid(RootModel[UUID]):
    """The standard library's identifier, as minted."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )


class ClockInterpreter(BaseModel):
    """Reads the present instant through the standard library's clock."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )

    action: ReadClock
    clock: type[datetime] = Field(exclude=True, repr=False)

    def execute(self) -> Timestamp:
        return Timestamp(self.clock.now(UTC))


class MintEmissionIdentitiesInterpreter(BaseModel):
    """Mints an identity for every emission position through the standard library's UUIDv7."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )

    action: MintEmissionIdentities
    mint: Callable[[], UUID] = Field(exclude=True, repr=False)

    def execute(self) -> EmittedIdentities:
        return EmittedIdentities(
            tuple(NodeId(Uuid(self.mint()).model_dump(mode="json")) for _ in range(1000))
        )
