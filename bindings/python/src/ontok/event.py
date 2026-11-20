"""Assertions of occurrences, not independent evidence that they happened."""

from pydantic import BaseModel


class Event[Occurrence](BaseModel):
    occurred: Occurrence
