"""Intended organizational ends expressed as compositions of Outcomes."""

from typing import Annotated

from pydantic import Field, RootModel

from .outcome import Outcome
from .type import State


class Purpose(RootModel[Annotated[tuple[Outcome[State[object]], ...], Field(min_length=1)]], frozen=True):
    """A nonempty composition; narrow root to an exact tuple and unions of Outcomes."""
