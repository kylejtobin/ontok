"""The bank's edges onto NATS: the delivered message as the Event it is, and the key-value
entry as the balance it holds."""

from typing import Annotated

from nats.aio.msg import Msg
from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import NodeId
from ontok.events import Event
from ontok.nats import DeliveredMessage, DeliveryRoute, Entry, Prior

from .account import Balance, NoBalance, Transaction, TransactionConstructor


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


class HeldBalance(BaseModel):
    """The entry the books hold for an account: the balance it is, and what a new balance is
    written against."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    entry: Entry = Field(validation_alias=AliasPath("reply"))

    @property
    def balance(self) -> Balance:
        return Balance.model_validate_json(self.entry.data)

    @property
    def prior(self) -> Prior:
        return self.entry


class NoHeldBalance(BaseModel):
    """Nothing on the books for an account: no balance, and what a first balance is written
    against."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    id: NodeId = Field(validation_alias=AliasPath("lookup", "action", "id"))
    prior: Prior = Field(validation_alias=AliasPath("prior"))

    @property
    def balance(self) -> NoBalance:
        return NoBalance(id=self.id)


BalanceRoute = Annotated[HeldBalance | NoHeldBalance, Field(union_mode="left_to_right")]
BalanceRouteConstructor: TypeAdapter[BalanceRoute] = TypeAdapter(BalanceRoute)
