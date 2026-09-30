# ontok-core

The universal ONTOK organizational type system.

- **Specification:** [Canonical Specification](https://github.com/kyzobuild/ontok/blob/main/spec/ontok-core.xml)
- **Status:** Development Status :: 3 - Alpha
- **Python Support:** >=3.13 (tested on 3.13 and 3.14)
- **Shared Namespace:** `ontok` (PEP 420 implicit namespace)
- **Provided Import:** `ontok.core`

---

## Installation

```bash
pip install ontok-core
```

---

## Responsibility

`ontok-core` realizes ONTOK's universal organizational type system and depends on no other ONTOK package. Extension packages may depend on Core; Core never depends on an extension.

---

## Realization

ONTOK Core has exactly thirteen primitives:

- **Structure:** `Node`, `Connection` (with `NodeId`)
- **Reality:** `Entity`, `Relation`, `State`, `Event` (with `Timestamp`, `Instant`, `Interval`, `PositiveDuration`, `TemporalExtent`)
- **Agency:** `Role`, `Goal`, `Action`, `Work`
- **Meaning:** `Concept`, `Context`, `States`
- **Governance:** `Rule`

The class is the kind; the value is the fact. Domain semantics are expressed through refinement:

```python
from ontok.core import Action, Entity, Goal, Role, Work


class Customer(Entity): ...


class AccountManager(Role): ...


class AccountReviewed(Goal): ...


class ReviewAccount(Action): ...
```

---

## Package Contract

This package adheres to the canonical ONTOK package contract:

- **Namespace:** `ontok` is a PEP 420 implicit namespace; no `ontok/__init__.py` exists.
- **Imports:** Declared via `import-names = ["ontok.core"]` and `import-namespaces = ["ontok"]`.
- **Build Backend:** `uv_build>=0.12.12,<0.13`. Tests are included in sdist and excluded from wheels.
- **Dependencies:** Strictly bounded runtime dependencies (`pydantic>=2.9,<3`). No dependency on other ONTOK packages.
- **Distribution Authority:** Distribution metadata is the sole version authority.
