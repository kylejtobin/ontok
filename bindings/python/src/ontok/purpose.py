"""Compositions of intended outcomes without independent goals."""

from typing import Annotated, Union

from pydantic import Field, RootModel

from .outcome import Outcome


class Outcomes(RootModel[tuple[Union[Outcome, "Outcomes", "Alternative"], ...]]):
    """Jointly required outcome positions, which may themselves contain compositions."""

    root: Annotated[
        tuple[Union[Outcome, "Outcomes", "Alternative"], ...],
        Field(
            min_length=1,
            description=(
                "One or more jointly required positions. Nested compositions and "
                "alternatives occupy positions; cardinality is narrowed by the domain."
            ),
        ),
    ]


class Alternative(RootModel[Outcome | Outcomes]):
    """One selected position from the alternatives permitted by a narrowing."""

    root: Outcome | Outcomes = Field(
        description="The selected Outcome or composition; permissible choices belong to the declaration."
    )


class Purpose(RootModel[Outcome | Outcomes | Alternative]):
    """An intended organizational end expressed entirely by desired outcomes."""

    root: Outcome | Outcomes | Alternative = Field(
        description="The desired Outcome, required composition, or admitted alternative."
    )
