"""Counterexamples from a second domain, independent of the shipped example."""

from typing import Annotated, Literal

import pytest
from pydantic import BaseModel, Field, ValidationError

from organization_model.scalars import MODEL_CONFIG, Nonempty
from organization_model.work import (
    ActionPermission,
    Activity,
    Authority,
    Decision,
    Event,
    ObligationPower,
    Permission,
    Process,
    ProducedOutcome,
    Purpose,
    Requirement,
    Responsibility,
    Role,
)


class PassedInspection(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    inspected: Literal["passed"] = "passed"


class FailedInspection(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    inspected: Literal["failed"] = "failed"


class AcceptedGoods(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    disposition: Literal["accepted"] = "accepted"


class RejectedGoods(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    disposition: Literal["rejected"] = "rejected"


class DeliveredGoods(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    disposition: Literal["delivered"] = "delivered"


class Receipt(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    receipt: Literal["issued"] = "issued"


class Accepted(ProducedOutcome[AcceptedGoods], frozen=True):
    pass


class Rejected(ProducedOutcome[RejectedGoods], frozen=True):
    pass


class Delivered(ProducedOutcome[DeliveredGoods], frozen=True):
    pass


class Receipted(ProducedOutcome[Receipt], frozen=True):
    pass


class AcceptCase(Permission[PassedInspection, Accepted], frozen=True):
    case: Literal["accept"] = "accept"


class RejectCase(Permission[FailedInspection, Rejected], frozen=True):
    case: Literal["reject"] = "reject"


type InspectionCases = Annotated[AcceptCase | RejectCase, Field(discriminator="case")]


class InspectionDecision(Decision[InspectionCases], frozen=True):
    pass


class AcceptGoods(Activity[PassedInspection, Accepted], frozen=True):
    pass


class RejectGoods(Activity[FailedInspection, Rejected], frozen=True):
    pass


class DispatchDependencies(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    acceptance: AcceptGoods


class DispatchPurpose(Purpose, frozen=True):
    root: tuple[Delivered, Nonempty[Receipted]]


class DispatchProcess(Process[DispatchDependencies, DispatchPurpose], frozen=True):
    pass


class DispatchDuty(Requirement[PassedInspection, Delivered], frozen=True):
    pass


class DeliveryResponsibility(Responsibility, frozen=True):
    root: DispatchDuty


class WarehouseRole(Role, frozen=True):
    root: tuple[DeliveryResponsibility]


class EstablishedPolicy(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    source: Literal["warehouse_policy"] = "warehouse_policy"


class DispatchPermission(ActionPermission[PassedInspection, Delivered], frozen=True):
    pass


class WarehouseAuthority(
    Authority[Literal["warehouse"], EstablishedPolicy, DispatchPermission], frozen=True
):
    pass


class DeliveryImposition(ObligationPower[DispatchDuty], frozen=True):
    pass


class WeatherChange(BaseModel, frozen=True):
    model_config = MODEL_CONFIG
    state: Literal["storm"] = "storm"


def accepted() -> Accepted:
    return Accepted(state=AcceptedGoods())


def delivered() -> Delivered:
    return Delivered(state=DeliveredGoods())


def dispatch_purpose() -> DispatchPurpose:
    return DispatchPurpose((delivered(), (Receipted(state=Receipt()),)))


def duty() -> DispatchDuty:
    return DispatchDuty(context=PassedInspection(), target=delivered())


def test_decision_admits_both_intended_complete_cases() -> None:
    accepted_decision = InspectionDecision(
        AcceptCase(context=PassedInspection(), target=accepted())
    )
    rejected_decision = InspectionDecision(
        RejectCase(context=FailedInspection(), target=Rejected(state=RejectedGoods()))
    )
    assert isinstance(accepted_decision.root, AcceptCase)
    assert isinstance(rejected_decision.root, RejectCase)


@pytest.mark.parametrize(
    ("case", "inspection", "disposition"),
    [
        ("accept", "failed", "accepted"),
        ("accept", "passed", "rejected"),
        ("reject", "passed", "rejected"),
        ("reject", "failed", "accepted"),
    ],
)
def test_decision_rejects_crossed_contexts_and_results(
    case: str, inspection: str, disposition: str
) -> None:
    with pytest.raises(ValidationError, match="literal_error"):
        InspectionDecision.model_validate(
            {
                "case": case,
                "context": {"inspected": inspection},
                "target": {"state": {"disposition": disposition}},
            }
        )


def test_decision_cannot_accept_a_foreign_third_alternative() -> None:
    with pytest.raises(ValidationError, match="union_tag_invalid"):
        InspectionDecision.model_validate({"case": "waive_inspection", "context": {}, "target": {}})


def test_decision_does_not_guess_a_case_without_its_tag() -> None:
    with pytest.raises(ValidationError, match="union_tag_not_found"):
        InspectionDecision.model_validate(
            {
                "context": {"inspected": "passed"},
                "target": {"state": {"disposition": "accepted"}},
            }
        )


def test_nested_construction_rechecks_a_deliberately_corrupted_case() -> None:
    legitimate = AcceptCase(context=PassedInspection(), target=accepted())
    corrupted = legitimate.model_copy(update={"target": Rejected(state=RejectedGoods())})
    with pytest.raises(ValidationError):
        InspectionDecision.model_validate(corrupted)


@pytest.mark.parametrize("independent_field", ["alternatives", "selected"])
def test_decision_has_no_independent_alternative_or_selection_slot(independent_field: str) -> None:
    payload = AcceptCase(context=PassedInspection(), target=accepted()).model_dump()
    payload[independent_field] = {"case": "reject"}
    with pytest.raises(ValidationError, match="extra_forbidden"):
        InspectionDecision.model_validate(payload)


def test_process_keeps_its_intended_end_once() -> None:
    process = DispatchProcess(
        inputs=DispatchDependencies(
            acceptance=AcceptGoods(inputs=PassedInspection(), outcomes=accepted())
        ),
        outcomes=dispatch_purpose(),
    )
    assert isinstance(process.outcomes, DispatchPurpose)
    assert set(DispatchProcess.model_fields) == {"inputs", "outcomes"}
    assert process.outcomes.root[0].state.disposition == "delivered"


def test_process_cannot_substitute_failed_work_for_its_success_prerequisite() -> None:
    failed = RejectGoods(inputs=FailedInspection(), outcomes=Rejected(state=RejectedGoods()))
    with pytest.raises(ValidationError):
        DispatchProcess.model_validate(
            {"inputs": {"acceptance": failed}, "outcomes": dispatch_purpose()}
        )


def test_process_cannot_add_a_second_disagreeing_purpose() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        DispatchProcess.model_validate(
            {
                "inputs": {
                    "acceptance": AcceptGoods(inputs=PassedInspection(), outcomes=accepted())
                },
                "outcomes": dispatch_purpose(),
                "purpose": "discard the goods",
            }
        )


@pytest.mark.parametrize("invalid_goals", [(), (delivered(),), (delivered(), ())])
def test_grouped_purpose_requires_every_group_and_its_members(invalid_goals: object) -> None:
    with pytest.raises(ValidationError):
        DispatchPurpose.model_validate(invalid_goals)


def test_event_is_not_an_intended_outcome_constituent() -> None:
    happened = Event[Delivered](occurred=delivered())
    with pytest.raises(ValidationError):
        DispatchPurpose.model_validate((happened, (Receipted(state=Receipt()),)))


def test_authority_requires_a_formal_basis() -> None:
    with pytest.raises(ValidationError, match="established_by"):
        WarehouseAuthority.model_validate(
            {
                "holder": "warehouse",
                "grant": DispatchPermission(context=PassedInspection(), target=delivered()),
            }
        )


def test_authority_permission_is_not_a_duty_or_an_imposition_power() -> None:
    legitimate = WarehouseAuthority(
        holder="warehouse",
        established_by=EstablishedPolicy(),
        grant=DispatchPermission(context=PassedInspection(), target=delivered()),
    )
    assert legitimate.grant.force == "permitted"
    for incompatible in (duty(), DeliveryImposition(imposable=duty())):
        with pytest.raises(ValidationError):
            WarehouseAuthority.model_validate(
                {
                    "holder": "warehouse",
                    "established_by": EstablishedPolicy(),
                    "grant": incompatible,
                }
            )


def test_role_exists_without_requiring_an_occupant() -> None:
    role = WarehouseRole((DeliveryResponsibility(duty()),))
    assert role.root[0].root.target.state.disposition == "delivered"
    assert set(WarehouseRole.model_fields) == {"root"}


def test_external_event_needs_no_fictional_internal_activity() -> None:
    event = Event[WeatherChange](occurred=WeatherChange())
    assert event.occurred.state == "storm"
