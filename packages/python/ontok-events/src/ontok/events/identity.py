from collections.abc import Callable
from uuid import NAMESPACE_OID, UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import NodeId
from ontok.events.delivery import Attempt
from ontok.events.position import Version


class StateIdentity(BaseModel):
    """The content that identifies a State: the Stream and the Version folded to."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )
    stream: NodeId = Field(description="The Stream the State is the fold of.")
    version: Version = Field(description="The Version the fold has reached.")


class DeliveryIdentity(BaseModel):
    """The content that identifies a Delivery: the Subscription, the Event, and the Attempt."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )
    subscription: NodeId = Field(description="The Subscription undertaking the Event.")
    event: NodeId = Field(description="The Event handed over.")
    attempt: Attempt = Field(description="Which delivery of this Event this is.")


Identity = StateIdentity | DeliveryIdentity
IdentityConstructor: TypeAdapter[Identity] = TypeAdapter(Identity)


class IdentityInterpreter(BaseModel):
    """The NodeId a determined fact has: a UUID version 8 derived from the rendering of
    its identifying content."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )
    action: Identity = Field(description="The content the identity is derived from.")
    uuid5: Callable[[UUID, str], UUID] = Field(
        exclude=True, repr=False, description="The standard library's uuid5."
    )

    def execute(self) -> NodeId:
        return NodeId(
            f"{UUID(int=self.uuid5(NAMESPACE_OID, self.action.model_dump_json()).int, version=8)}"
        )
