from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ontok.core import NodeId


class BankConfig(BaseSettings):
    """Who the bank's standing subscriptions are: the clerk's and the bookkeeper's identities,
    the role they act in, and the goal they act toward."""

    model_config = SettingsConfigDict(
        frozen=True,
        extra="forbid",
        strict=False,
        validate_default=True,
        revalidate_instances="never",
        env_prefix="BANK_",
    )
    clerk: NodeId = Field(description="The clerk's subscription.")
    bookkeeper: NodeId = Field(description="The bookkeeper's subscription.")
    teller: NodeId = Field(description="The role both act in.")
    books_balanced: NodeId = Field(description="The goal both act toward.")
