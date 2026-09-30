from datetime import timedelta

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel


class Timestamp(RootModel[AwareDatetime]):
    """A timezone-qualified point on the timeline."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: AwareDatetime


class PositiveDuration(RootModel[timedelta]):
    """A strictly positive length of elapsed time."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: timedelta = Field(gt=timedelta(0))


class Instant(BaseModel):
    """A temporal extent occupying one point on the timeline."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    at: Timestamp


class Interval(BaseModel):
    """A temporal extent beginning at one point and continuing for positive time."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    begins_at: Timestamp
    duration: PositiveDuration


TemporalExtent = Instant | Interval
