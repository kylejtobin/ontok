"""A scanned source file with a license to hold module-level function definitions: the licensed
file concept in the bs_detector context."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from app.domain.gate.bs_detector.type import FilePath, LicenseKind, LicensedPath


class LicensedFile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Literal[LicenseKind.LICENSED] = LicenseKind.LICENSED
    path: LicensedPath


class UnlicensedFile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Literal[LicenseKind.UNLICENSED] = LicenseKind.UNLICENSED
    path: FilePath


FileLicense = Annotated[LicensedFile | UnlicensedFile, Field(union_mode="left_to_right")]

FileLicenseConstructor: TypeAdapter[LicensedFile | UnlicensedFile] = TypeAdapter(FileLicense)
