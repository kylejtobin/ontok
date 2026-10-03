"""The clerk's ruling on each delivery: which deliveries she parks, returns, and completes."""

from typing import Annotated, Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

from ontok.events import Outcome


class Review(BaseModel):
    """A withdrawal: the clerk parks it for review."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    kind: Literal["withdrawn"] = Field(validation_alias=AliasPath("occurrence", "kind"))

    @property
    def outcome(self) -> Outcome:
        return Outcome.PARKED


class Retry(BaseModel):
    """A deposit on its first delivery: the clerk's printer jams and returns it."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    kind: Literal["deposited"] = Field(validation_alias=AliasPath("occurrence", "kind"))
    attempt: Literal[1] = Field(validation_alias=AliasPath("attempt", "root"))

    @property
    def outcome(self) -> Outcome:
        return Outcome.RETURNED


class Done(BaseModel):
    """Any other delivery: the clerk completes it."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    @property
    def outcome(self) -> Outcome:
        return Outcome.COMPLETE


Ruling = Annotated[Review | Retry | Done, Field(union_mode="left_to_right")]
RulingConstructor: TypeAdapter[Ruling] = TypeAdapter(Ruling)
