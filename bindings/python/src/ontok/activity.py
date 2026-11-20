"""Work whose admitted inputs determine defined outcomes."""

from pydantic import BaseModel, RootModel

from .outcome import Outcome
from .purpose import Purpose


class ActivityCase[Inputs, Results: Outcome | Purpose](BaseModel):
    """A whole admissible relationship: never mix inputs and outcomes of separate cases."""

    inputs: Inputs
    outcomes: Results


class Activity[Case: ActivityCase](RootModel[Case]):
    """Narrow to a union of complete ActivityCase models to declare alternatives."""
