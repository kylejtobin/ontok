"""Scalar constraints and quantities used by the organizational definitions."""

from datetime import timedelta
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MODEL_CONFIG = ConfigDict(
    frozen=True,
    strict=True,
    extra="forbid",
    validate_default=True,
    revalidate_instances="always",
)
ROOT_CONFIG = ConfigDict(
    frozen=True,
    strict=True,
    validate_default=True,
    revalidate_instances="always",
)

type Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
type CurrencyCode = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z]{3}$")]
type NonnegativeDecimal = Annotated[Decimal, Field(ge=0, allow_inf_nan=False, strict=True)]
type Probability = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False, strict=True)]
type Duration = Annotated[timedelta, Field(ge=timedelta(0), strict=True)]
type Nonempty[T] = Annotated[tuple[T, ...], Field(min_length=1)]


class Money[Currency](BaseModel, frozen=True):
    """A monetary magnitude, rather than a signed account balance."""

    model_config = MODEL_CONFIG
    amount: NonnegativeDecimal
    currency: Currency


class Quantity[Unit](BaseModel, frozen=True):
    """A magnitude whose denomination is part of its type."""

    model_config = MODEL_CONFIG
    magnitude: NonnegativeDecimal
    unit: Unit
