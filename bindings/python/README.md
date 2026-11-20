# ontok-python

The Python binding for Ontok. Ontok defines the semantics (see `rfc/ontok.md`); this package expresses them through native Pydantic `BaseModel` and `RootModel`, generics, unions, composition, and inheritance. It does not redefine them.

- `ontok.work` and `ontok.value` hold the nineteen kinds and the constituent types this binding uses to express them. The generic declarations are authoring templates from which a domain declares concrete models.
- `ontok.scalars` holds scalar constraints, `Money`, and `Quantity`. These are conveniences for domain models. They are not Ontok kinds.
- `ontok.examples` is one illustrative domain, a refund service. Its restrictions are local policy, not Ontok requirements.

Concrete domain models follow the established approach: meaningful distinctions are types, dependencies are required constituents, alternatives are unions of complete cases, specialization is inheritance and narrowing, and invalid combinations are structurally unrepresentable without procedural validation.

```bash
uv run pytest -q
uv run basedpyright
uv run ruff check src tests
```
