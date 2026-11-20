"""Organized Activity compositions directed toward a single Purpose."""

from .activity import Activity
from .purpose import Purpose


class Process[Activities, End: Purpose](Activity[Activities, End], frozen=True):
    """Narrowing of Activity: prerequisites compose Activities; outcomes is the Purpose."""
