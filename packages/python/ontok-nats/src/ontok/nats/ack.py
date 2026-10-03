from pydantic import BaseModel, ConfigDict, Field

from nats.aio.client import Client
from ontok.core import PositiveDuration
from ontok.events import Ending, Outcome
from ontok.nats.consumer import Ack
from ontok.nats.stream import Subject


class AckReply(BaseModel):
    """An Ending as NATS receives it: which Ack, on the delivered message's reply subject."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    ending: Ending = Field(description="The Ending.")
    reply: Subject = Field(description="The reply subject of the delivered message.")

    @property
    def ack(self) -> Ack:
        return {Outcome.COMPLETE: Ack.ACK, Outcome.RETURNED: Ack.NAK, Outcome.PARKED: Ack.TERM}[
            self.ending.outcome
        ]


class AckConfirmation(BaseModel):
    """The server's reply to an Ack sent as a request: it took the acknowledgement."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )


class AckInterpreter(BaseModel):
    """An Ack sent as a request: the Ending is returned once the server's confirmation
    constructs."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
        arbitrary_types_allowed=True,
    )

    action: AckReply = Field(description="The Ack to send.")
    wait: PositiveDuration = Field(description="How long the Ack waits for its confirmation.")
    client: Client = Field(exclude=True, repr=False, description="The NATS connection.")

    async def execute(self) -> Ending:
        AckConfirmation.model_validate(
            await self.client.request(
                self.action.reply.root,
                self.action.ack.value.encode(),
                timeout=self.wait.root.total_seconds(),
            ),
            from_attributes=True,
        )
        return self.action.ending
