"""Worth relative to a need, interest, or purpose across distinct dimensions."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from .activity import Activity
from .outcome import Outcome
from .purpose import Purpose
from .rule import Requirement
from .type import Interest, Need, State


class Assessment[Detail](BaseModel):
    """Worth relative to the enclosing Value's basis, not the sign of a change."""

    direction: Literal["benefit", "harm", "unchanged"] = Field(
        description="Whether this detail benefits, harms, or does not change worth relative to the basis."
    )
    detail: Detail = Field(description="The dimension-specific basis for this assessment.")


class FinancialChange[Nature, Extent](BaseModel):
    """Money earned, saved, preserved, made available, or an adverse counterpart."""

    nature: Nature = Field(description="The domain-defined nature of the financial change.")
    extent: Extent = Field(
        description="The monetary or qualitative extent of the financial change."
    )


class TemporalChange[Nature, Extent](BaseModel):
    """Time saved, gained, made available, or an adverse counterpart."""

    nature: Nature = Field(description="The domain-defined nature of the temporal change.")
    extent: Extent = Field(
        description="The duration or stated temporal condition describing its extent."
    )


class Fitness[Attainment](BaseModel):
    """Fitness for an organizational Purpose."""

    purpose: Purpose = Field(description="The Purpose against which fitness is assessed.")
    attainment: Attainment = Field(description="The extent to which that Purpose is attained.")


class Correctness[Context, Target, Conformity](BaseModel):
    """Conformity to a requirement rather than an arbitrary measurement."""

    requirement: Requirement[Context, Target] = Field(
        description="The required Rule against which correctness is assessed."
    )
    conformity: Conformity = Field(
        description="The extent or condition of conformity to that requirement."
    )


class Reliability[Context, Observation](BaseModel):
    """An expected Outcome assessed against its observation in context."""

    context: Context = Field(description="The context in which the Outcome is expected.")
    expected: Outcome = Field(description="The Outcome expected in this context.")
    observation: Observation = Field(
        description="The observation of whether the expected Outcome was attained."
    )


class LikelihoodChange[Extent](BaseModel):
    """Change in the likelihood of an adverse Outcome."""

    direction: Literal["increased", "decreased"] = Field(
        description="Whether likelihood increased or decreased."
    )
    extent: Extent = Field(description="The extent of the change in likelihood.")


class ConsequenceChange[Extent](BaseModel):
    """Change in the consequence of an adverse Outcome."""

    direction: Literal["increased", "decreased"] = Field(
        description="Whether the adverse consequence increased or decreased."
    )
    extent: Extent = Field(description="The extent of the change in consequence.")


class ExposureChange[Evidence](BaseModel):
    """Introduction or removal of exposure to an adverse Outcome."""

    direction: Literal["introduced", "removed"] = Field(
        description="Whether exposure to the adverse Outcome was introduced or removed."
    )
    evidence: Evidence = Field(description="Evidence supporting the change in exposure.")


class RiskDetail(BaseModel):
    """An adverse Outcome and exactly one distinct form of change in risk."""

    adverse: Outcome = Field(description="The adverse Outcome to which this risk relates.")
    change: LikelihoodChange | ConsequenceChange | ExposureChange = Field(
        description="A likelihood, consequence, or exposure change concerning that Outcome."
    )


class CapabilityChange[Evidence](BaseModel):
    """A change in the ability to accomplish an Activity."""

    activity: Activity = Field(description="The Activity whose accomplishment is affected.")
    direction: Literal["increased", "decreased"] = Field(
        description="Whether the ability to accomplish the Activity increased or decreased."
    )
    evidence: Evidence = Field(description="Evidence supporting the capability change.")


class Satisfaction[Expectation, Appraisal](BaseModel):
    """Appraisal relative to an expectation."""

    expectation: Expectation = Field(description="The expectation to which satisfaction relates.")
    appraisal: Appraisal = Field(description="The appraisal of satisfaction against that expectation.")


class Wellbeing[Condition](BaseModel):
    """The wellbeing condition of the person or people valued."""

    condition: State[Condition] = Field(
        description="The condition of the person or people, whose identity is the Value subject."
    )


class Safety[Threat, Protection](BaseModel):
    """Protection against a threat affecting human welfare."""

    threat: Threat = Field(description="The threat against which safety is assessed.")
    protection: Protection = Field(description="The protection against that threat.")


class Fulfillment[Attainment](BaseModel):
    """Attainment of a Purpose as a dimension of human welfare."""

    purpose: Purpose = Field(description="The Purpose whose fulfillment is assessed.")
    attainment: Attainment = Field(description="The degree or condition of its attainment.")


class Trust[Conduct, Appraisal](BaseModel):
    """Trust in the relationship or parties identified by the Value subject."""

    expected_conduct: Conduct = Field(description="The conduct expected of the related party.")
    appraisal: Appraisal = Field(description="The appraisal of trust in that conduct.")


class Loyalty[Commitment, Appraisal](BaseModel):
    """Loyalty in the relationship or parties identified by the Value subject."""

    commitment: Commitment = Field(description="The commitment underlying loyalty.")
    appraisal: Appraisal = Field(description="The appraisal of that loyalty.")


class Reputation[Audience, Standing](BaseModel):
    """Standing of the subject relationship or parties with an audience."""

    audience: Audience = Field(description="The audience with whom reputation is held.")
    standing: Standing = Field(description="The subject's standing with that audience.")


