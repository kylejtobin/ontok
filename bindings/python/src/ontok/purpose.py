"""Desired outcomes, jointly required or declared as alternatives."""

from typing import Annotated

from pydantic import Field, RootModel

from .outcome import Outcome


class Together(RootModel[Annotated[tuple[Outcome, ...], Field(min_length=2)]]):
    """Outcomes all required for the same intended end."""


class Alternative[Choice: Outcome](RootModel[Choice]):
    """Selects one outcome from alternatives declared in Choice."""


class Purpose[Composition: Outcome | Together | Alternative](RootModel[Composition]):
    """Intended organizational end; a concrete declaration fixes the composition."""
