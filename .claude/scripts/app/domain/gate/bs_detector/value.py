"""The bs_detector context's value layer: a source position, the one identity-free composition every
violation reports as its location. It composes the grammar's own `Line` and `Column` leaves, imported
from the foreign model that already proves them."""

from pydantic import BaseModel, ConfigDict

from app.domain.foreign.ast import Column, Line


class Location(BaseModel):
    """A position in a source file: the line and column a violation sits at. Equal by value, no identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    line: Line
    column: Column
