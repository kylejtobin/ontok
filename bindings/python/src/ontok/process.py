"""An Activity specializing inputs to composed activities and results to a Purpose."""

from typing import Annotated

from pydantic import Field, RootModel

from .activity import Activity
from .purpose import Purpose


class ActivityAlternative(RootModel[Activity]):
    """One Activity chosen from alternatives admitted by a narrowing."""

    root: Activity = Field(
        description="The admitted Activity selected at this composition position."
    )


class Activities(RootModel[tuple[Activity | ActivityAlternative, ...]]):
    """Jointly required Activity positions, not an independent execution order."""

    root: Annotated[
        tuple[Activity | ActivityAlternative, ...],
        Field(
            min_length=1,
            description=(
                "One or more required Activity positions; a position may select "
                "an alternative. Work dependencies are expressed by Activity inputs."
            ),
        ),
    ]


class Process(Activity[Activities]):
    """Composed work accomplishing its Purpose, which is stated only as its result."""

    inputs: Activities = Field(
        description="The composition of Activities constituting the Process."
    )
    outcomes: Purpose = Field(
        description="The single Purpose achieved by this Process, not an additional goal."
    )
