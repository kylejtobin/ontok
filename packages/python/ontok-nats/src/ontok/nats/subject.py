from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, TypeAdapter, computed_field

from ontok.core import NodeId
from ontok.events import EventTypeName, Provenance


class EntitySubject(BaseModel):
    """Every occurrence about one entity: the subject a claim checks, a history walks, and a latest
    read of every kind scans."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId

    @computed_field
    @property
    def text(self) -> str:
        return f"event.{self.about.root}.>"


class KindSubject(BaseModel):
    """Every occurrence of one kind about one entity: what a latest read of that kind scans."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId
    event_type: EventTypeName = Field(validation_alias=AliasPath("scope", "event_type"))

    @computed_field
    @property
    def text(self) -> str:
        return f"event.{self.about.root}.{self.event_type.root}.>"


LatestSubject = Annotated[KindSubject | EntitySubject, Field(union_mode="left_to_right")]
LatestSubjectConstructor: TypeAdapter[KindSubject | EntitySubject] = TypeAdapter(LatestSubject)


class FilterSubject(BaseModel):
    """Every occurrence of one kind about any entity: what a subscription listens for."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    event_type: EventTypeName

    @computed_field
    @property
    def text(self) -> str:
        return f"event.*.{self.event_type.root}.>"


class OriginSubject(BaseModel):
    """Where an originating occurrence is published."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId
    event_type: EventTypeName
    id: NodeId

    @computed_field
    @property
    def text(self) -> str:
        return f"event.{self.about.root}.{self.event_type.root}.{self.id.root}"


class EmissionSubject(BaseModel):
    """Where a derived occurrence is published: its responsibility, its causes, and its position."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    about: NodeId
    event_type: EventTypeName
    provenance: Provenance

    @computed_field
    @property
    def text(self) -> str:
        return ".".join(
            (
                "event",
                self.about.root,
                self.event_type.root,
                self.provenance.work_type.root,
                *(cause.root for cause in self.provenance.causes),
                str(self.provenance.position.root),
            )
        )


AddressSubject = Annotated[EmissionSubject | OriginSubject, Field(union_mode="left_to_right")]
AddressSubjectConstructor: TypeAdapter[EmissionSubject | OriginSubject] = TypeAdapter(
    AddressSubject
)
