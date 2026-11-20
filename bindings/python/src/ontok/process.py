"""Composition of activities and their dependencies toward one Purpose."""

from typing import Annotated

from pydantic import BaseModel, Field, RootModel

from .activity import Activity, ActivityCase
from .purpose import Purpose


class Sequence(RootModel[Annotated[tuple[Activity, ...], Field(min_length=2)]]):
    """Activities whose order establishes sequential dependencies."""


class Concurrent(RootModel[Annotated[tuple[Activity, ...], Field(min_length=2)]]):
    """Activities whose composition does not impose a sequential dependency."""


class ProcessWork[Arrangement: Sequence | Concurrent | Activity](RootModel[Arrangement]):
    """A work arrangement, which may be narrowed to a nested arrangement."""


class Process[Work: ProcessWork, End: Purpose](Activity[ActivityCase[Work, End]]):
    """Specialized Activity: composition as inputs, single Purpose as outcome."""
