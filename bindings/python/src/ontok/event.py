"""Assertions of occurrences, not independent evidence of their truth."""

from pydantic import BaseModel

from .type import CONFIG


class Event[Occurrence](BaseModel, frozen=True):
    """Work may depend on this assertion; no universal timestamp is required."""

    model_config = CONFIG
    occurred: Occurrence
