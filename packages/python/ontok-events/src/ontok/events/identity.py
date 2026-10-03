from uuid import NAMESPACE_OID, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ontok.core import NodeId
from ontok.events.delivery import Attempt
from ontok.events.position import Version


class StateIdentity(BaseModel):
    """The content that identifies a fold step: its Stream and the Version it reached."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: NodeId = Field(description="The Stream the step is the fold of.")
    version: Version = Field(description="The Version the fold reached.")

    @property
    def id(self) -> NodeId:
        return NodeId(f"{UUID(int=uuid5(NAMESPACE_OID, self.model_dump_json()).int, version=8)}")


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

    @property
    def id(self) -> NodeId:
        return NodeId(f"{UUID(int=uuid5(NAMESPACE_OID, self.model_dump_json()).int, version=8)}")


Identity = StateIdentity | DeliveryIdentity
IdentityConstructor: TypeAdapter[Identity] = TypeAdapter(Identity)
