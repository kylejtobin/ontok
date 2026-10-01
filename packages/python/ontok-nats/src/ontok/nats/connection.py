from pydantic import ConfigDict, Field, NatsDsn, RootModel


class ServerUrl(RootModel[NatsDsn]):
    """The URL of a NATS server."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )


class Account(RootModel[str]):
    """The name of the account a connection is in."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[^\s.*>]+$")


class User(RootModel[str]):
    """The name of the user a connection authenticates as."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(min_length=1)
