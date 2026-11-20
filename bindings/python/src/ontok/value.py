"""Worth assessed relative to a need, interest, or purpose.

One subject and basis are shared by one or more dimension-specific assessments.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .outcome import Outcome
from .purpose import Purpose
from .rule import Requirement
from .type import Interest, Need, State


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
    """Benefit, harm, or no change relative to the enclosing Value's basis."""


class FinancialChange[Extent](BaseModel):
    change: Literal[
        "earned", "saved", "preserved", "made_available",
        "lost", "spent", "depleted", "made_unavailable",
    ]
    extent: Extent


class TemporalChange[Extent](BaseModel):
    change: Literal[
        "saved", "gained", "made_available", "lost", "spent", "made_unavailable"
    ]
    extent: Extent


class Fitness[Attainment](BaseModel):
    purpose: Purpose
    attainment: Attainment


class Correctness[Context, Target, Conformity](BaseModel):
    requirement: Requirement[Context, Target]
    conformity: Conformity


class Reliability[Context, Expected: Outcome, Observation](BaseModel):
    context: Context
    expected: Expected
    observation: Observation


class LikelihoodChange[Extent](BaseModel):
    direction: Literal["increased", "decreased"]
    extent: Extent


class ConsequenceChange[Extent](BaseModel):
    direction: Literal["increased", "decreased"]
    extent: Extent


class ExposureChange[Evidence](BaseModel):
    direction: Literal["introduced", "removed"]
    evidence: Evidence


class RiskDetail[
    Adverse: Outcome,
    Change: LikelihoodChange | ConsequenceChange | ExposureChange,
](BaseModel):
    adverse: Adverse
    change: Change


class CapabilityChange[Work: Activity, Evidence](BaseModel):
    activity: Work
    direction: Literal["increased", "decreased"]
    evidence: Evidence


class Satisfaction[Expectation, Appraisal](BaseModel):
    expectation: Expectation
    appraisal: Appraisal


class Wellbeing[Condition](BaseModel):
    condition: State[Condition]


class Safety[Threat, Protection](BaseModel):
    threat: Threat
    protection: Protection


class Fulfillment[Attainment](BaseModel):
    purpose: Purpose
    attainment: Attainment


class Trust[Conduct, Appraisal](BaseModel):
    expected_conduct: Conduct
    appraisal: Appraisal


class Loyalty[Commitment, Appraisal](BaseModel):
    commitment: Commitment
    appraisal: Appraisal


class Reputation[Audience, Standing](BaseModel):
    audience: Audience
    standing: Standing


class RelationshipStrength[Appraisal](RootModel[Appraisal]):
    """Appraisal of the strength of the subject relationship."""


class Availability[Extent](RootModel[Extent]):
    """Accessible extent of the subject resource."""


class Preservation[Condition](RootModel[State[Condition]]):
    """Condition retained for the subject resource."""


class Value[
    Subject,
    Basis: Need | Interest | Purpose,
    Detail: (
        FinancialChange
        | TemporalChange
        | Fitness
        | Correctness
        | Reliability
        | RiskDetail
        | CapabilityChange
        | Satisfaction
        | Wellbeing
        | Safety
        | Fulfillment
        | Trust
        | Loyalty
        | Reputation
        | RelationshipStrength
        | Availability
        | Preservation
    ),
](BaseModel):
    """Domain-specific details can be specialized without duplicating the basis."""

    subject: Subject
    relative_to: Basis
    assessments: Annotated[tuple[Assessment[Detail], ...], Field(min_length=1)]


class Economic[Subject, Basis: Need | Interest | Purpose, Extent](
    Value[Subject, Basis, FinancialChange[Extent]]
):
    """Economic benefit or harm assessed through a financial change."""


class Time[Subject, Basis: Need | Interest | Purpose, Extent](
    Value[Subject, Basis, TemporalChange[Extent]]
):
    """Time benefit or harm assessed through a temporal change."""


class Quality[
    Subject,
    Basis: Need | Interest | Purpose,
    Aspect: Fitness | Correctness | Reliability,
](Value[Subject, Basis, Aspect]):
    """Fitness, correctness, or reliability."""


class Risk[
    Subject,
    Basis: Need | Interest | Purpose,
    Adverse: Outcome,
    Change: LikelihoodChange | ConsequenceChange | ExposureChange,
](Value[Subject, Basis, RiskDetail[Adverse, Change]]):
    """Likelihood, consequence, or exposure concerning an adverse Outcome."""


class Capability[
    Subject,
    Basis: Need | Interest | Purpose,
    Work: Activity,
    Evidence,
](Value[Subject, Basis, CapabilityChange[Work, Evidence]]):
    """Change in the ability to accomplish an Activity."""


class HumanWelfare[
    Subject,
    Basis: Need | Interest | Purpose,
    Aspect: Satisfaction | Wellbeing | Safety | Fulfillment,
](Value[Subject, Basis, Aspect]):
    """Satisfaction, wellbeing, safety, or fulfillment."""


class Relationships[
    Subject,
    Basis: Need | Interest | Purpose,
    Aspect: Trust | Loyalty | Reputation | RelationshipStrength,
](Value[Subject, Basis, Aspect]):
    """The relationship or parties being valued are the subject, stated once."""


class Resources[
    Subject,
    Basis: Need | Interest | Purpose,
    Aspect: Availability | Preservation,
](Value[Subject, Basis, Aspect]):
    """Availability or preservation of a scarce subject resource."""
