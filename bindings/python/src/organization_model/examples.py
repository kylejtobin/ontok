"""Closed domain declarations used to challenge the reusable vocabulary.

The refund policy is illustrative: a receipt and at most 30 elapsed days permit
a refund. These are explicit domain choices, not universal organizational rules.
All declarations below remain models; none performs the described work.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel

from .scalars import (
    MODEL_CONFIG,
    ROOT_CONFIG,
    Duration,
    Money,
    Nonempty,
    Probability,
    Quantity,
    Text,
)
from .value import (
    AbilityChange,
    Assessment,
    Availability,
    Benefit,
    Capability,
    ConsequenceChange,
    Correctness,
    Economic,
    ExposureChange,
    FinancialChange,
    Fitness,
    Fulfillment,
    Harm,
    HumanWelfare,
    Interest,
    LikelihoodChange,
    Loyalty,
    Need,
    Preservation,
    Quality,
    Relationships,
    RelationshipStrength,
    Reliability,
    Reputation,
    Resources,
    Risk,
    Safety,
    Satisfaction,
    Time,
    TimeChange,
    Trust,
    Unchanged,
    Wellbeing,
)
from .work import (
    ActionPermission,
    Activity,
    Authority,
    Communication,
    Coordination,
    Decision,
    DecisionPower,
    Event,
    Interaction,
    MaintainedOutcome,
    ObligationPower,
    Participation,
    Permission,
    Process,
    ProducedOutcome,
    Prohibition,
    Purpose,
    Requirement,
    Responsibility,
    ResponsibilityTransfer,
    Role,
    Validity,
)


class Dollars(Money[Literal["USD"]], frozen=True):
    """A concrete monetary denomination."""


class StaffHours(Quantity[Literal["staff_hours"]], frozen=True):
    """A concrete resource quantity."""


class Organization(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    name: Text


class Person(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["person"] = "person"
    name: Text


class SoftwareParticipant(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    kind: Literal["software"] = "software"
    name: Text


type Occupant = Annotated[Person | SoftwareParticipant, Field(discriminator="kind")]


class Eligible(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    receipt_present: Literal[True]
    days_since_purchase: Annotated[int, Field(ge=0, le=30)]


class Expired(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    receipt_present: Literal[True]
    days_since_purchase: Annotated[int, Field(ge=31)]


class MissingReceipt(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    receipt_present: Literal[False]
    days_since_purchase: Annotated[int, Field(ge=0)]


class RefundAction(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    action: Literal["issue_refund"] = "issue_refund"


class ApprovedState(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    status: Literal["approved"] = "approved"


class ExpiredState(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    status: Literal["declined"] = "declined"
    reason: Literal["expired"] = "expired"


class MissingReceiptState(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    status: Literal["declined"] = "declined"
    reason: Literal["missing_receipt"] = "missing_receipt"


class ApprovedReview(
    Activity[Permission[Eligible, RefundAction], ProducedOutcome[ApprovedState]], frozen=True
):
    case: Literal["approved"] = "approved"


class ExpiredReview(
    Activity[Prohibition[Expired, RefundAction], ProducedOutcome[ExpiredState]], frozen=True
):
    case: Literal["expired"] = "expired"


class MissingReceiptReview(
    Activity[Prohibition[MissingReceipt, RefundAction], ProducedOutcome[MissingReceiptState]],
    frozen=True,
):
    case: Literal["missing_receipt"] = "missing_receipt"


type ReviewCases = Annotated[
    ApprovedReview | ExpiredReview | MissingReceiptReview, Field(discriminator="case")
]


class RefundDecision(Decision[ReviewCases], frozen=True):
    """The permitted selection is the complete-case union itself."""


class NoticeReady(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    status: Literal["notice_ready"] = "notice_ready"


class PrepareNotice(Activity[tuple[()], ProducedOutcome[NoticeReady]], frozen=True):
    """A nullary work definition is legitimate; not all work consumes a record."""


class RefundPrerequisites(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    approved_review: ApprovedReview
    prepared_notice: PrepareNotice


class RefundIssued(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    status: Literal["refund_issued"] = "refund_issued"


class CustomerInformed(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    status: Literal["customer_informed"] = "customer_informed"


class RefundOutcome(ProducedOutcome[RefundIssued], frozen=True):
    """The refund result, independently usable in a target or occurrence."""


class NotificationOutcome(ProducedOutcome[CustomerInformed], frozen=True):
    """The communication result."""


class RefundPurpose(Purpose, frozen=True):
    """Both results are required; neither is an optional field."""

    root: tuple[RefundOutcome, NotificationOutcome]


class GroupedPurpose(Purpose, frozen=True):
    """Two required, nonempty, independently typed outcome groups."""

    root: tuple[Nonempty[RefundOutcome], Nonempty[NotificationOutcome]]


class RefundProcess(Process[RefundPrerequisites, RefundPurpose], frozen=True):
    """The composed work's outcomes are its single intended end."""


