"""Worth relative to a basis, expressed through eight independent dimensions."""

from typing import Literal

from pydantic import BaseModel

from .activity import Activity
from .outcome import Outcome
from .purpose import Purpose
from .rule import Requirement
from .type import Assessment, CONFIG, Interest, Need, State


class Value[
    Subject,
    Basis: Need[object, object] | Interest[object, object] | Purpose,
    Detail,
](BaseModel, frozen=True):
    model_config = CONFIG
    subject: Subject
    relative_to: Basis
    assessment: Assessment[Detail]


class FinancialChange[Amount](BaseModel, frozen=True):
    model_config = CONFIG
    operation: Literal["earned", "saved", "preserved", "made_available", "spent", "lost", "made_unavailable"]
    extent: Amount


class TemporalChange[Extent](BaseModel, frozen=True):
    model_config = CONFIG
    operation: Literal["saved", "gained", "made_available", "consumed", "lost"]
    extent: Extent


class Fitness[End: Purpose, Attainment](BaseModel, frozen=True):
    model_config = CONFIG
    purpose: End
    attainment: Attainment


class Correctness[Duty: Requirement[object, object], Conformity](BaseModel, frozen=True):
    model_config = CONFIG
    requirement: Duty
    conformity: Conformity


class Reliability[Context, Expected: Outcome[State[object]], Observation](BaseModel, frozen=True):
    model_config = CONFIG
    context: Context
    expected: Expected
    observation: Observation


class Likelihood[Adverse: Outcome[State[object]], Extent](BaseModel, frozen=True):
    model_config = CONFIG
    adverse: Adverse
    direction: Literal["reduced", "increased"]
    extent: Extent


class Consequence[Adverse: Outcome[State[object]], Extent](BaseModel, frozen=True):
    model_config = CONFIG
    adverse: Adverse
    direction: Literal["reduced", "increased"]
    extent: Extent


class Exposure[Adverse: Outcome[State[object]], Evidence](BaseModel, frozen=True):
    model_config = CONFIG
    adverse: Adverse
    operation: Literal["removed", "introduced"]
    evidence: Evidence


class Ability[Work: Activity[object, Outcome[State[object]] | Purpose], Evidence](BaseModel, frozen=True):
    model_config = CONFIG
    activity: Work
    operation: Literal["gained", "strengthened", "weakened", "lost"]
    evidence: Evidence


class Satisfaction[Expectation, Appraisal](BaseModel, frozen=True):
    model_config = CONFIG
    expectation: Expectation
    appraisal: Appraisal


class Wellbeing[Condition](BaseModel, frozen=True):
    model_config = CONFIG
    condition: Condition


class Safety[Threat, Protection](BaseModel, frozen=True):
    model_config = CONFIG
    threat: Threat
    protection: Protection


class Fulfillment[End: Purpose, Attainment](BaseModel, frozen=True):
    model_config = CONFIG
    purpose: End
    attainment: Attainment


class Trust[Conduct, Appraisal](BaseModel, frozen=True):
    model_config = CONFIG
    expected_conduct: Conduct
    appraisal: Appraisal


class Loyalty[Commitment, Appraisal](BaseModel, frozen=True):
    model_config = CONFIG
    commitment: Commitment
    appraisal: Appraisal


class Reputation[Audience, Standing](BaseModel, frozen=True):
    model_config = CONFIG
    audience: Audience
    standing: Standing


class RelationshipStrength[Appraisal](BaseModel, frozen=True):
    model_config = CONFIG
    appraisal: Appraisal


class Availability[Accessible](BaseModel, frozen=True):
    model_config = CONFIG
    accessible: Accessible


class Preservation[Retained](BaseModel, frozen=True):
    model_config = CONFIG
    retained: Retained


class Economic[Subject, Basis: Need[object, object] | Interest[object, object] | Purpose, Change: FinancialChange[object]](
    Value[Subject, Basis, Change], frozen=True
):
    dimension: Literal["economic"] = "economic"


class Time[Subject, Basis: Need[object, object] | Interest[object, object] | Purpose, Change: TemporalChange[object]](
    Value[Subject, Basis, Change], frozen=True
):
    dimension: Literal["time"] = "time"


class Quality[
    Subject,
    Basis: Need[object, object] | Interest[object, object] | Purpose,
    Detail: Fitness[Purpose, object] | Correctness[Requirement[object, object], object] | Reliability[object, Outcome[State[object]], object],
](Value[Subject, Basis, Detail], frozen=True):
    dimension: Literal["quality"] = "quality"


class Risk[
    Subject,
    Basis: Need[object, object] | Interest[object, object] | Purpose,
    Detail: Likelihood[Outcome[State[object]], object] | Consequence[Outcome[State[object]], object] | Exposure[Outcome[State[object]], object],
](Value[Subject, Basis, Detail], frozen=True):
    dimension: Literal["risk"] = "risk"


class Capability[
    Subject,
    Basis: Need[object, object] | Interest[object, object] | Purpose,
    Detail: Ability[Activity[object, Outcome[State[object]] | Purpose], object],
](Value[Subject, Basis, Detail], frozen=True):
    dimension: Literal["capability"] = "capability"


class HumanWelfare[
    Subject,
    Basis: Need[object, object] | Interest[object, object] | Purpose,
    Detail: Satisfaction[object, object] | Wellbeing[object] | Safety[object, object] | Fulfillment[Purpose, object],
](Value[Subject, Basis, Detail], frozen=True):
    dimension: Literal["human_welfare"] = "human_welfare"


class Relationships[
    Subject,
    Basis: Need[object, object] | Interest[object, object] | Purpose,
    Detail: Trust[object, object] | Loyalty[object, object] | Reputation[object, object] | RelationshipStrength[object],
](Value[Subject, Basis, Detail], frozen=True):
    dimension: Literal["relationships"] = "relationships"


class Resources[
    Subject,
    Basis: Need[object, object] | Interest[object, object] | Purpose,
    Detail: Availability[object] | Preservation[object],
](Value[Subject, Basis, Detail], frozen=True):
    dimension: Literal["resources"] = "resources"
