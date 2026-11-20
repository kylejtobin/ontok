"""Value assessments grouped by universal dimensions and relative worth."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .activity import Activity
from .outcome import Outcome
from .purpose import Purpose
from .rule import Requirement
from .type import Interest, Need, State


class ValueDimension(StrEnum):
    """The eight dimensions through which organizational worth is expressed."""

    ECONOMIC = "economic"
    TIME = "time"
    QUALITY = "quality"
    RISK = "risk"
    CAPABILITY = "capability"
    HUMAN_WELFARE = "human_welfare"
    RELATIONSHIPS = "relationships"
    RESOURCES = "resources"


class AssessmentDirection(StrEnum):
    """How a dimensional change affects worth relative to the stated basis."""

    BENEFIT = "benefit"
    HARM = "harm"
    UNCHANGED = "unchanged"


class ChangeDirection(StrEnum):
    """Whether a magnitude or ability increased or decreased."""

    INCREASED = "increased"
    DECREASED = "decreased"


class ExposureDirection(StrEnum):
    """Whether exposure to an adverse outcome was introduced or removed."""

    INTRODUCED = "introduced"
    REMOVED = "removed"


class RiskChangeKind(StrEnum):
    """The distinct aspects of exposure to an adverse outcome that can change."""

    LIKELIHOOD = "likelihood"
    CONSEQUENCE = "consequence"
    EXPOSURE = "exposure"


class Assessment[Detail](BaseModel):
    """A dimension-specific judgment of worth under the enclosing Value's basis."""

    dimension: ValueDimension = Field(
        description="The universal dimension to which this assessment belongs."
    )
    direction: AssessmentDirection = Field(
        description="Whether the detail benefits, harms, or leaves worth unchanged relative to the basis."
    )
    detail: Detail = Field(
        description="The detail required by this dimension, independent of its worth."
    )


class FinancialChange[Nature, Extent](BaseModel):
    """A financial change whose nature and extent are supplied by the domain."""

    nature: Nature = Field(
        description="How money was earned, saved, preserved, made available, or adversely changed."
    )
    extent: Extent = Field(
        description="The monetary or qualitative extent of that financial change."
    )


class TemporalChange[Nature, Extent](BaseModel):
    """A temporal change whose nature and extent are supplied by the domain."""

    nature: Nature = Field(
        description="How time was saved, gained, made available, or adversely changed."
    )
    extent: Extent = Field(
        description="The duration or stated temporal condition of the change."
    )


class Fitness[Attainment](BaseModel):
    """Fitness of the subject for accomplishing an intended Purpose."""

    purpose: Purpose = Field(description="The Purpose against which fitness is considered.")
    attainment: Attainment = Field(
        description="The extent or condition of attainment of that Purpose."
    )


class Correctness[Context, Target, Conformity](BaseModel):
    """Conformity of the subject to a binding requirement."""

    requirement: Requirement[Context, Target] = Field(
        description="The required Rule against which correctness is considered."
    )
    conformity: Conformity = Field(
        description="The extent or condition of conformity to that requirement."
    )


class Reliability[Context, Observation](BaseModel):
    """Whether an expected Outcome is attained in a specified context."""

    context: Context = Field(description="The context in which the Outcome is expected.")
    expected: Outcome = Field(description="The Outcome expected in that context.")
    observation: Observation = Field(
        description="The observation of whether the expected Outcome was attained."
    )


class LikelihoodChange[Extent](BaseModel):
    """Change in the likelihood of the adverse Outcome held by RiskDetail."""

    kind: Literal[RiskChangeKind.LIKELIHOOD] = Field(
        default=RiskChangeKind.LIKELIHOOD,
        description="Identifies a change in likelihood.",
    )
    direction: ChangeDirection = Field(
        description="Whether the adverse Outcome became more or less likely."
    )
    extent: Extent = Field(description="The extent of the likelihood change.")


class ConsequenceChange[Extent](BaseModel):
    """Change in the consequence of the adverse Outcome held by RiskDetail."""

    kind: Literal[RiskChangeKind.CONSEQUENCE] = Field(
        default=RiskChangeKind.CONSEQUENCE,
        description="Identifies a change in consequence.",
    )
    direction: ChangeDirection = Field(
        description="Whether the adverse Outcome became more or less consequential."
    )
    extent: Extent = Field(description="The extent of the consequence change.")


