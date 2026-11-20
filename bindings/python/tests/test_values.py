"""Counterexamples and positive constructions for all value detail families."""

from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from organization_model.examples import (
    BusinessNeed,
    CapabilityAssessment,
    CustomerInterest,
    CustomerRelationship,
    EconomicAssessment,
    Organization,
    Person,
    QualityAssessment,
    RefundProcess,
    RefundPurpose,
    RefundService,
    RelationshipAssessment,
    ResourceAssessment,
    RiskAssessment,
    SupportCapacity,
    SupportRequirement,
    TimeAssessment,
    ValueProfile,
    WelfareAssessment,
)


def purpose() -> RefundPurpose:
    return RefundPurpose.model_validate(
        (
            {"state": {"status": "refund_issued"}},
            {"state": {"status": "customer_informed"}},
        )
    )


def need() -> BusinessNeed:
    return BusinessNeed(holder=Organization(name="Service business"), required=purpose())


def interest() -> CustomerInterest:
    return CustomerInterest(holder=Person(name="Customer"), concern=purpose())


def requirement() -> SupportRequirement:
    return SupportRequirement.model_validate({"context": {}, "target": purpose()})


def process() -> RefundProcess:
    return RefundProcess.model_validate(
        {
            "inputs": {
                "approved_review": {
                    "inputs": {
                        "context": {"receipt_present": True, "days_since_purchase": 3},
                        "target": {},
                    },
                    "outcomes": {"state": {"status": "approved"}},
                },
                "prepared_notice": {
                    "inputs": (),
                    "outcomes": {"state": {"status": "notice_ready"}},
                },
            },
            "outcomes": purpose(),
        }
    )


def payload(
    model: type[BaseModel], detail: Mapping[str, object], effect: str = "benefit"
) -> dict[str, object]:
    subject: object = RefundService()
    basis: object = need()
    if model is WelfareAssessment:
        subject = Person(name="Customer")
        basis = interest()
    elif model is RelationshipAssessment:
        subject = CustomerRelationship(
            customer=Person(name="Customer"), organization=Organization(name="Service business")
        )
        basis = interest()
    elif model is ResourceAssessment:
        subject = SupportCapacity(team=Organization(name="Service business"))
    return {
        "subject": subject,
        "relative_to": basis,
        "assessment": {"kind": effect, "detail": detail},
    }


def facets() -> tuple[tuple[type[BaseModel], dict[str, object]], ...]:
    return (
        (
            EconomicAssessment,
            {
                "kind": "financial_change",
                "operation": "saved",
                "extent": {"amount": Decimal("12.50"), "currency": "USD"},
            },
        ),
        (
            TimeAssessment,
            {"kind": "time_change", "operation": "saved", "extent": timedelta(minutes=20)},
        ),
        (QualityAssessment, {"kind": "fitness", "purpose": purpose(), "attainment": "met"}),
        (
            QualityAssessment,
            {"kind": "correctness", "requirement": requirement(), "conformity": "conforming"},
        ),
        (
            QualityAssessment,
            {
                "kind": "reliability",
                "context": {},
                "required_outcome": {"state": {"status": "refund_issued"}},
                "observation": Decimal("0.95"),
            },
        ),
        (
            RiskAssessment,
            {
                "kind": "likelihood",
                "adverse_outcome": {"state": {"consequence": "customer_lost"}},
                "direction": "reduced",
                "extent": Decimal("0.15"),
            },
        ),
        (
            RiskAssessment,
            {
                "kind": "consequence",
                "adverse_outcome": {"state": {"consequence": "customer_lost"}},
                "direction": "reduced",
                "extent": {"amount": Decimal("50"), "currency": "USD"},
            },
        ),
        (
            RiskAssessment,
            {
                "kind": "exposure",
                "adverse_outcome": {"state": {"consequence": "customer_lost"}},
                "operation": "removed",
                "basis": "exposure_path_closed",
            },
        ),
        (
            CapabilityAssessment,
            {
                "kind": "ability_change",
                "activity": process(),
                "operation": "gained",
                "evidence": "demonstrated",
            },
        ),
        (
            WelfareAssessment,
            {"kind": "satisfaction", "expectation": interest(), "assessment": "satisfied"},
        ),
        (WelfareAssessment, {"kind": "wellbeing", "condition": "improved"}),
        (
            WelfareAssessment,
            {"kind": "safety", "threat": "workplace_injury", "protection": "hazard_removed"},
        ),
        (
            WelfareAssessment,
            {"kind": "fulfillment", "purpose": purpose(), "attainment": "fulfilled"},
        ),
        (
            RelationshipAssessment,
            {
                "kind": "trust",
                "expected_conduct": purpose(),
                "assessment": "confidence_increased",
            },
        ),
        (
            RelationshipAssessment,
            {"kind": "loyalty", "commitment": purpose(), "assessment": "commitment_strengthened"},
        ),
        (
            RelationshipAssessment,
            {"kind": "reputation", "audience": (Person(name="Observer"),), "standing": "trusted"},
        ),
        (
            RelationshipAssessment,
            {"kind": "relationship_strength", "assessment": "strengthened"},
        ),
        (
            ResourceAssessment,
            {
                "kind": "availability",
                "accessible": {"magnitude": Decimal("10"), "unit": "staff_hours"},
            },
        ),
        (ResourceAssessment, {"kind": "preservation", "retained": "capacity_preserved"}),
    )


