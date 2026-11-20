"""Constructive and counterexample checks for the declared organizational meanings."""

from datetime import timedelta
from itertools import product

import pytest
from pydantic import ValidationError

from ontok import examples as e
from ontok.work import Activity


def goal() -> e.RefundPurpose:
    return e.RefundPurpose(
        (e.RefundOutcome(state=e.RefundIssued()), e.NotificationOutcome(state=e.CustomerInformed()))
    )


def cases() -> tuple[e.ApprovedReview, e.ExpiredReview, e.MissingReceiptReview]:
    return (
        e.ApprovedReview.model_validate(
            {
                "inputs": {
                    "context": {"receipt_present": True, "days_since_purchase": 10},
                    "target": {},
                },
                "outcomes": {"state": {"status": "approved"}},
            }
        ),
        e.ExpiredReview.model_validate(
            {
                "inputs": {
                    "context": {"receipt_present": True, "days_since_purchase": 31},
                    "target": {},
                },
                "outcomes": {"state": {"status": "declined", "reason": "expired"}},
            }
        ),
        e.MissingReceiptReview.model_validate(
            {
                "inputs": {
                    "context": {"receipt_present": False, "days_since_purchase": 10},
                    "target": {},
                },
                "outcomes": {"state": {"status": "declined", "reason": "missing_receipt"}},
            }
        ),
    )


def role() -> e.SupportRole:
    duty = e.SupportRequirement(context=e.SupportContext(), target=goal())
    return e.SupportRole((e.SupportResponsibility(duty),))


def participation() -> e.SupportParticipation:
    return e.SupportParticipation(occupant=e.Person(name="Reviewer"), role=role())


def process() -> e.RefundProcess:
    return e.RefundProcess(
        inputs=e.RefundPrerequisites(
            approved_review=cases()[0],
            prepared_notice=e.PrepareNotice.model_validate(
                {"inputs": (), "outcomes": {"state": {"status": "notice_ready"}}}
            ),
        ),
        outcomes=goal(),
    )


@pytest.mark.parametrize(
    ("tag_index", "context_index", "outcome_index"), tuple(product(range(3), repeat=3))
)
def test_exactly_the_three_declared_decision_cases_survive_the_cartesian_product(
    tag_index: int, context_index: int, outcome_index: int
) -> None:
    alternatives = cases()
    selected_tag = alternatives[tag_index].case
    raw = {
        "case": selected_tag,
        "inputs": alternatives[context_index].inputs,
        "outcomes": alternatives[outcome_index].outcomes,
    }
    if tag_index == context_index == outcome_index:
        selected = e.RefundDecision.model_validate(raw)
        assert selected.root.case == selected_tag
    else:
        with pytest.raises(ValidationError):
            e.RefundDecision.model_validate(raw)


@pytest.mark.parametrize("day", (0, 30))
def test_policy_boundaries_accept_eligible_inputs(day: int) -> None:
    assert e.Eligible(receipt_present=True, days_since_purchase=day)


@pytest.mark.parametrize("day", (-1, 31))
def test_policy_boundaries_reject_ineligible_inputs(day: int) -> None:
    with pytest.raises(ValidationError):
        e.Eligible(receipt_present=True, days_since_purchase=day)


def test_grouped_purpose_retains_required_types_at_every_level() -> None:
    refund, notification = goal().root
    assert e.GroupedPurpose(((refund, refund), (notification,))).root[0] == (refund, refund)
    for invalid in ((), ((refund,),), ((refund,), ()), ((notification,), (refund,))):
        with pytest.raises(ValidationError):
            e.GroupedPurpose.model_validate(invalid)


def test_maintenance_is_a_valid_outcome_without_a_change_of_state() -> None:
    maintained = e.ServiceMaintenance(state=e.ServiceAvailable(), throughout=timedelta(hours=8))
    assert e.ContinuousService((maintained,)).root[0].state.status == "available"
    with pytest.raises(ValidationError):
        e.ServiceMaintenance(state=e.ServiceAvailable(), throughout=timedelta(hours=-1))


def test_outcome_has_no_mandatory_value_assessment() -> None:
    assert e.RefundOutcome(state=e.RefundIssued()).state.status == "refund_issued"
    assert set(e.RefundOutcome.model_fields) == {"state", "kind"}


def test_a_role_and_its_responsibility_do_not_require_an_assigned_performer() -> None:
    standalone = role()
    assert standalone.root[0].root.target == goal()
    assert set(e.SupportRole.model_fields) == {"root"}


