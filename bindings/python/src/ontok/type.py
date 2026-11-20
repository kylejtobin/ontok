"""Semantic constituents shared by Ontok's foundational concepts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, RootModel

CONFIG = ConfigDict(frozen=True, strict=True, extra="forbid", validate_default=True, revalidate_instances="always")


class State[Content](RootModel[Content], frozen=True):
    """A condition whose content is established by a domain declaration."""


class Need[Holder, Required](BaseModel, frozen=True):
    """Something a holder requires."""

    model_config = CONFIG
    holder: Holder
    required: Required


class Interest[Holder, Concern](BaseModel, frozen=True):
    """Something in which a holder has a stake."""

    model_config = CONFIG
    holder: Holder
    concern: Concern


class Benefit[Detail](BaseModel, frozen=True):
    model_config = CONFIG
    kind: Literal["benefit"] = "benefit"
    detail: Detail


class Harm[Detail](BaseModel, frozen=True):
    model_config = CONFIG
    kind: Literal["harm"] = "harm"
    detail: Detail


class Unchanged[Detail](BaseModel, frozen=True):
    model_config = CONFIG
    kind: Literal["unchanged"] = "unchanged"
    detail: Detail


class Assessment[Detail](RootModel[Benefit[Detail] | Harm[Detail] | Unchanged[Detail]], frozen=True):
    """Worth relative to a basis; change direction alone cannot establish worth."""
