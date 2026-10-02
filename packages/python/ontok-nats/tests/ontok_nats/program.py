"""The test program's edge: the route that constructs a Delivery from a delivered message, and
the clerk's ruling on how each delivery ends."""

from typing import Annotated, Literal

from nats.aio.msg import Msg
from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

from ontok.events import Event, Events, Outcome
from ontok.nats import DeliveredMessage, DeliveryRoute, Messages

from .world import Deposited, Withdrawn

Transaction = Deposited | Withdrawn
TransactionConstructor: TypeAdapter[Transaction] = TypeAdapter(Transaction)


class BankRoute(DeliveryRoute):
    """The bank's delivered message: the transaction it carries and the Event it is."""

    @classmethod
    def receive(cls, raw: Msg) -> "BankRoute":
        return cls(message=DeliveredMessage.model_validate(raw, from_attributes=True))

    @property
    def occurrence(self) -> Transaction:
        return TransactionConstructor.validate_json(self.message.payload.root)

    @property
    def event(self) -> Event:
        return Event(
            occurrence=self.occurrence,
            stream=self.stream,
            version=self.version,
            position=self.position,
        )


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


class Page(BaseModel):
    """The messages one pull delivered, as the Events they are."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    messages: Messages = Field(description="The messages.")

    @property
    def events(self) -> Events:
        return Events(tuple(BankRoute(message=m).event for m in self.messages.root))
