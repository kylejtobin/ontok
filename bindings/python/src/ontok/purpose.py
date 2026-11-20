"""Desired outcomes composed without a second independently stated goal."""

from typing import Annotated, Union

from pydantic import Field, RootModel

from .outcome import Outcome


class Outcomes(RootModel[tuple[Union[Outcome, "Outcomes"], ...]]):
    """Jointly required outcome positions; composition may be nested."""

    root: Annotated[
        tuple[Union[Outcome, "Outcomes"], ...],
        Field(
            min_length=1,
            description=(
                "The outcome positions required together; a domain may narrow each "
                "position to alternatives and constrain the cardinality of a nested group."
            ),
        ),
    ]


class Purpose[End: Outcome | Outcomes](RootModel[End]):
    """An intended organizational end expressed through desired Outcomes."""

    root: End = Field(
        description=(
            "A desired Outcome or composition; alternatives are modeled by narrowing "
            "this position to a union of complete admissible outcomes."
        )
    )
