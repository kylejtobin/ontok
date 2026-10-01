from enum import StrEnum

from pydantic import ConfigDict, Field, RootModel


class ConsumerName(RootModel[str]):
    """The name of a consumer: no whitespace, period, asterisk, greater-than, or slash."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(pattern=r"^[^\s.*>/\\]+$")


class ConsumerSequence(RootModel[int]):
    """The sequence number a consumer assigns to a delivery. The first delivery is 1."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class NumDelivered(RootModel[int]):
    """How many times a message has been delivered to a consumer."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class NumPending(RootModel[int]):
    """How many messages remain for a consumer after this one."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=0)


class MaxDeliver(RootModel[int]):
    """The most times a message is delivered to a consumer."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: int = Field(ge=1)


class DeliverPolicy(StrEnum):
    """Where a consumer begins in the stream."""

    ALL = "all"
    LAST = "last"
    NEW = "new"
    BY_START_SEQUENCE = "by_start_sequence"
    BY_START_TIME = "by_start_time"
    LAST_PER_SUBJECT = "last_per_subject"


class AckPolicy(StrEnum):
    """How a consumer requires messages to be acknowledged."""

    NONE = "none"
    ALL = "all"
    EXPLICIT = "explicit"


class Ack(StrEnum):
    """The reply a consumer sends on a delivered message's reply subject."""

    ACK = "+ACK"
    NAK = "-NAK"
    TERM = "+TERM"