class SupportContext(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    participation: Literal["customer_support"] = "customer_support"


class SupportRequirement(Requirement[SupportContext, RefundPurpose], frozen=True):
    """Responsibility can specify an end without prescribing its method."""


class SupportResponsibility(Responsibility, frozen=True):
    """Duty to obtain the defined customer-support end."""

    root: SupportRequirement


class SupportRole(Role, frozen=True):
    """A role may exist without a human or software occupant."""

    root: tuple[SupportResponsibility]


class SupportParticipation(Participation[Occupant, SupportRole], frozen=True):
    """Either kind of occupant can participate in the same organizational role."""


class PolicyRecord(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    title: Text
    revision: Text


type RefundGrants = Annotated[
    ActionPermission[SupportContext, RefundAction]
    | DecisionPower[RefundDecision]
    | ObligationPower[SupportRequirement],
    Field(discriminator="kind"),
]


class RefundAuthority(Authority[SupportRole, PolicyRecord, RefundGrants], frozen=True):
    """A scoped grant established by a formal policy record."""


class ReceiptMessage(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    message: Text


type ServiceExchanges = Annotated[
    Communication[SupportParticipation, tuple[Person], ReceiptMessage]
    | ResponsibilityTransfer[SupportParticipation, SupportParticipation, SupportResponsibility]
    | Coordination[tuple[SupportParticipation, SoftwareParticipant], RefundProcess],
    Field(discriminator="kind"),
]


class ServiceInteraction(Interaction[ServiceExchanges], frozen=True):
    """Three exchanges with different required participant relationships."""


class SupplierCancellation(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    supplier: Text
    reason: Text


class SupplierEvent(Event[SupplierCancellation], frozen=True):
    """An external occurrence with no mandatory exact timestamp or work origin."""


class RefundEvent(Event[RefundOutcome], frozen=True):
    """A recorded result is distinct from the desired result composition."""


class ServiceAvailable(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    status: Literal["available"] = "available"


class ServiceMaintenance(MaintainedOutcome[ServiceAvailable, Duration], frozen=True):
    """Maintaining a state is an outcome even though the state does not change."""


class ContinuousService(Purpose, frozen=True):
    """A purpose can concern continued satisfaction, not only a new state."""

    root: tuple[ServiceMaintenance]


class NoticeValidity(Validity[SupportContext, NotificationOutcome], frozen=True):
    """A concrete fourth normative form."""


class RefundService(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    name: Literal["refund_service"] = "refund_service"


class BusinessNeed(Need[Organization, RefundPurpose], frozen=True):
    """The need's holder is supplied once, rather than duplicated as beneficiary."""


class CustomerInterest(Interest[Person, RefundPurpose], frozen=True):
    """An alternative basis of worth."""


class EconomicAssessment(
    Economic[RefundService, BusinessNeed, Assessment[FinancialChange[Dollars]]], frozen=True
):
    """A monetary assessment with a fixed, validated denomination."""


class TimeAssessment(
    Time[RefundService, BusinessNeed, Assessment[TimeChange[Duration]]], frozen=True
):
    """Temporal benefit/harm is separate from its native duration magnitude."""


type QualityBenefits = Annotated[
    Fitness[RefundPurpose, Literal["met"]]
    | Correctness[SupportRequirement, Literal["conforming"]]
    | Reliability[SupportContext, RefundOutcome, Probability],
    Field(discriminator="kind"),
]
type QualityHarms = Annotated[
    Fitness[RefundPurpose, Literal["unmet"]]
    | Correctness[SupportRequirement, Literal["nonconforming"]]
    | Reliability[SupportContext, RefundOutcome, Probability],
    Field(discriminator="kind"),
]
type QualityWorth = Annotated[
    Benefit[QualityBenefits] | Harm[QualityHarms], Field(discriminator="kind")
]


class QualityAssessment(Quality[RefundService, BusinessNeed, QualityWorth], frozen=True):
    """Quality has three independently meaningful assessment structures."""


class CustomerLoss(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    consequence: Literal["customer_lost"] = "customer_lost"


class LossOutcome(ProducedOutcome[CustomerLoss], frozen=True):
    """An adverse possibility, without asserting that it has occurred."""


class RemovedExposure(ExposureChange[LossOutcome, Literal["exposure_path_closed"]], frozen=True):
    operation: Literal["removed"] = "removed"


class IntroducedExposure(ExposureChange[LossOutcome, Literal["exposure_path_open"]], frozen=True):
    operation: Literal["introduced"] = "introduced"


class ReducedLikelihood(LikelihoodChange[LossOutcome, Probability], frozen=True):
    direction: Literal["reduced"] = "reduced"


class IncreasedLikelihood(LikelihoodChange[LossOutcome, Probability], frozen=True):
    direction: Literal["increased"] = "increased"


class ReducedConsequence(ConsequenceChange[LossOutcome, Dollars], frozen=True):
    direction: Literal["reduced"] = "reduced"


class IncreasedConsequence(ConsequenceChange[LossOutcome, Dollars], frozen=True):
    direction: Literal["increased"] = "increased"


type RiskBenefits = Annotated[
    ReducedLikelihood | ReducedConsequence | RemovedExposure,
    Field(discriminator="kind"),
]
type RiskHarms = Annotated[
    IncreasedLikelihood | IncreasedConsequence | IntroducedExposure,
    Field(discriminator="kind"),
]
type RiskWorth = Annotated[Benefit[RiskBenefits] | Harm[RiskHarms], Field(discriminator="kind")]


class RiskAssessment(Risk[RefundService, BusinessNeed, RiskWorth], frozen=True):
    """Likelihood, consequence, and exposure remain different assertions."""


class GainedAbility(AbilityChange[RefundProcess, Literal["demonstrated"]], frozen=True):
    operation: Literal["gained"] = "gained"


class StrengthenedAbility(
    AbilityChange[RefundProcess, Literal["additional_capacity_demonstrated"]], frozen=True
):
    operation: Literal["strengthened"] = "strengthened"


class WeakenedAbility(
    AbilityChange[RefundProcess, Literal["reduced_capacity_demonstrated"]], frozen=True
):
    operation: Literal["weakened"] = "weakened"


class LostAbility(AbilityChange[RefundProcess, Literal["capacity_unavailable"]], frozen=True):
    operation: Literal["lost"] = "lost"


type CapabilityBenefits = Annotated[
    GainedAbility | StrengthenedAbility, Field(discriminator="operation")
]
type CapabilityHarms = Annotated[WeakenedAbility | LostAbility, Field(discriminator="operation")]
type CapabilityWorth = Annotated[
    Benefit[CapabilityBenefits] | Harm[CapabilityHarms], Field(discriminator="kind")
]


class CapabilityAssessment(Capability[RefundService, BusinessNeed, CapabilityWorth], frozen=True):
    """Capability concerns the defined work, not an arbitrary capability name."""


type WelfareBenefits = Annotated[
    Satisfaction[CustomerInterest, Literal["satisfied"]]
    | Wellbeing[Literal["improved"]]
    | Safety[Literal["workplace_injury"], Literal["hazard_removed"]]
    | Fulfillment[RefundPurpose, Literal["fulfilled"]],
    Field(discriminator="kind"),
]
type WelfareHarms = Annotated[
    Satisfaction[CustomerInterest, Literal["unsatisfied"]]
    | Wellbeing[Literal["diminished"]]
    | Safety[Literal["workplace_injury"], Literal["hazard_present"]]
    | Fulfillment[RefundPurpose, Literal["unfulfilled"]],
    Field(discriminator="kind"),
]
type WelfareWorth = Annotated[
    Benefit[WelfareBenefits] | Harm[WelfareHarms], Field(discriminator="kind")
]


class WelfareAssessment(HumanWelfare[Person, CustomerInterest, WelfareWorth], frozen=True):
    """A qualitative assessment needs no invented universal numeric scale."""


class CustomerRelationship(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    customer: Person
    organization: Organization


type RelationshipBenefits = Annotated[
    Trust[RefundPurpose, Literal["confidence_increased"]]
    | Loyalty[RefundPurpose, Literal["commitment_strengthened"]]
    | Reputation[Nonempty[Person], Literal["trusted"]]
    | RelationshipStrength[Literal["strengthened"]],
    Field(discriminator="kind"),
]
type RelationshipHarms = Annotated[
    Trust[RefundPurpose, Literal["confidence_reduced"]]
    | Loyalty[RefundPurpose, Literal["commitment_weakened"]]
    | Reputation[Nonempty[Person], Literal["distrusted"]]
    | RelationshipStrength[Literal["weakened"]],
    Field(discriminator="kind"),
]
type RelationshipWorth = Annotated[
    Benefit[RelationshipBenefits] | Harm[RelationshipHarms], Field(discriminator="kind")
]


class RelationshipAssessment(
    Relationships[CustomerRelationship, CustomerInterest, RelationshipWorth], frozen=True
):
    """Relationship value retains the participants and the assessed property."""


class SupportCapacity(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    team: Organization


type ResourceBenefits = Annotated[
    Availability[StaffHours] | Preservation[Literal["capacity_preserved"]],
    Field(discriminator="kind"),
]
type ResourceHarms = Annotated[
    Availability[StaffHours] | Preservation[Literal["capacity_depleted"]],
    Field(discriminator="kind"),
]
type ResourceWorth = Annotated[
    Benefit[ResourceBenefits]
    | Harm[ResourceHarms]
    | Unchanged[Preservation[Literal["capacity_preserved"]]],
    Field(discriminator="kind"),
]


class ResourceAssessment(Resources[SupportCapacity, BusinessNeed, ResourceWorth], frozen=True):
    """Resource quantity has its unit; preservation can be qualitative."""


type AssessmentDimension = Annotated[
    EconomicAssessment
    | TimeAssessment
    | QualityAssessment
    | RiskAssessment
    | CapabilityAssessment
    | WelfareAssessment
    | RelationshipAssessment
    | ResourceAssessment,
    Field(discriminator="dimension"),
]


class ValueProfile(RootModel[Nonempty[AssessmentDimension]], frozen=True):
    """Composition, not eight optional fields or an invented universal score."""

    model_config = ROOT_CONFIG


CLOSED_MODELS: tuple[type[BaseModel], ...] = (
    Dollars,
    StaffHours,
    RefundDecision,
    RefundPurpose,
    GroupedPurpose,
    RefundProcess,
    SupportRole,
    SupportParticipation,
    RefundAuthority,
    ServiceInteraction,
    SupplierEvent,
    RefundEvent,
    ServiceMaintenance,
    ContinuousService,
    NoticeValidity,
    EconomicAssessment,
    TimeAssessment,
    QualityAssessment,
    RiskAssessment,
    CapabilityAssessment,
    WelfareAssessment,
    RelationshipAssessment,
    ResourceAssessment,
    ValueProfile,
)