def harm_facets() -> tuple[tuple[type[BaseModel], dict[str, object]], ...]:
    changes: dict[str, dict[str, object]] = {
        "financial_change": {"operation": "spent"},
        "time_change": {"operation": "consumed"},
        "fitness": {"attainment": "unmet"},
        "correctness": {"conformity": "nonconforming"},
        "reliability": {"observation": Decimal("0.5")},
        "likelihood": {"direction": "increased"},
        "consequence": {"direction": "increased"},
        "exposure": {"operation": "introduced", "basis": "exposure_path_open"},
        "ability_change": {"operation": "lost", "evidence": "capacity_unavailable"},
        "satisfaction": {"assessment": "unsatisfied"},
        "wellbeing": {"condition": "diminished"},
        "safety": {"protection": "hazard_present"},
        "fulfillment": {"attainment": "unfulfilled"},
        "trust": {"assessment": "confidence_reduced"},
        "loyalty": {"assessment": "commitment_weakened"},
        "reputation": {"standing": "distrusted"},
        "relationship_strength": {"assessment": "weakened"},
        "availability": {"accessible": {"magnitude": Decimal("0"), "unit": "staff_hours"}},
        "preservation": {"retained": "capacity_depleted"},
    }
    return tuple((model, detail | changes[str(detail["kind"])]) for model, detail in facets())


@pytest.mark.parametrize(("model", "detail"), facets())
def test_each_detail_has_a_valid_complete_construction(
    model: type[BaseModel], detail: dict[str, object]
) -> None:
    instance = model.model_validate(payload(model, detail))
    dumped = instance.model_dump()
    assert dumped["assessment"]["kind"] == "benefit"
    assert dumped["assessment"]["detail"]["kind"] == detail["kind"]
    assert model.model_validate_json(instance.model_dump_json()) == instance


@pytest.mark.parametrize(("model", "detail"), harm_facets())
def test_harm_is_representable_in_every_dimension_and_detail_family(
    model: type[BaseModel], detail: dict[str, object]
) -> None:
    instance = model.model_validate(payload(model, detail, "harm"))
    assert instance.model_dump()["assessment"]["kind"] == "harm"
    assert model.model_validate_json(instance.model_dump_json()) == instance


@pytest.mark.parametrize(
    ("operation", "evidence", "effect"),
    (
        ("strengthened", "additional_capacity_demonstrated", "benefit"),
        ("weakened", "reduced_capacity_demonstrated", "harm"),
    ),
)
def test_capability_can_change_without_being_wholly_gained_or_lost(
    operation: str, evidence: str, effect: str
) -> None:
    detail = {
        "kind": "ability_change",
        "activity": process(),
        "operation": operation,
        "evidence": evidence,
    }
    instance = CapabilityAssessment.model_validate(payload(CapabilityAssessment, detail, effect))
    assert instance.assessment.detail.operation == operation


@pytest.mark.parametrize(
    ("model", "detail", "opposite"),
    tuple(
        (model, detail, opposite)
        for collection, opposite in ((facets(), "harm"), (harm_facets(), "benefit"))
        for model, detail in collection
        if detail["kind"] not in {"financial_change", "time_change", "reliability", "availability"}
    ),
)
def test_declared_worth_cannot_be_recombined_with_opposite_detail(
    model: type[BaseModel], detail: dict[str, object], opposite: str
) -> None:
    """These are the explicit example judgments, not universal polarity rules."""
    with pytest.raises(ValidationError):
        model.model_validate(payload(model, detail, opposite))


@pytest.mark.parametrize(
    ("model", "detail", "constituent"),
    tuple(
        (model, detail, constituent)
        for model, detail in facets()
        for constituent in detail
        if constituent not in {"kind", "operation", "direction"}
    ),
)
def test_each_detail_requires_its_semantic_constituents(
    model: type[BaseModel], detail: dict[str, object], constituent: str
) -> None:
    incomplete = dict(detail)
    incomplete.pop(constituent)
    with pytest.raises(ValidationError):
        model.model_validate(payload(model, incomplete))


