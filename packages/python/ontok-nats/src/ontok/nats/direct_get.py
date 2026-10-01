from enum import StrEnum


class Status(StrEnum):
    """The status header on a direct get reply that carries no message."""

    END_OF_BATCH = "204"
    NO_MESSAGES = "404"
