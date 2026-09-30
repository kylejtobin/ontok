from pydantic import BaseModel, ConfigDict, Field, RootModel

from ontok.core import Action, PositiveDuration
from ontok.events.type import EventTypeName, FailureReason, WorkTypeName
from ontok.events.value import Unavailable


class Subscription(BaseModel):
    """A responsibility's standing interest in its occurrences, from the beginning of memory, and
    how long its work may take."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    work_type: WorkTypeName
    event_types: tuple[EventTypeName, ...] = Field(min_length=1)
    patience: PositiveDuration


class Responsibility(Action):
    """Declared work that responds to occurrences of these kinds, with its interchange identity."""

    work_type: WorkTypeName
    consumes: tuple[EventTypeName, ...] = Field(min_length=1)
    patience: PositiveDuration

    @property
    def event_types(self) -> tuple[EventTypeName, ...]:
        return self.consumes

    @property
    def subscription(self) -> Subscription:
        return Subscription(
            work_type=self.work_type, event_types=self.event_types, patience=self.patience
        )


class ConjunctionResponsibility(Action):
    """Declared work that responds when occurrences of two kinds have both happened to an entity."""

    work_type: WorkTypeName
    first: EventTypeName
    second: EventTypeName
    patience: PositiveDuration

    @property
    def event_types(self) -> tuple[EventTypeName, ...]:
        return (self.first, self.second)

    @property
    def subscription(self) -> Subscription:
        return Subscription(
            work_type=self.work_type, event_types=self.event_types, patience=self.patience
        )


class EnsureSubscription(BaseModel):
    """The effect of making a subscription exist, idempotently."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subscription: Subscription


class DeleteSubscription(BaseModel):
    """The effect of removing a subscription and its progress."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subscription: Subscription


class SubscriptionEnsured(BaseModel):
    """The subscription exists."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subscription: Subscription


class EnsureUnavailable(BaseModel):
    """The provider did not make the subscription exist."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subscription: Subscription
    reason: FailureReason


class SubscriptionDeleted(BaseModel):
    """The subscription and its progress are gone."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    subscription: Subscription


Ensured = SubscriptionEnsured | EnsureUnavailable
Deleted = SubscriptionDeleted | Unavailable


class StartupSubscriptions(RootModel[tuple[Ensured, ...]]):
    """Each responsibility's ensure outcome at startup, in declared order."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )
