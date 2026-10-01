from pydantic import ConfigDict, Field, RootModel

from ontok.core.structure import Connection


class RelationId(RootModel[str]):
    """A canonical UUID that distinguishes a Relation: version 7 when minted, version 8 when
    derived from content."""

    model_config = ConfigDict(
        frozen=True, strict=True, validate_default=True, revalidate_instances="never"
    )

    root: str = Field(
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[78][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    )


class Relation(Connection):
    """An identifiable domain association from one Node to another."""

    id: RelationId = Field(description="The identifier that distinguishes this Relation.")
