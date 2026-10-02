from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ontok.core import PositiveDuration
from ontok.nats.connection import ServerUrl, User
from ontok.nats.consumer import MaxDeliver
from ontok.nats.kv import Bucket
from ontok.nats.stream import StreamName


class NatsConfig(BaseSettings):
    """How this program reaches NATS: the server, who it is, the stream and bucket it uses, and
    how its consumers acknowledge."""

    model_config = SettingsConfigDict(
        frozen=True,
        extra="forbid",
        strict=False,
        validate_default=True,
        revalidate_instances="never",
        env_prefix="NATS_",
    )
    url: ServerUrl = Field(description="The server.")
    user: User = Field(description="The user the connection authenticates as.")
    credentials: SecretStr = Field(description="The user's password.")
    stream: StreamName = Field(description="The stream that holds the organization's events.")
    bucket: Bucket = Field(description="The bucket that holds the organization's read models.")
    ack_wait: PositiveDuration = Field(description="How long a delivery waits for its Ack.")
    max_deliver: MaxDeliver = Field(description="The most times an Event is delivered.")
    reply_wait: PositiveDuration = Field(description="How long a request waits for its reply.")
