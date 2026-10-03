"""An account at the bank: its transactions, its balance on the books, and its statement."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, TypeAdapter

from ontok.core import NodeId
from ontok.events import NoReadModel, Occurrence, Page, ReadModel


class Amount(RootModel[Decimal]):
    """A sum of money."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: Decimal = Field(decimal_places=2)


class Deposited(Occurrence):
    """Money came into an account."""

    kind: Literal["deposited"] = Field(default="deposited", description="Which transaction.")
    amount: Amount = Field(description="How much.")

    @property
    def signed(self) -> Amount:
        return Amount(self.amount.root)


class Withdrawn(Occurrence):
    """Money left an account."""

    kind: Literal["withdrawn"] = Field(default="withdrawn", description="Which transaction.")
    amount: Amount = Field(description="How much.")

    @property
    def signed(self) -> Amount:
        return Amount(-self.amount.root)


Transaction = Deposited | Withdrawn
TransactionConstructor: TypeAdapter[Transaction] = TypeAdapter(Transaction)


class Balance(ReadModel):
    """What an account holds, as of a position."""

    amount: Amount = Field(description="What it holds.")


class NoBalance(NoReadModel):
    """An account with no balance on the books: it holds nothing, as of nothing."""

    @property
    def stream(self) -> NodeId:
        return self.id

    @property
    def amount(self) -> Amount:
        return Amount(Decimal(0))


class Statement(BaseModel):
    """An account's balance on the books and the page of its transactions since: its balance
    as of the page."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    held: Balance | NoBalance = Field(description="The balance on the books.")
    page: Page = Field(description="The transactions since.")

    @property
    def balance(self) -> Balance:
        return Balance(
            id=self.held.stream,
            stream=self.held.stream,
            position=self.page.last,
            amount=Amount(
                self.held.amount.root
                + sum(
                    (
                        TransactionConstructor.validate_python(event.occurrence).signed.root
                        for event in self.page.events
                    ),
                    Decimal(0),
                )
            ),
        )
