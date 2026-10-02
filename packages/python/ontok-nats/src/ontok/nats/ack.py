from pydantic import BaseModel, ConfigDict, Field

from ontok.events import End, Ending
from ontok.nats.consumer import Ack
from ontok.nats.stream import Subject


class AckReply(BaseModel):
    """The reply sent for an Ending: which Ack, on the delivered message's reply subject."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    ending: Ending = Field(description="The Delivery to end, and how.")
    reply: Subject = Field(description="The reply subject of the delivered message.")

    @property
    def ack(self) -> Ack:
        return {End.ACKNOWLEDGE: Ack.ACK, End.REJECT: Ack.NAK, End.PARK: Ack.TERM}[self.ending.end]
