"""Compositions of desired Outcomes."""

from typing import Annotated

from pydantic import Field, RootModel

from .outcome import Outcome


class Together[Positions: tuple](RootModel[Positions]):
    """Jointly required positions, not an ordering of their realization."""

    root: Annotated[Positions, Field(min_length=2)]


class Alternative[Selection: Outcome](RootModel[Selection]):
    """One permitted Outcome chosen from alternatives in the declaration."""


class Group[Members: tuple](RootModel[Members]):
    """Nested group whose cardinality may be narrowed by a domain."""

    root: Annotated[Members, Field(min_length=1)]


class Purpose[End: Outcome | Together | Alternative | Group](RootModel[End]):
    """An intended end stated solely through its Outcome composition."""
