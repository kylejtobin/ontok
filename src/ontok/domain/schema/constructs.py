from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .base import OntokId, OntokModel, TimeInterval


class Concept(OntokModel):
    """Reusable category or type that domain ontologies specialize."""

    kind: Literal["concept"] = "concept"
    parent_ids: tuple[OntokId, ...] = Field(default_factory=tuple)


class Context(OntokModel):
    """Scope in which claims, states, relations, or rules apply."""

    kind: Literal["context"] = "context"
    parent_id: OntokId | None = None


class Evidence(OntokModel):
    """Source, observation, or artifact supporting a claim."""

    kind: Literal["evidence"] = "evidence"
    source_uri: str | None = None
    source_text: str | None = None
    observed_at: TimeInterval | None = None
    context_id: OntokId | None = None


class Entity(OntokModel):
    """Persistent thing with identity."""

    kind: Literal["entity"] = "entity"
    concept_id: OntokId | None = None
    external_ids: tuple[str, ...] = Field(default_factory=tuple)
    context_id: OntokId | None = None


class Event(OntokModel):
    """Occurrence or change in time."""

    kind: Literal["event"] = "event"
    concept_id: OntokId | None = None
    interval: TimeInterval | None = None
    participant_ids: tuple[OntokId, ...] = Field(default_factory=tuple)
    context_id: OntokId | None = None


class State(OntokModel):
    """Condition true over an interval or within a scope."""

    kind: Literal["state"] = "state"
    subject_id: OntokId
    concept_id: OntokId | None = None
    value: str | None = None
    interval: TimeInterval | None = None
    context_id: OntokId | None = None


class Role(OntokModel):
    """Contextual participation of an entity in an event, relation, or context."""

    kind: Literal["role"] = "role"
    entity_id: OntokId
    role_concept_id: OntokId | None = None
    event_id: OntokId | None = None
    relation_id: OntokId | None = None
    context_id: OntokId | None = None

    @model_validator(mode="after")
    def _has_scope_anchor(self) -> "Role":
        if self.event_id is None and self.relation_id is None and self.context_id is None:
            raise ValueError("role must be anchored by event_id, relation_id, or context_id")
        return self


class Relation(OntokModel):
    """Typed connection between two ONTOK objects."""

    kind: Literal["relation"] = "relation"
    subject_id: OntokId
    predicate: str = Field(min_length=1)
    object_id: OntokId
    concept_id: OntokId | None = None
    interval: TimeInterval | None = None
    context_id: OntokId | None = None


class Claim(OntokModel):
    """Asserted proposition that can be supported, contradicted, revised, or promoted."""

    kind: Literal["claim"] = "claim"
    subject_id: OntokId
    predicate: str = Field(min_length=1)
    object_id: OntokId | None = None
    literal_value: str | None = None
    evidence_ids: tuple[OntokId, ...] = Field(default_factory=tuple)
    context_id: OntokId | None = None
    interval: TimeInterval | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    revises_claim_ids: tuple[OntokId, ...] = Field(default_factory=tuple)
    contradicts_claim_ids: tuple[OntokId, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _has_object_or_literal(self) -> "Claim":
        if self.object_id is None and self.literal_value is None:
            raise ValueError("claim must have object_id or literal_value")
        if self.object_id is not None and self.literal_value is not None:
            raise ValueError("claim cannot have both object_id and literal_value")
        return self


class Rule(OntokModel):
    """Constraint, derivation, identity policy, contradiction policy, or retrieval policy."""

    kind: Literal["rule"] = "rule"
    rule_type: Literal["constraint", "derivation", "identity", "contradiction", "retrieval", "policy"]
    expression: str = Field(min_length=1)
    applies_to_ids: tuple[OntokId, ...] = Field(default_factory=tuple)
    context_id: OntokId | None = None
