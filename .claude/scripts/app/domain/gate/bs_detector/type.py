"""The bs_detector context's atomic vocabulary: the kind axis every violation pins, the file-license
scalars a path-licensed detector reads, and the def node-type a function violation proves. Scalars only,
per the topology."""

from enum import StrEnum
from typing import Literal

from pydantic import Field, RootModel

from app.domain.foreign.ast import NodeKind


class BSKindName(StrEnum):
    """The closed set of bad-syntax kinds, one member per detector. A violation pins its detector's member,
    so a finding always names which detector proved it."""

    MODULE_LEVEL_FUNCTION = "module_level_function"


class BSKind(RootModel[BSKindName], frozen=True):
    """A bad-syntax kind carried as a value: the detector identity a violation reports."""

    root: BSKindName


class DefNodeType(RootModel[Literal[NodeKind.FUNCTION_DEF, NodeKind.ASYNC_FUNCTION_DEF]], frozen=True):
    """The node-type tag of a function definition, sync or async: the closed value space a violation reads
    off a node to prove it is a def, refusing a class or any other statement."""

    root: Literal[NodeKind.FUNCTION_DEF, NodeKind.ASYNC_FUNCTION_DEF]


class FilePath(RootModel[str], frozen=True):
    """The path of a scanned source file: any non-empty path, the license-bearing value of a file with no
    module-level-function license."""

    root: str = Field(min_length=1)


class LicensedPath(RootModel[str], frozen=True):
    """A file path where a module-level function is licensed: a route file (`api/<ctx>.py`) or the
    composition root (`main.py`), per the topology. The pattern is the domain's bound, so this scalar
    constructs only from a licensed path and refuses every other, proving the license by construction."""

    root: str = Field(pattern=r"(?:.*/)?(?:api/[^/]+|main)\.py$")


class LicenseKind(StrEnum):
    """The license axis for a scanned file: licensed for module-level definitions, or not."""

    LICENSED = "licensed"
    UNLICENSED = "unlicensed"