class ExposureChange[Evidence](BaseModel):
    """Introduction or removal of exposure to the adverse Outcome held by RiskDetail."""

    kind: Literal[RiskChangeKind.EXPOSURE] = Field(
        default=RiskChangeKind.EXPOSURE,
        description="Identifies a change in exposure.",
    )
    direction: ExposureDirection = Field(
        description="Whether exposure was introduced or removed."
    )
    evidence: Evidence = Field(description="Evidence supporting the exposure change.")


class RiskDetail(BaseModel):
    """One change in likelihood, consequence, or exposure to an adverse Outcome."""

    adverse: Outcome = Field(description="The adverse Outcome whose risk changed.")
    change: LikelihoodChange | ConsequenceChange | ExposureChange = Field(
        discriminator="kind",
        description="Exactly one change in likelihood, consequence, or exposure.",
    )


class CapabilityChange[Evidence](BaseModel):
    """Change in the ability to perform an Activity."""

    activity: Activity = Field(description="The Activity whose accomplishment is affected.")
    direction: ChangeDirection = Field(
        description="Whether the ability to accomplish that Activity increased or decreased."
    )
    evidence: Evidence = Field(description="Evidence supporting the capability change.")


class Satisfaction[Expectation, Appraisal](BaseModel):
    """An appraisal of satisfaction against an expectation."""

    expectation: Expectation = Field(description="The expectation governing satisfaction.")
    appraisal: Appraisal = Field(description="The appraisal relative to that expectation.")


class Wellbeing[Condition](BaseModel):
    """The condition of people already identified by the Value's subject."""

    condition: State[Condition] = Field(
        description="The human wellbeing condition being assessed."
    )


class Safety[Threat, Protection](BaseModel):
    """Protection of people against a threat."""

    threat: Threat = Field(description="The threat to the people concerned.")
    protection: Protection = Field(description="The protection against that threat.")


class Fulfillment[Attainment](BaseModel):
    """Attainment of a Purpose as a matter of human welfare."""

    purpose: Purpose = Field(description="The Purpose whose fulfillment matters.")
    attainment: Attainment = Field(
        description="The extent or condition of attainment of that Purpose."
    )


class Trust[Conduct, Appraisal](BaseModel):
    """Trust within the relationship identified by the Value's subject."""

    expected_conduct: Conduct = Field(description="The conduct expected of the related parties.")
    appraisal: Appraisal = Field(description="The appraisal of trust in that conduct.")


class Loyalty[Commitment, Appraisal](BaseModel):
    """Loyalty within the relationship identified by the Value's subject."""

    commitment: Commitment = Field(description="The commitment on which loyalty is assessed.")
    appraisal: Appraisal = Field(description="The appraisal of loyalty to that commitment.")


class Reputation[Audience, Standing](BaseModel):
    """The subject's standing with an audience."""

    audience: Audience = Field(description="The audience among whom reputation is held.")
    standing: Standing = Field(description="The subject's standing with that audience.")


class RelationshipStrength[Appraisal](BaseModel):
    """Strength of the relationship identified by the enclosing Value."""

    appraisal: Appraisal = Field(
        description="The appraisal of the subject relationship's strength."
    )


class Availability[Extent](BaseModel):
    """Availability of the scarce resource identified by the enclosing Value."""

    accessible: Extent = Field(description="The accessible extent of the subject resource.")


class Preservation[Condition](BaseModel):
    """Preservation of the scarce resource identified by the enclosing Value."""

    retained: State[Condition] = Field(
        description="The condition retained for the subject resource."
    )


class EconomicAssessment(Assessment[FinancialChange]):
    """A financial change and its economic worth."""

    dimension: Literal[ValueDimension.ECONOMIC] = Field(
        default=ValueDimension.ECONOMIC,
        description="Identifies the Economic dimension.",
    )


class TimeAssessment(Assessment[TemporalChange]):
    """A temporal change and its worth."""

    dimension: Literal[ValueDimension.TIME] = Field(
        default=ValueDimension.TIME,
        description="Identifies the Time dimension.",
    )


class QualityAssessment(Assessment[Fitness | Correctness | Reliability]):
    """Fitness, correctness, or reliability and its worth."""

    dimension: Literal[ValueDimension.QUALITY] = Field(
        default=ValueDimension.QUALITY,
        description="Identifies the Quality dimension.",
    )