@pytest.mark.parametrize(
    "model",
    (
        EconomicAssessment,
        TimeAssessment,
        QualityAssessment,
        RiskAssessment,
        CapabilityAssessment,
        WelfareAssessment,
        RelationshipAssessment,
        ResourceAssessment,
    ),
)
def test_dimension_rejects_detail_from_another_dimension(model: type[BaseModel]) -> None:
    wrong_detail = (
        {"kind": "wellbeing", "condition": "improved"}
        if model is EconomicAssessment
        else {
            "kind": "financial_change",
            "operation": "saved",
            "extent": {"amount": Decimal("10"), "currency": "USD"},
        }
    )
    with pytest.raises(ValidationError):
        model.model_validate(payload(model, wrong_detail))


@pytest.mark.parametrize(
    "extent",
    (
        {"amount": Decimal("-1"), "currency": "USD"},
        {"amount": Decimal("10"), "currency": "EUR"},
        {"amount": "10", "currency": "USD"},
        {"amount": Decimal("NaN"), "currency": "USD"},
    ),
)
def test_money_uses_magnitude_and_declared_currency(extent: dict[str, object]) -> None:
    detail = {"kind": "financial_change", "operation": "saved", "extent": extent}
    with pytest.raises(ValidationError):
        EconomicAssessment.model_validate(payload(EconomicAssessment, detail))


def test_time_magnitude_cannot_be_negative() -> None:
    detail = {"kind": "time_change", "operation": "saved", "extent": timedelta(seconds=-1)}
    with pytest.raises(ValidationError):
        TimeAssessment.model_validate(payload(TimeAssessment, detail))


@pytest.mark.parametrize("probability", (Decimal("-0.1"), Decimal("1.1"), Decimal("Infinity")))
def test_probability_rejects_out_of_range_values(probability: Decimal) -> None:
    risk = {
        "kind": "likelihood",
        "adverse_outcome": {"state": {"consequence": "customer_lost"}},
        "direction": "reduced",
        "extent": probability,
    }
    quality = {
        "kind": "reliability",
        "context": {},
        "required_outcome": {"state": {"status": "refund_issued"}},
        "observation": probability,
    }
    with pytest.raises(ValidationError):
        RiskAssessment.model_validate(payload(RiskAssessment, risk))
    with pytest.raises(ValidationError):
        QualityAssessment.model_validate(payload(QualityAssessment, quality))


@pytest.mark.parametrize(
    "accessible",
    (
        {"magnitude": Decimal("3"), "unit": "USD"},
        {"magnitude": Decimal("-3"), "unit": "staff_hours"},
    ),
)
def test_resource_quantity_preserves_unit_and_magnitude(accessible: dict[str, object]) -> None:
    detail = {"kind": "availability", "accessible": accessible}
    with pytest.raises(ValidationError):
        ResourceAssessment.model_validate(payload(ResourceAssessment, detail))


def test_reputation_requires_an_audience() -> None:
    detail = {"kind": "reputation", "audience": (), "standing": "trusted"}
    with pytest.raises(ValidationError):
        RelationshipAssessment.model_validate(payload(RelationshipAssessment, detail))


def test_profile_contains_all_dimensions_and_all_declared_facets() -> None:
    values = tuple(model.model_validate(payload(model, detail)) for model, detail in facets())
    profile = ValueProfile.model_validate(values)
    assert len(profile.root) == 19
    assert {value.dimension for value in profile.root} == {
        "economic",
        "time",
        "quality",
        "risk",
        "capability",
        "human_welfare",
        "relationships",
        "resources",
    }


def test_profile_preserves_tradeoffs_and_qualitative_value() -> None:
    economic = EconomicAssessment.model_validate(payload(EconomicAssessment, facets()[0][1]))
    welfare = WelfareAssessment.model_validate(
        payload(WelfareAssessment, {"kind": "wellbeing", "condition": "diminished"}, "harm")
    )
    resources = ResourceAssessment.model_validate(
        payload(
            ResourceAssessment,
            {"kind": "preservation", "retained": "capacity_preserved"},
            "unchanged",
        )
    )
    profile = ValueProfile((economic, welfare, resources))
    assert tuple(value.assessment.kind for value in profile.root) == (
        "benefit",
        "harm",
        "unchanged",
    )
    assert welfare.model_dump()["assessment"]["detail"]["condition"] == "diminished"


def test_profile_cannot_be_empty() -> None:
    with pytest.raises(ValidationError):
        ValueProfile(())


def test_closed_exposure_requires_compatible_evidence() -> None:
    detail = {
        "kind": "exposure",
        "adverse_outcome": {"state": {"consequence": "customer_lost"}},
        "operation": "removed",
        "basis": "exposure_path_open",
    }
    with pytest.raises(ValidationError):
        RiskAssessment.model_validate(payload(RiskAssessment, detail))


def test_gained_capability_requires_compatible_evidence() -> None:
    detail = {
        "kind": "ability_change",
        "activity": process(),
        "operation": "gained",
        "evidence": "capacity_unavailable",
    }
    with pytest.raises(ValidationError):
        CapabilityAssessment.model_validate(payload(CapabilityAssessment, detail))
