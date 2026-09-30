from pydantic import BaseModel, ConfigDict, Field

from ontok.core.identity import NodeId


class Node(BaseModel):
    """A distinct thing represented in the organizational graph."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    id: NodeId = Field(description="The identifier that distinguishes this Node.")


class Connection(BaseModel):
    """A typed link declaring how Nodes relate within the organizational graph."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        revalidate_instances="never",
    )

    source: NodeId = Field(description="The Node from which the Connection originates.")
    target: NodeId = Field(description="The Node at which the Connection terminates.")
