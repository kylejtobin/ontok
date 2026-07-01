from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, TypeAdapter, model_validator

from app.domain.foreign.ast import Column, Line, Statement
from app.domain.gate.bs_detector.type import BSKindName, DefNodeType
from app.domain.gate.bs_detector.value import Location


class ModuleLevelFunctionViolation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", from_attributes=True)

    kind: Literal[BSKindName.MODULE_LEVEL_FUNCTION] = BSKindName.MODULE_LEVEL_FUNCTION
    node_type: DefNodeType
    line: Line
    column: Column

    @property
    def location(self) -> Location:
        return Location(line=self.line, column=self.column)


class NotAModuleLevelDef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    statement: Statement

    @model_validator(mode="before")
    @classmethod
    def _wrap(cls, data: object) -> object:
        return {"statement": data}


ModuleLevelDefScan = Annotated[
    ModuleLevelFunctionViolation | NotAModuleLevelDef,
    Field(union_mode="left_to_right"),
]

ModuleLevelDefScanConstructor: TypeAdapter[ModuleLevelFunctionViolation | NotAModuleLevelDef] = TypeAdapter(ModuleLevelDefScan)


class ModuleLevelFunctionFindings(RootModel[tuple[ModuleLevelFunctionViolation, ...]]):
    model_config = ConfigDict(frozen=True)
    root: tuple[ModuleLevelFunctionViolation, ...] = Field()
