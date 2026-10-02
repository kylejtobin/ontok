from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

from ontok.events import Events, Version
from ontok.nats.stream import Sequence


class ExpectAt(BaseModel):
    """An Append asserting its Stream is at a Version, with the Events there: the last is the
    sequence expected."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    version: Version = Field(
        validation_alias=AliasPath("append", "expected", "version"),
        description="The Version asserted.",
    )
    events: Events = Field(
        validation_alias=AliasPath("prior"), description="The Events the Stream holds."
    )

    @property
    def sequence(self) -> Sequence:
        return Sequence(max(event.position.root for event in self.events.root))


class ExpectNone(BaseModel):
    """An Append asserting its Stream does not exist: its subject is expected at sequence 0."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["no_stream"] = Field(
        validation_alias=AliasPath("append", "expected", "value"), description="The assertion."
    )

    @property
    def sequence(self) -> Literal[0]:
        return 0


class ExpectAny(BaseModel):
    """An Append asserting nothing of its Stream: no sequence is expected."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    value: Literal["any"] = Field(
        validation_alias=AliasPath("append", "expected", "value"), description="The assertion."
    )


Expect = ExpectAt | ExpectNone | ExpectAny
ExpectConstructor: TypeAdapter[Expect] = TypeAdapter(Expect)
