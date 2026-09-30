from pydantic import ConfigDict, Field, RootModel

from ontok.core.state import State
from ontok.core.structure import Node


class States(RootModel[tuple[State, ...]]):
    """The conditions that constitute a situation."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: tuple[State, ...] = Field(min_length=1)


class Context(Node):
    """A situation."""

    state: States = Field(description="The conditions that hold in this situation.")
