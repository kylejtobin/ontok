"""Activities composed toward a Purpose, specializing Activity."""

from typing import Annotated

from pydantic import Field, RootModel

from .activity import Activity, ActivityCase
from .purpose import Purpose


class Activities[Members: tuple](RootModel[Members]):
    """Joint Activity positions; alternatives can occupy individual positions."""

    root: Annotated[Members, Field(min_length=1)]


class Process[Work: Activities, End: Purpose](Activity[ActivityCase[Work, End]]):
    """Its Activity composition is its input and its Purpose its sole result."""
