from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import Event
from ontok.events.memory import ReadAddress, Readings, Retained
from ontok.events.type import ClaimRefusal, Disposition, FailureReason
from ontok.events.value import Absent, Address, AddressConstructor, Expectation, Unavailable


class Origination(BaseModel):
    """The effect of committing one originating occurrence to memory under a claim."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    event: Event
    expectation: Expectation

    @property
    def address(self) -> Address:
        return AddressConstructor.validate_python(self.event, from_attributes=True)

    @property
    def reads(self) -> tuple[ReadAddress, ...]:
        return (ReadAddress(address=self.address),)

    @property
    def disposition(self) -> Disposition:
        return Disposition.COMPLETE


class Lead(BaseModel):
    """The first occurrence of an append, whose address answers for the whole batch."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    event: Event = Field(validation_alias=AliasPath("events", 0))

    @property
    def address(self) -> Address:
        return AddressConstructor.validate_python(self.event, from_attributes=True)

    @property
    def reads(self) -> tuple[ReadAddress, ...]:
        return (ReadAddress(address=self.address),)


class NoLead(BaseModel):
    """An append of no occurrences has no lead and settles nothing."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    @property
    def reads(self) -> tuple[ReadAddress, ...]:
        return ()


Leading = Annotated[Lead | NoLead, Field(union_mode="left_to_right")]
LeadingConstructor: TypeAdapter[Lead | NoLead] = TypeAdapter(Leading)


class Append(BaseModel):
    """The effect of committing a response's emissions to memory atomically under one claim."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    expectation: Expectation
    events: tuple[Event, ...] = Field(max_length=1000)
    disposition: Disposition

    @property
    def lead(self) -> Leading:
        return LeadingConstructor.validate_python(self, from_attributes=True)

    @property
    def reads(self) -> tuple[ReadAddress, ...]:
        return self.lead.reads


AnyAppend = Origination | Append


class Written(BaseModel):
    """Memory's answer that every occurrence of the append landed."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    append: AnyAppend

    @property
    def reads(self) -> tuple[ReadAddress, ...]:
        return ()


class Contested(BaseModel):
    """Memory's answer that the append's claim did not hold, and its account of why."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    append: AnyAppend
    refusal: ClaimRefusal

    @property
    def reads(self) -> tuple[ReadAddress, ...]:
        return self.append.reads


class AppendUnavailable(BaseModel):
    """The provider did not complete the append."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    append: AnyAppend
    reason: FailureReason

    @property
    def reads(self) -> tuple[ReadAddress, ...]:
        return ()


Answer = Written | Contested | AppendUnavailable


class AlreadyPresent(BaseModel):
    """This publication was already remembered: the claim failed because it had already held."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    contested: Contested = Field(validation_alias=AliasPath("answer"))
    existing: Retained = Field(validation_alias=AliasPath("readings", "root", 0))

    @property
    def disposition(self) -> Disposition:
        return self.contested.append.disposition


class Conflict(BaseModel):
    """Another occurrence holds the position the claim required."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    contested: Contested = Field(validation_alias=AliasPath("answer"))
    absent: Absent = Field(validation_alias=AliasPath("readings", "root", 0))

    @property
    def disposition(self) -> Disposition:
        return Disposition.RETRY


class Unsettled(BaseModel):
    """The claim did not hold and the settling read was unavailable; nothing is known."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    contested: Contested = Field(validation_alias=AliasPath("answer"))
    unavailable: Unavailable = Field(validation_alias=AliasPath("readings", "root", 0))

    @property
    def disposition(self) -> Disposition:
        return Disposition.RETRY


class NotDurable(BaseModel):
    """The provider did not complete the append; nothing is known to be remembered."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    unavailable: AppendUnavailable = Field(validation_alias=AliasPath("answer"))

    @property
    def disposition(self) -> Disposition:
        return Disposition.RETRY


class Appended(BaseModel):
    """The occurrences were remembered."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    written: Written = Field(validation_alias=AliasPath("answer"))

    @property
    def disposition(self) -> Disposition:
        return self.written.append.disposition


Durability = Annotated[
    AlreadyPresent | Conflict | Unsettled | NotDurable | Appended,
    Field(union_mode="left_to_right"),
]
DurabilityConstructor: TypeAdapter[
    AlreadyPresent | Conflict | Unsettled | NotDurable | Appended
] = TypeAdapter(Durability)


class Settled(BaseModel):
    """An append's answer together with the readings that settle it."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    answer: Answer
    readings: Readings

    @property
    def durability(self) -> Durability:
        return DurabilityConstructor.validate_python(self, from_attributes=True)