class RelationshipStrength[Appraisal](RootModel[Appraisal]):
    """Strength of the relationship already identified by the Value subject."""

    root: Appraisal = Field(description="The appraisal of the subject relationship's strength.")


class Availability[Extent](RootModel[Extent]):
    """Availability of the scarce resource identified by the Value subject."""

    root: Extent = Field(description="The extent of the subject resource that is accessible.")


class Preservation[Condition](RootModel[State[Condition]]):
    """Preservation of the scarce resource identified by the Value subject."""

    root: State[Condition] = Field(
        description="The condition retained for the subject resource."
    )


class EconomicAssessment(Assessment[FinancialChange]):
    """Economic change assessed relative to the shared Value basis."""

    dimension: Literal["economic"] = Field(
        description="Identifies the Economic dimension of this assessment."
    )


class TimeAssessment(Assessment[TemporalChange]):
    """Temporal change assessed relative to the shared Value basis."""

    dimension: Literal["time"] = Field(
        description="Identifies the Time dimension of this assessment."
    )


class QualityAssessment(Assessment[Fitness | Correctness | Reliability]):
    """Exactly one of fitness, correctness, or reliability."""

    dimension: Literal["quality"] = Field(
        description="Identifies the Quality dimension of this assessment."
    )


class RiskAssessment(Assessment[RiskDetail]):
    """Likelihood, consequence, or exposure concerning an adverse Outcome."""

    dimension: Literal["risk"] = Field(
        description="Identifies the Risk dimension of this assessment."
    )


class CapabilityAssessment(Assessment[CapabilityChange]):
    """Change in ability to accomplish an Activity."""

    dimension: Literal["capability"] = Field(
        description="Identifies the Capability dimension of this assessment."
    )


class HumanWelfareAssessment(Assessment[Satisfaction | Wellbeing | Safety | Fulfillment]):
    """Exactly one form of human welfare."""

    dimension: Literal["human_welfare"] = Field(
        description="Identifies the Human Welfare dimension of this assessment."
    )


class RelationshipsAssessment(
    Assessment[Trust | Loyalty | Reputation | RelationshipStrength]
):
    """Exactly one form of relationship value."""

    dimension: Literal["relationships"] = Field(
        description="Identifies the Relationships dimension of this assessment."
    )


class ResourcesAssessment(Assessment[Availability | Preservation]):
    """Availability or preservation of a scarce resource."""

    dimension: Literal["resources"] = Field(
        description="Identifies the Resources dimension of this assessment."
    )


class Value[Subject](BaseModel):
    """One subject and basis supporting one or more independent dimensional assessments."""

    subject: Subject = Field(description="The matter whose worth is being assessed.")
    relative_to: Need | Interest | Purpose = Field(
        description="The Need, Interest, or Purpose relative to which worth is assessed."
    )
    assessments: Annotated[
        tuple[
            EconomicAssessment
            | TimeAssessment
            | QualityAssessment
            | RiskAssessment
            | CapabilityAssessment
            | HumanWelfareAssessment
            | RelationshipsAssessment
            | ResourcesAssessment,
            ...,
        ],
        Field(
            min_length=1,
            description=(
                "One or more dimension-specific assessments sharing this subject and basis, "
                "without combining their extents into one quantity."
            ),
        ),
    ]


class Economic[Subject](Value[Subject]):
    """Economic Value, retaining the universal subject and basis."""

    assessments: Annotated[
        tuple[EconomicAssessment, ...],
        Field(min_length=1, description="The subject's Economic assessments."),
    ]


class Time[Subject](Value[Subject]):
    """Time Value, retaining the universal subject and basis."""

    assessments: Annotated[
        tuple[TimeAssessment, ...],
        Field(min_length=1, description="The subject's Time assessments."),
    ]


class Quality[Subject](Value[Subject]):
    """Quality Value, retaining the universal subject and basis."""

    assessments: Annotated[
        tuple[QualityAssessment, ...],
        Field(min_length=1, description="The subject's fitness, correctness, or reliability assessments."),
    ]


class Risk[Subject](Value[Subject]):
    """Risk Value, retaining the universal subject and basis."""

    assessments: Annotated[
        tuple[RiskAssessment, ...],
        Field(min_length=1, description="The subject's Risk assessments."),
    ]


class Capability[Subject](Value[Subject]):
    """Capability Value, retaining the universal subject and basis."""

    assessments: Annotated[
        tuple[CapabilityAssessment, ...],
        Field(min_length=1, description="The subject's Capability assessments."),
    ]


class HumanWelfare[Subject](Value[Subject]):
    """Human Welfare Value, retaining the universal subject and basis."""

    assessments: Annotated[
        tuple[HumanWelfareAssessment, ...],
        Field(min_length=1, description="The subject's Human Welfare assessments."),
    ]


class Relationships[Subject](Value[Subject]):
    """Relationships Value, with the relationship or related parties as its subject."""

    assessments: Annotated[
        tuple[RelationshipsAssessment, ...],
        Field(min_length=1, description="The subject relationship's assessments."),
    ]


class Resources[Subject](Value[Subject]):
    """Resources Value, with a scarce asset or material as its subject."""

    assessments: Annotated[
        tuple[ResourcesAssessment, ...],
        Field(min_length=1, description="The subject resource's assessments."),
    ]
