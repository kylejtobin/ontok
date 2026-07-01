import ast
from functools import cached_property
from pathlib import Path

from ast2json import ast2json # pyright: ignore[reportUnknownVariableType]
from pydantic import BaseModel, Field

from app.domain.foreign.ast import Module


class BSReport(BaseModel):
    """A report of a BS detection."""

    path: Path = Field(description="The path of the file that was scanned.")

    @cached_property
    def module(self) -> Module:
        return Module.model_validate(ast2json(ast.parse(self.path.read_text())))
