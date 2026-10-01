# ontok-core

The universal ONTOK organizational type system: fourteen primitives that say what kinds of things an organization contains, realized as strict, frozen Pydantic models in the `ontok` namespace.

- **Import:** `ontok.core`
- **Python:** 3.13 or later
- **Depends on:** `pydantic>=2.9,<3`, and no other ONTOK package
- **Status:** alpha
- **Architecture:** [wiki/architecture/ontok-core.md](https://github.com/kylejtobin/ontok/blob/main/wiki/architecture/ontok-core.md)

## Install

```bash
pip install "ontok-core @ git+https://github.com/kylejtobin/ontok.git#subdirectory=packages/python/ontok-core"
```

## Use

```python
from ontok.core import Action, Entity, Goal, NodeId, Role


class Customer(Entity): ...


class AccountManager(Role): ...


class AccountReviewed(Goal): ...


class ReviewAccount(Action): ...


review = ReviewAccount(
    id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2b"),
    role=AccountManager(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2c")),
    goal=AccountReviewed(id=NodeId("0192a1b2-c3d4-7e5f-8a6b-7c8d9e0f1a2d")),
)
```

The class is the kind; the value is the fact; a `ValidationError` is the absence of a fact. The module is its own specification.

## Package

`ontok` is a PEP 420 implicit namespace: no `ontok/__init__.py` exists in any distribution. The wheel carries the source, `py.typed`, `LICENSE`, and `NOTICE`; distribution metadata is the sole version authority.
