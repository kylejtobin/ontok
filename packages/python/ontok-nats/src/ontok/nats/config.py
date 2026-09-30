from pydantic import ConfigDict, Field, RootModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class NatsUrl(RootModel[str]):
    """Where the server listens, as a NATS URL."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^(nats|tls)://\S+$")


class NatsSettings(BaseSettings):
    """The deployment's account of the server and the program identity that connects to it."""

    model_config = SettingsConfigDict(
        frozen=True,
        extra="forbid",
        strict=False,
        validate_default=True,
        revalidate_instances="never",
        env_prefix="ONTOK_NATS_",
    )

    url: NatsUrl
    user: SecretStr
    password: SecretStr
