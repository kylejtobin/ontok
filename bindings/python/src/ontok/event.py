"""Assertions of occurrences, without inferring truth or requiring a timestamp."""

from pydantic import BaseModel


class Event[Occurrence](BaseModel):
    occurred: Occurrence
