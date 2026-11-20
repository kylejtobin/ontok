"""A Process is an Activity whose inputs compose Activities toward a Purpose."""

from typing import Annotated, Union

from pydantic import Field, RootModel

from .activity import Activity, ActivityCase
from .purpose import Purpose


class Activities(RootModel[tuple[Union[Activity, "Activities"], ...]]):
    """Required Activity positions with nested composition, not execution order."""

    root: Annotated[
        tuple[Union[Activity, "Activities"], ...],
        Field(
            min_length=1,
            description=(
                "The Activities constituting the Process. Position alternatives and "
                "cardinalities may be narrowed; dependencies belong in Activity inputs."
            ),
        ),
    ]


class ProcessCase(ActivityCase[Activities, Purpose]):
    """An Activity case requiring composed Activities and producing a Purpose."""

    inputs: Activities = Field(
        description="The nonempty composition of Activities constituting this Process."
    )


class Process[Case: ProcessCase](Activity[Case]):
    """An Activity specialized to an admissible ProcessCase, without a second goal."""
