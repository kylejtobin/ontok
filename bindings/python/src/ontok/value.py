"""Typed assessments of organizational value and its eight dimensions.

The generic classes are authoring templates. Concrete domain models close their
parameters, including the subject, basis, and evidence for each assessment.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .scalars import MODEL_CONFIG
from .work import Activity, Outcome, Purpose, Requirement


class Need[Holder, RequiredState](BaseModel, frozen=True):
    """A required condition or state belonging to a holder."""

    model_config = MODEL_CONFIG
    holder: Holder
    required: RequiredState


class Interest[Holder, Concern](BaseModel, frozen=True):
    """A holder's concern or stake in a typed subject."""

    model_config = MODEL_CONFIG
    holder: Holder
    concern: Concern


type ValueBasis = Need[object, object] | Interest[object, object] | Purpose


class Benefit[Detail](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["benefit"] = "benefit"
    detail: Detail


class Harm[Detail](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["harm"] = "harm"
    detail: Detail


class Unchanged[Detail](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["unchanged"] = "unchanged"
    detail: Detail


type Assessment[Detail] = Annotated[
    Benefit[Detail] | Harm[Detail] | Unchanged[Detail],
    Field(discriminator="kind"),
]


class Value[Subject, Basis: ValueBasis, ValueAssessment: Assessment[object]](
    BaseModel, frozen=True
):
    """A subject's worth relative to a basis, through a typed assessment."""

    model_config = MODEL_CONFIG
    subject: Subject
    relative_to: Basis
    assessment: ValueAssessment


class FinancialChange[Extent](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["financial_change"] = "financial_change"
    operation: Literal[
        "earned", "saved", "preserved", "made_available", "spent", "lost", "made_unavailable"
    ]
    extent: Extent


class TimeChange[Extent](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["time_change"] = "time_change"
    operation: Literal["saved", "gained", "made_available", "consumed", "lost"]
    extent: Extent


class Fitness[End: Purpose, Attainment](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["fitness"] = "fitness"
    purpose: End
    attainment: Attainment


class Correctness[Required: Requirement[object, object], Conformity](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["correctness"] = "correctness"
    requirement: Required
    conformity: Conformity


class Reliability[Context, RequiredOutcome: Outcome[object], Observation](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["reliability"] = "reliability"
    context: Context
    required_outcome: RequiredOutcome
    observation: Observation


class LikelihoodChange[AdverseOutcome: Outcome[object], Extent](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["likelihood"] = "likelihood"
    adverse_outcome: AdverseOutcome
    direction: Literal["reduced", "increased"]
    extent: Extent


class ConsequenceChange[AdverseOutcome: Outcome[object], Extent](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["consequence"] = "consequence"
    adverse_outcome: AdverseOutcome
    direction: Literal["reduced", "increased"]
    extent: Extent


class ExposureChange[AdverseOutcome: Outcome[object], Basis](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["exposure"] = "exposure"
    adverse_outcome: AdverseOutcome
    operation: Literal["removed", "introduced"]
    basis: Basis


class AbilityChange[Work: Activity[object, object], Evidence](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["ability_change"] = "ability_change"
    activity: Work
    operation: Literal["gained", "strengthened", "weakened", "lost"]
    evidence: Evidence


class Satisfaction[Expectation, Assessment](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["satisfaction"] = "satisfaction"
    expectation: Expectation
    assessment: Assessment


class Wellbeing[Condition](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["wellbeing"] = "wellbeing"
    condition: Condition


class Safety[Threat, Protection](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["safety"] = "safety"
    threat: Threat
    protection: Protection


class Fulfillment[End: Purpose, Attainment](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["fulfillment"] = "fulfillment"
    purpose: End
    attainment: Attainment


class Trust[ExpectedConduct, Assessment](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["trust"] = "trust"
    expected_conduct: ExpectedConduct
    assessment: Assessment


class Loyalty[Commitment, Assessment](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["loyalty"] = "loyalty"
    commitment: Commitment
    assessment: Assessment


class Reputation[Audience, Standing](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["reputation"] = "reputation"
    audience: Audience
    standing: Standing


class RelationshipStrength[Assessment](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["relationship_strength"] = "relationship_strength"
    assessment: Assessment


class Availability[AccessibleExtent](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["availability"] = "availability"
    accessible: AccessibleExtent


class Preservation[RetainedCondition](BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["preservation"] = "preservation"
    retained: RetainedCondition


type EconomicDetail = FinancialChange[object]
type TimeDetail = TimeChange[object]
type QualityDetail = Annotated[
    Fitness[Purpose, object]
    | Correctness[Requirement[object, object], object]
    | Reliability[object, Outcome[object], object],
    Field(discriminator="kind"),
]
type RiskDetail = Annotated[
    LikelihoodChange[Outcome[object], object]
    | ConsequenceChange[Outcome[object], object]
    | ExposureChange[Outcome[object], object],
    Field(discriminator="kind"),
]
type CapabilityDetail = AbilityChange[Activity[object, object], object]
type WelfareDetail = Annotated[
    Satisfaction[object, object]
    | Wellbeing[object]
    | Safety[object, object]
    | Fulfillment[Purpose, object],
    Field(discriminator="kind"),
]
type RelationshipDetail = Annotated[
    Trust[object, object]
    | Loyalty[object, object]
    | Reputation[object, object]
    | RelationshipStrength[object],
    Field(discriminator="kind"),
]
type ResourceDetail = Annotated[
    Availability[object] | Preservation[object],
    Field(discriminator="kind"),
]


class Economic[Subject, Basis: ValueBasis, ValueAssessment: Assessment[EconomicDetail]](
    Value[Subject, Basis, ValueAssessment], frozen=True
):
    dimension: Literal["economic"] = "economic"


class Time[Subject, Basis: ValueBasis, ValueAssessment: Assessment[TimeDetail]](
    Value[Subject, Basis, ValueAssessment], frozen=True
):
    dimension: Literal["time"] = "time"


class Quality[Subject, Basis: ValueBasis, ValueAssessment: Assessment[QualityDetail]](
    Value[Subject, Basis, ValueAssessment], frozen=True
):
    dimension: Literal["quality"] = "quality"


class Risk[Subject, Basis: ValueBasis, ValueAssessment: Assessment[RiskDetail]](
    Value[Subject, Basis, ValueAssessment], frozen=True
):
    dimension: Literal["risk"] = "risk"


class Capability[Subject, Basis: ValueBasis, ValueAssessment: Assessment[CapabilityDetail]](
    Value[Subject, Basis, ValueAssessment], frozen=True
):
    dimension: Literal["capability"] = "capability"


class HumanWelfare[Subject, Basis: ValueBasis, ValueAssessment: Assessment[WelfareDetail]](
    Value[Subject, Basis, ValueAssessment], frozen=True
):
    dimension: Literal["human_welfare"] = "human_welfare"


class Relationships[Subject, Basis: ValueBasis, ValueAssessment: Assessment[RelationshipDetail]](
    Value[Subject, Basis, ValueAssessment], frozen=True
):
    dimension: Literal["relationships"] = "relationships"


class Resources[Subject, Basis: ValueBasis, ValueAssessment: Assessment[ResourceDetail]](
    Value[Subject, Basis, ValueAssessment], frozen=True
):
    dimension: Literal["resources"] = "resources"
