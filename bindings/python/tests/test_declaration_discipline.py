"""Guard the construction discipline independently of specific business examples."""

import ast
import json
import subprocess
import sys
import typing
from pathlib import Path
from typing import TypeAliasType, TypedDict, TypeVar, cast, get_args, get_origin

import pytest
from pydantic import BaseModel

import organization_model
from organization_model.examples import CLOSED_MODELS

assert organization_model.__file__ is not None
PACKAGE = Path(organization_model.__file__).parent
PROJECT = Path(__file__).resolve().parents[1]
DECLARATION_MODULES = ("scalars.py", "work.py", "value.py", "examples.py")
SEMANTIC_TARGETS = (
    "Purpose",
    "Activity",
    "Process",
    "Role",
    "Authority",
    "Rule",
    "Decision",
    "Event",
    "Interaction",
    "Outcome",
    "Value",
    "Economic",
    "Time",
    "Quality",
    "Risk",
    "Capability",
    "HumanWelfare",
    "Relationships",
    "Resources",
)
PROCEDURAL_CONSTRUCTORS = {
    "create_model",
    "field_validator",
    "model_validator",
    "BeforeValidator",
    "AfterValidator",
    "PlainValidator",
    "WrapValidator",
}


@pytest.mark.parametrize("module_name", DECLARATION_MODULES)
def test_model_declarations_do_not_hide_procedural_validation(module_name: str) -> None:
    tree = ast.parse((PACKAGE / module_name).read_text())
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            violations.append(f"procedure at line {node.lineno}")
        if isinstance(node, ast.Call):
            target = node.func
            name = target.id if isinstance(target, ast.Name) else ""
            if isinstance(target, ast.Attribute):
                name = target.attr
            if name in PROCEDURAL_CONSTRUCTORS:
                violations.append(f"{name} at line {node.lineno}")
            if any(keyword.arg == "default_factory" for keyword in node.keywords):
                violations.append(f"computed default at line {node.lineno}")
    assert not violations, f"{module_name}: {violations}"


@pytest.mark.parametrize("module_name", DECLARATION_MODULES)
def test_declared_fields_and_aliases_have_no_any_escape_hatch(module_name: str) -> None:
    tree = ast.parse((PACKAGE / module_name).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            annotation = node.annotation
        elif isinstance(node, ast.TypeAlias):
            annotation = node.value
        else:
            continue
        for constituent in ast.walk(annotation):
            assert not (isinstance(constituent, ast.Name) and constituent.id == "Any"), (
                f"{module_name}:{constituent.lineno} erases a declared type"
            )
            assert not (isinstance(constituent, ast.Attribute) and constituent.attr == "Any"), (
                f"{module_name}:{constituent.lineno} erases a declared type"
            )


def assert_immutable_annotation(
    annotation: object,
    visited: set[type[BaseModel]],
    bindings: dict[TypeVar, object] | None = None,
) -> None:
    bindings = {} if bindings is None else bindings
    while isinstance(annotation, TypeVar):
        assert annotation in bindings, "closed model contains an unbound type variable"
        annotation = bindings[annotation]
    assert annotation is not typing.Any, "closed model contains Any"
    assert annotation is not object, "closed model contains an unconstrained object payload"
    if isinstance(annotation, TypeAliasType):
        assert not annotation.__type_params__, "generic alias has no concrete arguments"
        assert_immutable_annotation(annotation.__value__, visited, bindings)
        return
    origin = get_origin(annotation)
    if isinstance(origin, TypeAliasType):
        local_bindings = dict(bindings)
        for parameter, argument in zip(origin.__type_params__, get_args(annotation), strict=True):
            assert isinstance(parameter, TypeVar), "unsupported variadic alias parameter"
            local_bindings[parameter] = argument
        assert_immutable_annotation(origin.__value__, visited, local_bindings)
        return
    assert origin not in (dict, list, set), f"mutable model constituent: {annotation!r}"
    assert annotation not in (dict, list, set), f"untyped mutable constituent: {annotation!r}"
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        model = annotation
        if model in visited:
            return
        visited.add(model)
        assert model.model_config.get("frozen") is True, model.__name__
        for field in model.model_fields.values():
            assert_immutable_annotation(field.annotation, visited, bindings)
    for argument in get_args(annotation):
        assert_immutable_annotation(argument, visited, bindings)


def test_closed_examples_have_immutable_constituents() -> None:
    assert CLOSED_MODELS, "Concrete declarations are needed to verify constituent guarantees"
    visited: set[type[BaseModel]] = set()
    for model in CLOSED_MODELS:
        assert_immutable_annotation(model, visited)


def test_all_nineteen_semantic_targets_are_public_once() -> None:
    for name in SEMANTIC_TARGETS:
        assert organization_model.__all__.count(name) == 1, name
        model = getattr(organization_model, name)
        assert isinstance(model, type) and issubclass(model, BaseModel), name


class DiagnosticPosition(TypedDict):
    line: int


class DiagnosticRange(TypedDict):
    start: DiagnosticPosition


class Diagnostic(TypedDict):
    severity: str
    rule: str
    range: DiagnosticRange


class CheckerResult(TypedDict):
    generalDiagnostics: list[Diagnostic]


def test_semantic_bounds_reject_invalid_type_declarations(tmp_path: Path) -> None:
    source = """from typing import Literal
from organization_model.examples import (
    BusinessNeed, Person, RefundPrerequisites, RefundPurpose, RefundService, SupportContext,
)
from organization_model.value import Benefit, Economic, Fitness
from organization_model.work import Interaction, Permission, Process, Responsibility

class WrongProcess(Process[RefundPrerequisites, Person], frozen=True):
    pass

type NonEconomicAssessment = Benefit[Fitness[RefundPurpose, Literal["met"]]]
class WrongEconomic(Economic[RefundService, BusinessNeed, NonEconomicAssessment], frozen=True):
    pass

class WrongInteraction(Interaction[Person], frozen=True):
    pass

class WrongResponsibility(Responsibility, frozen=True):
    root: Permission[SupportContext, RefundPurpose]
"""
    declaration = tmp_path / "invalid_declarations.py"
    declaration.write_text(source)
    checked = subprocess.run(
        [
            sys.executable,
            "-m",
            "basedpyright",
            "--project",
            str(PROJECT / "pyproject.toml"),
            "--outputjson",
            str(declaration),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert checked.returncode == 1, checked.stdout + checked.stderr
    report = cast("CheckerResult", json.loads(checked.stdout))
    diagnostics = report["generalDiagnostics"]
    actual = {
        (diagnostic["range"]["start"]["line"], diagnostic["rule"])
        for diagnostic in diagnostics
        if diagnostic["severity"] == "error"
    }
    expected: set[tuple[int, str]] = set()
    for number, line in enumerate(source.splitlines()):
        if line.startswith(("class WrongProcess", "class WrongEconomic", "class WrongInteraction")):
            expected.add((number, "reportInvalidTypeArguments"))
        if line.strip().startswith("root: Permission"):
            expected.add((number, "reportIncompatibleVariableOverride"))
    assert len(expected) == 4
    assert actual == expected, checked.stdout
