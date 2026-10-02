from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

from ontok.events import Position
from ontok.nats.consumer import DeliverPolicy
from ontok.nats.stream import Sequence


class BeginAfter(BaseModel):
    """A Subscription beginning after a Position: the consumer starts at the next sequence."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    position: Position = Field(
        validation_alias=AliasPath("begins", "position"), description="The Position begun after."
    )

    @property
    def deliver_policy(self) -> DeliverPolicy:
        return DeliverPolicy.BY_START_SEQUENCE

    @property
    def opt_start_seq(self) -> Sequence:
        return Sequence(self.position.root + 1)


class BeginAll(BaseModel):
    """A Subscription beginning at the beginning: the consumer delivers all."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["beginning"] = Field(
        validation_alias=AliasPath("begins", "value"), description="Where it begins."
    )

    @property
    def deliver_policy(self) -> DeliverPolicy:
        return DeliverPolicy.ALL


class BeginNew(BaseModel):
    """A Subscription beginning now: the consumer delivers only what is new."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["now"] = Field(
        validation_alias=AliasPath("begins", "value"), description="Where it begins."
    )

    @property
    def deliver_policy(self) -> DeliverPolicy:
        return DeliverPolicy.NEW


Begin = BeginAfter | BeginAll | BeginNew
BeginConstructor: TypeAdapter[Begin] = TypeAdapter(Begin)
