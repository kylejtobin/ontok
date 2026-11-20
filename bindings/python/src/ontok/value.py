"""Worth relative to a basis, expressed through independent dimensions."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .outcome import Outcome
from .purpose import Purpose
from .rule import Requirement
from .type import Interest, Need


class Benefit[Detail](BaseModel):
    direction: Literal["benefit"]
    detail: Detail


class Harm[Detail](BaseModel):
    direction: Literal["harm"]
    detail: Detail


class Unchanged[Detail](BaseModel):
    direction: Literal["unchanged"]
    detail: Detail


class Assessment[Detail](RootModel[Benefit[Detail] | Harm[Detail] | Unchanged[Detail]]):
    """Value direction is assessed relative to the enclosing Value's basis."""


class EconomicChange[Extent](BaseModel):
    dimension: Literal["economic"] = "economic"
    operation: Literal["earned", "saved", "preserved", "made_available", "lost", "spent"]
    extent: Extent


class TimeChange[Extent](BaseModel):
    dimension: Literal["time"] = "time"
    operation: Literal["saved", "gained", "made_available", "lost", "consumed"]
    extent: Extent


class QualityMeasure[End: Purpose, Obligation: Requirement, Evidence](BaseModel):
    """Fitness, correctness, or reliability relative to its stated reference."""

    dimension: Literal["quality"] = "quality"
    reference: End | Obligation | Outcome
    evidence: Evidence


class RiskMeasure[Adverse: Outcome, Exposure](BaseModel):
    dimension: Literal["risk"] = "risk"
    adverse: Adverse
    exposure: Exposure


class CapabilityMeasure[Work: Activity, Ability](BaseModel):
    dimension: Literal["capability"] = "capability"
    activity: Work
    ability: Ability


class WelfareMeasure[Evidence](BaseModel):
    dimension: Literal["human_welfare"] = "human_welfare"
    aspect: Literal["satisfaction", "wellbeing", "safety", "fulfillment"]
    evidence: Evidence


class RelationshipMeasure[Evidence](BaseModel):
    dimension: Literal["relationships"] = "relationships"
    aspect: Literal["trust", "loyalty", "reputation", "strength"]
    evidence: Evidence


class ResourceMeasure[Evidence](BaseModel):
    dimension: Literal["resources"] = "resources"
    aspect: Literal["availability", "preservation"]
    evidence: Evidence


class Value[Subject, Basis: Need | Interest | Purpose, Detail](BaseModel):
    """One subject, one basis, and one or more dimensional assessments."""

    subject: Subject
    relative_to: Basis
    dimensions: Annotated[tuple[Assessment[Detail], ...], Field(min_length=1)]


class Economic[Subject, Basis: Need | Interest | Purpose, Extent](
    Value[Subject, Basis, EconomicChange[Extent]]
):
    """Money earned, saved, preserved, or made available."""


class Time[Subject, Basis: Need | Interest | Purpose, Extent](
    Value[Subject, Basis, TimeChange[Extent]]
):
    """Time saved, gained, or made available."""


class Quality[Subject, Basis: Need | Interest | Purpose, End: Purpose, Obligation: Requirement, Evidence](
    Value[Subject, Basis, QualityMeasure[End, Obligation, Evidence]]
):
    """Fitness for purpose, correctness, and reliability."""


class Risk[Subject, Basis: Need | Interest | Purpose, Adverse: Outcome, Exposure](
    Value[Subject, Basis, RiskMeasure[Adverse, Exposure]]
):
    """Reduced exposure to uncertain adverse outcomes."""


class Capability[Subject, Basis: Need | Interest | Purpose, Work: Activity, Ability](
    Value[Subject, Basis, CapabilityMeasure[Work, Ability]]
):
    """Increased ability to accomplish something."""


class HumanWelfare[Subject, Basis: Need | Interest | Purpose, Evidence](
    Value[Subject, Basis, WelfareMeasure[Evidence]]
):
    """Satisfaction, wellbeing, safety, and fulfillment."""


class Relationships[Subject, Basis: Need | Interest | Purpose, Evidence](
    Value[Subject, Basis, RelationshipMeasure[Evidence]]
):
    """Trust, loyalty, reputation, and relationship strength."""


class Resources[Subject, Basis: Need | Interest | Purpose, Evidence](
    Value[Subject, Basis, ResourceMeasure[Evidence]]
):
    """Availability and preservation of scarce assets or materials."""
