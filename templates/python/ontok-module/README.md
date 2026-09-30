# __DISTRIBUTION_NAME__

__DESCRIPTION__

- **Specification:** [Canonical Specification](__SPECIFICATION_URL__)
- **Status:** Development Status :: __STATUS__
- **Python Support:** >=3.13 (tested on 3.13 and 3.14)
- **Shared Namespace:** `ontok` (PEP 420 implicit namespace)
- **Provided Import:** `ontok.__MODULE_NAME__`

---

## Installation

```bash
pip install __DISTRIBUTION_NAME__
```

---

## Responsibility

`__DISTRIBUTION_NAME__` realizes the domain semantics defined in its specification under `ontok.__MODULE_NAME__`.

---

## Package Contract

This package adheres to the canonical ONTOK package contract:

### 1. Required Files
- `pyproject.toml` — Standards-compliant build and project metadata.
- `README.md` — Package documentation linking to canonical specification and describing status.
- `LICENSE` — Apache License 2.0.
- `NOTICE` — Copyright 2026 Kyle Tobin.
- `src/ontok/__MODULE_NAME__/__init__.py` — Package entrypoint (empty for deferred modules until real semantics exist).
- `src/ontok/__MODULE_NAME__/py.typed` — PEP 561 marker declaring typed distribution.
- `tests/` — Test tree included in source distribution and excluded from wheels.

### 2. Namespace and Imports
- **Shared Namespace:** `ontok` is a PEP 420 implicit namespace. No `ontok/__init__.py` may exist in any distribution.
- **Import Namespace:** Declared via `import-namespaces = ["ontok"]` in `pyproject.toml`.
- **Import Name:** Declared via `import-names = ["ontok.__MODULE_NAME__"]` in `pyproject.toml`.

### 3. Build Configuration
- **Build Backend:** `uv_build>=0.12.12,<0.13`
- **Module Name:** `ontok.__MODULE_NAME__`
- **Wheel Contents:** Source tree, `py.typed`, `LICENSE`, `NOTICE`, and distribution metadata. Tests are excluded.
- **Source Distribution Contents:** Source tree, tests (`tests/**`), `README.md`, `LICENSE`, `NOTICE`, and `pyproject.toml`.

### 4. Dependencies
- Universal kernel dependencies: `ontok-core>=0.1.0,<0.2.0`.
- Published dependencies must never contain workspace paths or editable references.
- All dependencies must declare upper bounds.

### 5. Documentation
- Package documentation must state installation, Python support, responsibility, namespace, and status.
- Implemented packages must include one minimal public-API example.
- Deferred packages must explicitly state that they are not release candidates.
- Specification links must be absolute canonical GitHub links.

---

## Workspace Development Instructions

When developing this package inside the ONTOK workspace:

1. Place the package directory under `packages/python/__DISTRIBUTION_NAME__`.
2. Bind local dependencies to the workspace in `pyproject.toml`:
   ```toml
   [tool.uv.sources]
   ontok-core = { workspace = true }
   ```
3. Run `uv lock` from the workspace root to register the member.
4. Verify that build artifacts (`uv build --package __DISTRIBUTION_NAME__ --no-sources`) do not contain workspace paths or editable references.

---

## Creation Checklist

When creating a new ONTOK module:

- [ ] **1. Realization:** Render this template into `packages/python/__DISTRIBUTION_NAME__`. Declare the module's kinds under `src/ontok/__MODULE_NAME__/` through the python-development standard; the module is its own specification.
- [ ] **2. Architecture page:** Write `wiki/architecture/__DISTRIBUTION_NAME__.md` stating the module as it is.
- [ ] **3. Semantic Test:** Write tests under `tests/` proving domain invariants through value construction, not substrate trivia.
- [ ] **4. Artifact Test:** Build the wheel and source distribution with `uv build --package __DISTRIBUTION_NAME__ --no-sources`. Prove that the wheel excludes tests, the sdist includes tests, `py.typed` is present, and no `ontok/__init__.py` exists.
- [ ] **5. Workspace Registration:** Register the package in the root `pyproject.toml` workspace members, update `uv.lock`, and ensure all workspace quality gates pass.
