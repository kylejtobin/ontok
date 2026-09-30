"""An address proves an occurrence's kind, and lineage its causes."""

from ontok.events import (
    AddressConstructor,
    EmissionAddress,
    Lineage,
    Ordinal,
    OriginAddress,
    PolicyProvenance,
    WorkTypeName,
)

from .ontology import OrderPlaced, identifier, placed


class OrderShipped(OrderPlaced):
    provenance: PolicyProvenance


def shipped() -> OrderShipped:
    return OrderShipped(
        id=identifier(2),
        occurred=placed().occurred,
        event_type=placed().event_type,
        order=placed().order,
        provenance=PolicyProvenance(
            work_type=WorkTypeName("shop-Fulfilment"), cause=placed().id, position=Ordinal(0)
        ),
    )


def test_an_occurrence_without_provenance_is_originating_and_one_with_it_is_derived() -> None:
    assert isinstance(
        AddressConstructor.validate_python(placed(), from_attributes=True), OriginAddress
    )
    assert isinstance(
        AddressConstructor.validate_python(shipped(), from_attributes=True), EmissionAddress
    )


def test_lineage_connects_each_cause_to_the_occurrence_itself() -> None:
    lineage = Lineage.model_validate(shipped(), from_attributes=True)
    assert tuple(c.target for c in lineage.causation) == (shipped().id,)
    assert tuple(c.source for c in lineage.causation) == (placed().id,)
