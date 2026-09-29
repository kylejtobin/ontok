from typing import Self

from platformdirs import user_data_dir
from pydantic import Field, RootModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataDirectory(RootModel[str], frozen=True):
    """The directory in which ONTOK EX stores durable runtime data."""

    root: str = Field(min_length=1)

    @classmethod
    def platform_default(cls) -> Self:
        return cls(user_data_dir("ontok-ex", appauthor=False))


class ExecutionConfig(BaseSettings):
    """The environment from which ONTOK EX obtains its data directory."""

    model_config = SettingsConfigDict(
        frozen=True,
        extra="forbid",
        env_prefix="ONTOK_EX_",
        enable_decoding=False,
    )

    data_directory: DataDirectory = Field(
        default_factory=DataDirectory.platform_default,
        description="The directory in which ONTOK EX stores durable runtime data.",
    )
