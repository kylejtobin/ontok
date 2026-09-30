import re
import tomllib
from functools import cached_property
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class DistributionName(RootModel[str]):
    """The package distribution name, starting with ontok-."""

    root: str = Field(pattern=r"^ontok-[a-z0-9-]+$")


class ModuleName(RootModel[str]):
    """The Python subpackage name under the shared ontok namespace."""

    root: str = Field(pattern=r"^[a-z0-9_]+$")


class PackageVersion(RootModel[str]):
    """A semantic package version string."""

    root: str = Field(pattern=r"^\d+\.\d+\.\d+$")


class PackageDescription(RootModel[str]):
    """A non-empty one-line description of the package."""

    root: str = Field(min_length=1)


class TemplateTokens(BaseModel):
    """The complete set of replacement tokens required to render an ONTOK module."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    distribution_name: DistributionName
    module_name: ModuleName
    version: PackageVersion
    description: PackageDescription
    status: Literal[
        "1 - Planning",
        "2 - Pre-Alpha",
        "3 - Alpha",
        "4 - Beta",
        "5 - Production/Stable",
    ]
    keywords: tuple[str, ...] = Field(min_length=1)
    dependencies: tuple[str, ...] = ()
    specification_url: str = Field(pattern=r"^https://github\.com/kylejtobin/ontok/.+$")

    @cached_property
    def replacements(self) -> dict[str, str]:
        kw_lines = ",\n    ".join(f'"{k}"' for k in self.keywords)
        dep_lines = ",\n    ".join(f'"{d}"' for d in self.dependencies)
        return {
            "__DISTRIBUTION_NAME__": self.distribution_name.root,
            "__MODULE_NAME__": self.module_name.root,
            "__VERSION__": self.version.root,
            "__DESCRIPTION__": self.description.root,
            "__STATUS__": self.status,
            '"__KEYWORDS__"': kw_lines,
            '"__DEPENDENCIES__"': dep_lines,
            "__KEYWORDS__": kw_lines,
            "__DEPENDENCIES__": dep_lines,
            "__SPECIFICATION_URL__": self.specification_url,
        }


class ProjectUrls(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    Homepage: str
    Repository: str
    Issues: str
    Specification: str


class AuthorInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    email: str


class ProjectMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    name: str
    version: str
    description: str
    readme: str
    requires_python: str = Field(validation_alias="requires-python")
    license: str
    license_files: list[str] = Field(validation_alias="license-files")
    authors: list[AuthorInfo]
    keywords: list[str]
    classifiers: list[str]
    dependencies: list[str]
    urls: ProjectUrls
    import_names: list[str] = Field(validation_alias="import-names")
    import_namespaces: list[str] = Field(validation_alias="import-namespaces")


class BuildSystemMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    requires: list[str]
    build_backend: str = Field(validation_alias="build-backend")


class UvBuildBackendSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    module_name: str = Field(validation_alias="module-name")
    source_include: list[str] = Field(validation_alias="source-include")


class ToolUvSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", populate_by_name=True)

    build_backend: UvBuildBackendSettings = Field(validation_alias="build-backend")


class ToolSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    uv: ToolUvSettings


class RenderedPackageMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", populate_by_name=True)

    project: ProjectMetadata
    build_system: BuildSystemMetadata = Field(validation_alias="build-system")
    tool: ToolSettings


class PackageTemplate(BaseModel):
    """The canonical non-publishable package template on disk."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: Path

    @cached_property
    def pyproject_file(self) -> Path:
        return self.root / "pyproject.toml"

    @cached_property
    def readme_file(self) -> Path:
        return self.root / "README.md"

    @cached_property
    def license_file(self) -> Path:
        return self.root / "LICENSE"

    @cached_property
    def notice_file(self) -> Path:
        return self.root / "NOTICE"

    @cached_property
    def source_module_dir(self) -> Path:
        return self.root / "src" / "ontok" / "__MODULE_NAME__"

    @cached_property
    def init_file(self) -> Path:
        return self.source_module_dir / "__init__.py"

    @cached_property
    def py_typed_file(self) -> Path:
        return self.source_module_dir / "py.typed"

    @cached_property
    def namespace_init_file(self) -> Path:
        return self.root / "src" / "ontok" / "__init__.py"

    @cached_property
    def tests_dir(self) -> Path:
        return self.root / "tests"

    @cached_property
    def conftest_file(self) -> Path:
        return self.tests_dir / "conftest.py"

    def render(self, destination: Path, tokens: TemplateTokens) -> "RenderedPackage":
        destination.mkdir(parents=True, exist_ok=True)
        replacements = tokens.replacements

        for path in self.root.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self.root)
                rel_str = str(rel_path)
                for token, val in replacements.items():
                    rel_str = rel_str.replace(token, val)
                dest_file = destination / rel_str
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                content = path.read_text(encoding="utf-8")
                for token, val in replacements.items():
                    content = content.replace(token, val)
                dest_file.write_text(content, encoding="utf-8")

        return RenderedPackage(root=destination, tokens=tokens)


class RenderedPackage(BaseModel):
    """A concrete package rendered from the template in a target directory."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: Path
    tokens: TemplateTokens

    @cached_property
    def pyproject_file(self) -> Path:
        return self.root / "pyproject.toml"

    @cached_property
    def readme_file(self) -> Path:
        return self.root / "README.md"

    @cached_property
    def license_file(self) -> Path:
        return self.root / "LICENSE"

    @cached_property
    def notice_file(self) -> Path:
        return self.root / "NOTICE"

    @cached_property
    def module_dir(self) -> Path:
        return self.root / "src" / "ontok" / self.tokens.module_name.root

    @cached_property
    def init_file(self) -> Path:
        return self.module_dir / "__init__.py"

    @cached_property
    def py_typed_file(self) -> Path:
        return self.module_dir / "py.typed"

    @cached_property
    def namespace_init_file(self) -> Path:
        return self.root / "src" / "ontok" / "__init__.py"

    @cached_property
    def tests_dir(self) -> Path:
        return self.root / "tests"

    @cached_property
    def parsed_pyproject(self) -> dict[str, object]:
        return tomllib.loads(self.pyproject_file.read_text(encoding="utf-8"))

    @cached_property
    def metadata(self) -> RenderedPackageMetadata:
        return RenderedPackageMetadata.model_validate(self.parsed_pyproject)

    @cached_property
    def unreplaced_tokens(self) -> tuple[str, ...]:
        found: list[str] = []
        token_pattern = re.compile(r"__[A-Z0-9_]+__")
        for path in self.root.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                found.extend(token_pattern.findall(text))
        return tuple(sorted(set(found)))
