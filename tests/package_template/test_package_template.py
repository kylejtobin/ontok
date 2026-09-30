from pathlib import Path

from pytest import fail

from .model import (
    AuthorInfo,
    BuildSystemMetadata,
    DistributionName,
    ModuleName,
    PackageDescription,
    PackageTemplate,
    PackageVersion,
    ProjectMetadata,
    ProjectUrls,
    TemplateTokens,
    ToolSettings,
    ToolUvSettings,
    UvBuildBackendSettings,
)


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical_template() -> PackageTemplate:
    template_path = _workspace_root() / "templates" / "python" / "ontok-module"
    return PackageTemplate(root=template_path)


def _sample_tokens() -> TemplateTokens:
    return TemplateTokens(
        distribution_name=DistributionName("ontok-sample"),
        module_name=ModuleName("sample"),
        version=PackageVersion("0.0.0"),
        description=PackageDescription("Sample module realizing test semantics."),
        status="1 - Planning",
        keywords=("ontok", "sample"),
        dependencies=("ontok-core>=0.1.0,<0.2.0",),
        specification_url="https://github.com/kylejtobin/ontok/blob/main/spec/ontok-sample.xml",
    )


def test_template_directory_invariants() -> None:
    template = _canonical_template()
    root = _workspace_root()

    if not template.root.is_dir():
        fail(f"Template directory does not exist: {template.root}")

    if (root / "packages" / "python") in template.root.parents:
        fail("Template must live strictly outside packages/python.")

    expected_files = (
        template.pyproject_file,
        template.readme_file,
        template.license_file,
        template.notice_file,
        template.init_file,
        template.py_typed_file,
        template.conftest_file,
    )
    missing = [str(f) for f in expected_files if not f.is_file()]
    if missing:
        fail(f"Template is missing required files: {missing}")

    if template.namespace_init_file.exists():
        fail("Template must not contain src/ontok/__init__.py (violates PEP 420).")


def test_deterministic_template_rendering(tmp_path: Path) -> None:
    template = _canonical_template()
    tokens = _sample_tokens()
    dest = tmp_path / "ontok-sample"

    rendered = template.render(dest, tokens)

    if rendered.unreplaced_tokens:
        fail(f"Unreplaced tokens found in rendered package: {rendered.unreplaced_tokens}")

    rendered_files = (
        rendered.pyproject_file,
        rendered.readme_file,
        rendered.license_file,
        rendered.notice_file,
        rendered.init_file,
        rendered.py_typed_file,
    )
    missing = [str(f) for f in rendered_files if not f.is_file()]
    if missing:
        fail(f"Rendered package missing required files: {missing}")

    if rendered.namespace_init_file.exists():
        fail("Rendered package must not contain ontok/__init__.py (violates PEP 420).")

    if not rendered.tests_dir.is_dir():
        fail("Rendered package missing tests/ directory.")

    license_text = rendered.license_file.read_text(encoding="utf-8")
    if "Apache License" not in license_text:
        fail("Rendered package LICENSE does not contain Apache License text.")

    notice_text = rendered.notice_file.read_text(encoding="utf-8")
    if "Kyle Tobin" not in notice_text:
        fail("Rendered package NOTICE does not contain copyright holder Kyle Tobin.")


def test_rendered_package_metadata_contract(tmp_path: Path) -> None:
    template = _canonical_template()
    tokens = _sample_tokens()
    dest = tmp_path / "ontok-sample"

    rendered = template.render(dest, tokens)
    meta = rendered.metadata

    expected_project = ProjectMetadata(
        name=tokens.distribution_name.root,
        version=tokens.version.root,
        description=tokens.description.root,
        readme="README.md",
        requires_python=">=3.13",
        license="Apache-2.0",
        license_files=["LICENSE", "NOTICE"],
        authors=[AuthorInfo(name="Kyle Tobin", email="tobin.kyle@gmail.com")],
        keywords=list(tokens.keywords),
        classifiers=[
            f"Development Status :: {tokens.status}",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.13",
            "Programming Language :: Python :: 3.14",
            "Typing :: Typed",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Libraries",
        ],
        dependencies=list(tokens.dependencies),
        urls=ProjectUrls(
            Homepage="https://github.com/kylejtobin/ontok",
            Repository="https://github.com/kylejtobin/ontok",
            Issues="https://github.com/kylejtobin/ontok/issues",
            Specification=tokens.specification_url,
        ),
        import_names=[f"ontok.{tokens.module_name.root}"],
        import_namespaces=["ontok"],
    )
    if meta.project != expected_project:
        fail(f"Project metadata mismatch:\nExpected: {expected_project}\nGot: {meta.project}")

    expected_build = BuildSystemMetadata(
        requires=["uv_build>=0.12.12,<0.13"],
        build_backend="uv_build",
    )
    if meta.build_system != expected_build:
        fail(f"Build system mismatch:\nExpected: {expected_build}\nGot: {meta.build_system}")

    expected_tool = ToolSettings(
        uv=ToolUvSettings(
            build_backend=UvBuildBackendSettings(
                module_name=f"ontok.{tokens.module_name.root}",
                source_include=["tests/**"],
            )
        )
    )
    if meta.tool.uv.build_backend != expected_tool.uv.build_backend:
        fail(f"Tool settings mismatch:\nExpected: {expected_tool}\nGot: {meta.tool}")


def test_rendered_readme_contents(tmp_path: Path) -> None:
    template = _canonical_template()
    tokens = _sample_tokens()
    dest = tmp_path / "ontok-sample"

    rendered = template.render(dest, tokens)
    readme = rendered.readme_file.read_text(encoding="utf-8")

    required_snippets = (
        "pip install ontok-sample",
        tokens.specification_url,
        "Package Contract",
        "Workspace Development Instructions",
        "Creation Checklist",
        "ontok-core = { workspace = true }",
    )
    missing = [s for s in required_snippets if s not in readme]
    if missing:
        fail(f"README missing required contract sections: {missing}")


def test_rendered_package_pep420_filesystem_layout(tmp_path: Path) -> None:
    template = _canonical_template()
    tokens = _sample_tokens()
    dest = tmp_path / "ontok-sample"

    rendered = template.render(dest, tokens)

    # PEP 420 layout invariants
    # 1. Subpackage directory must exist under src/ontok/<module>
    if not rendered.module_dir.is_dir():
        fail(f"Subpackage directory {rendered.module_dir} does not exist.")

    # 2. Subpackage must provide __init__.py and py.typed
    if not rendered.init_file.is_file():
        fail(f"Subpackage {rendered.init_file} does not exist.")

    if not rendered.py_typed_file.is_file():
        fail(f"Subpackage {rendered.py_typed_file} does not exist.")

    # 3. Namespace parent directory must exist under src/ontok
    namespace_dir = rendered.root / "src" / "ontok"
    if not namespace_dir.is_dir():
        fail("Namespace parent directory src/ontok does not exist.")

    # 4. Namespace directory must NOT have __init__.py
    if rendered.namespace_init_file.exists():
        fail("PEP 420 violation: src/ontok/__init__.py must not exist.")

    # 5. Must not be inside workspace packages/python
    workspace_packages = _workspace_root() / "packages" / "python"
    if workspace_packages in rendered.root.parents:
        fail("Rendered package must be isolated and not part of workspace members.")