class RiskAssessment(Assessment[RiskDetail]):
    """A change in exposure to uncertain adverse outcomes and its worth."""

    dimension: Literal[ValueDimension.RISK] = Field(
        default=ValueDimension.RISK,
        description="Identifies the Risk dimension.",
    )


class CapabilityAssessment(Assessment[CapabilityChange]):
    """A change in organizational ability and its worth."""

    dimension: Literal[ValueDimension.CAPABILITY] = Field(
        default=ValueDimension.CAPABILITY,
        description="Identifies the Capability dimension.",
    )


class HumanWelfareAssessment(Assessment[Satisfaction | Wellbeing | Safety | Fulfillment]):
    """One of four human welfare details and its worth."""

    dimension: Literal[ValueDimension.HUMAN_WELFARE] = Field(
        default=ValueDimension.HUMAN_WELFARE,
        description="Identifies the Human Welfare dimension.",
    )


class RelationshipsAssessment(
    Assessment[Trust | Loyalty | Reputation | RelationshipStrength]
):
    """One of four relationship details and its worth."""

    dimension: Literal[ValueDimension.RELATIONSHIPS] = Field(
        default=ValueDimension.RELATIONSHIPS,
        description="Identifies the Relationships dimension.",
    )


class ResourcesAssessment(Assessment[Availability | Preservation]):
    """Availability or preservation of scarce resources and its worth."""

    dimension: Literal[ValueDimension.RESOURCES] = Field(
        default=ValueDimension.RESOURCES,
        description="Identifies the Resources dimension.",
    )


class Value[Subject](BaseModel):
    """Worth of one subject relative to one basis in any mixture of dimensions."""

    subject: Subject = Field(description="The matter whose worth is being assessed.")
    relative_to: Need | Interest | Purpose = Field(
        description="The Need, Interest, or Purpose relative to which worth is assessed."
    )
    assessments: Annotated[
        tuple[
            Annotated[
                EconomicAssessment
                | TimeAssessment
                | QualityAssessment
                | RiskAssessment
                | CapabilityAssessment
                | HumanWelfareAssessment
                | RelationshipsAssessment
                | ResourcesAssessment,
                Field(discriminator="dimension"),
            ],
            ...,
        ],
        Field(
            min_length=1,
            description=(
                "Nonempty, dimension-specific judgments sharing this one subject and "
                "basis without collapsing their distinct details into a single measure."
            ),
        ),
    ]


class Economic[Subject](Value[Subject]):
    """Value narrowed to economic assessments."""

    assessments: Annotated[
        tuple[EconomicAssessment, ...],
        Field(min_length=1, description="The subject's economic assessments."),
    ]


class Time[Subject](Value[Subject]):
    """Value narrowed to temporal assessments."""

    assessments: Annotated[
        tuple[TimeAssessment, ...],
        Field(min_length=1, description="The subject's time assessments."),
    ]


class Quality[Subject](Value[Subject]):
    """Value narrowed to quality assessments."""

    assessments: Annotated[
        tuple[QualityAssessment, ...],
        Field(min_length=1, description="The subject's quality assessments."),
    ]


class Risk[Subject](Value[Subject]):
    """Value narrowed to risk assessments."""

    assessments: Annotated[
        tuple[RiskAssessment, ...],
        Field(min_length=1, description="The subject's risk assessments."),
    ]


class Capability[Subject](Value[Subject]):
    """Value narrowed to capability assessments."""

    assessments: Annotated[
        tuple[CapabilityAssessment, ...],
        Field(min_length=1, description="The subject's capability assessments."),
    ]


class HumanWelfare[Subject](Value[Subject]):
    """Value narrowed to human-welfare assessments."""

    assessments: Annotated[
        tuple[HumanWelfareAssessment, ...],
        Field(min_length=1, description="The subject's human-welfare assessments."),
    ]


class Relationships[Subject](Value[Subject]):
    """Value narrowed to relationships assessments."""

    assessments: Annotated[
        tuple[RelationshipsAssessment, ...],
        Field(min_length=1, description="The subject relationship's assessments."),
    ]


class Resources[Subject](Value[Subject]):
    """Value narrowed to resource assessments."""

    assessments: Annotated[
        tuple[ResourcesAssessment, ...],
        Field(min_length=1, description="The subject resource's assessments."),
    ]
