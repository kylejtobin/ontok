from pydantic import BaseModel, ConfigDict

from ontok.core import Causation, NodeId
from ontok.events.value import Provenance


class Lineage(BaseModel):
    """A derived occurrence's identity and provenance, from which its causation follows."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    id: NodeId
    provenance: Provenance

    @property
    def causation(self) -> tuple[Causation, ...]:
        return tuple(Causation(source=cause, target=self.id) for cause in self.provenance.causes)