def test_same_role_supports_human_or_software_participation() -> None:
    for occupant in (e.Person(name="Reviewer"), e.SoftwareParticipant(name="Review service")):
        assigned = e.SupportParticipation(occupant=occupant, role=role())
        assert assigned.role == role()


@pytest.mark.parametrize(
    "grant",
    (
        {"kind": "action_permission", "context": {}, "target": {}},
        {"kind": "decision_power", "scope": cases()[0]},
        {
            "kind": "obligation_power",
            "imposable": e.SupportRequirement(context=e.SupportContext(), target=goal()),
        },
    ),
)
def test_authority_preserves_all_three_distinct_forms(grant: dict[str, object]) -> None:
    authority = e.RefundAuthority.model_validate(
        {
            "holder": role(),
            "established_by": {"title": "Refund policy", "revision": "1"},
            "grant": grant,
        }
    )
    assert authority.grant.kind == grant["kind"]


def test_permission_requirement_prohibition_and_validity_remain_distinct() -> None:
    assert cases()[0].inputs.force == "permitted"
    assert cases()[1].inputs.force == "prohibited"
    assert role().root[0].root.force == "required"
    valid = e.NoticeValidity(context=e.SupportContext(), target=goal().root[1])
    assert valid.force == "valid"
    with pytest.raises(ValidationError):
        e.NoticeValidity.model_validate(
            {"force": "required", "context": {}, "target": goal().root[1]}
        )


def exchanges() -> tuple[dict[str, object], ...]:
    actor = participation()
    return (
        {
            "kind": "communication",
            "sender": actor,
            "recipients": (e.Person(name="Customer"),),
            "content": {"message": "Refund approved"},
        },
        {
            "kind": "responsibility_transfer",
            "source": actor,
            "destination": actor,
            "responsibility": role().root[0],
        },
        {
            "kind": "coordination",
            "participants": (actor, e.SoftwareParticipant(name="Notifier")),
            "work": process(),
        },
    )


@pytest.mark.parametrize("exchange", exchanges())
def test_each_interaction_form_constructs_without_requiring_distinct_actor_identities(
    exchange: dict[str, object],
) -> None:
    assert e.ServiceInteraction.model_validate(exchange).root.kind == exchange["kind"]


@pytest.mark.parametrize(
    ("exchange", "required"),
    ((exchanges()[0], "recipients"), (exchanges()[1], "responsibility"), (exchanges()[2], "work")),
)
def test_interaction_forms_cannot_omit_their_distinctive_constituent(
    exchange: dict[str, object], required: str
) -> None:
    incomplete = {key: value for key, value in exchange.items() if key != required}
    with pytest.raises(ValidationError):
        e.ServiceInteraction.model_validate(incomplete)


def test_communication_cannot_have_no_recipients() -> None:
    raw = dict(exchanges()[0], recipients=())
    with pytest.raises(ValidationError):
        e.ServiceInteraction.model_validate(raw)


class ResponseToCancellation(Activity[e.SupplierEvent, e.ServiceMaintenance], frozen=True):
    """An occurrence affects work by being a required typed input."""


def test_external_event_can_be_a_dependency_without_an_affects_registry() -> None:
    occurrence = e.SupplierEvent(
        occurred=e.SupplierCancellation(supplier="Supplier", reason="Storm")
    )
    response = ResponseToCancellation(
        inputs=occurrence,
        outcomes=e.ServiceMaintenance(state=e.ServiceAvailable(), throughout=timedelta(hours=1)),
    )
    assert response.inputs.occurred.reason == "Storm"
    with pytest.raises(ValidationError):
        ResponseToCancellation.model_validate({"outcomes": response.outcomes})


def test_frozen_nested_state_cannot_be_reassigned_normally() -> None:
    instance = process()
    field_name = "days_since_purchase"
    with pytest.raises(ValidationError, match="frozen_instance"):
        setattr(instance.inputs.approved_review.inputs.context, field_name, 99)


def test_json_roundtrip_preserves_exact_tagged_types_and_tuple_structure() -> None:
    instance = process()
    restored = e.RefundProcess.model_validate_json(instance.model_dump_json())
    assert restored == instance
    assert isinstance(restored.outcomes.root, tuple)
    assert isinstance(restored.inputs.approved_review, e.ApprovedReview)
    decision = e.RefundDecision(cases()[1])
    assert isinstance(
        e.RefundDecision.model_validate_json(decision.model_dump_json()).root, e.ExpiredReview
    )
