from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ontok.nats.error import ApiError
from ontok.nats.stream import Sequence, StreamName


class PubAck(BaseModel):
    """The acknowledgement of a publish: the stream and the sequence the message landed at."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    stream: StreamName = Field(description="The stream the message landed in.")
    seq: Sequence = Field(description="The sequence the message landed at.")


PublishReply = PubAck | ApiError
PublishReplyConstructor: TypeAdapter[PublishReply] = TypeAdapter(PublishReply)
