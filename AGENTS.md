# AGENTS.md

ONTOK is a modular declarative semantic language for making organizational meaning explicit, portable, and executable. This repository contains ONTOK Core, its modules, and their documentation. Each module is its own specification.

## Project knowledge

`wiki/` is what this project knows that the code does not say, and the project-knowledge protocol is always on. At the start of every task orient from `wiki/index.md` and read only the pages the task needs; open a directory index before a page. Give delegated agents the pages they need and require their report to name evidence, contradictions, and a knowledge delta. While working, notice what becomes durable knowledge. Before finishing, reconcile it into the page that owns it, or say there is no delta. The wiki never restates a source file. Read `wiki/architecture/<module>.md` before any structural change to that module; state the change as its design, by construct, before any task list or code; and edit the page's section and the code in the same commit. A page states what is and carries no status: a design becomes a page only in the commit that makes every sentence of it true. The standard for every page is `.agents/skills/project-knowledge`.

## Start with the model

Do not infer ONTOK's semantics from implementation convenience. The module defines the language; a program refines it.

ONTOK Core has exactly thirteen primitives:

```text
Node
Connection
Entity
Relation
State
Event
Role
Goal
Action
Work
Concept
Context
Rule
```

Everything else in Core either supports those primitives or is constructed from them. Do not add a primitive merely because a useful capability needs representation.

The class is the kind. Domain semantics are expressed through refinement:

```python
class Invoice(Entity): ...


class ReportsTo(Relation): ...


class HireApproved(Event): ...
```

Do not introduce instance-level `type`, `kind`, `TypeId`, URI discriminator, or registry fields to simulate subclassing unless the specification explicitly requires one for semantics other than class identity.

## Preserve the distinctions

ONTOK deliberately distinguishes reality, agency, meaning, and governance. Do not collapse those distinctions for implementation convenience.

An `Event` is a durable memorial of an occurrence. Temporal sequence does not imply causation; `Causation` is a `Relation` between Events.

A `Concept` represents meaning and alignment. It is not a type registry. For example, a declaration such as `cust_no` may mean the Concept `Customer`, and independently developed Concepts may align with one another.

`Context` expresses the conditions under which meaning or action applies. `Rule` governs Action within Context.

## Semantic Topology

Semantic Topology is part of ONTOK Core's meaning capability, but it is not a thirteenth primitive.

It is the evolving organizational structure formed among Concepts. Semantic relationships such as equivalence, broader/narrower meaning, relatedness, close matching, and overlap are represented through refinements of `Relation` whose endpoints are Concepts.

A topology belongs to the organization rather than to a source system. It may reconcile concepts originating in different applications, schemas, graphs, documents, standards, or intelligent systems without requiring those sources to adopt one canonical model.

Semantic Topology evolves through explicit validated change. Models may infer or propose semantic structure; software owns validation, durable state, authority, and revision.

## Keep Core small

Universal organizational semantics belong in `ontok-core`. Reusable domain or standards-specific semantics belong in modules. Organization-specific semantics belong in organization-specific refinements.

`ontok-vsm` and `ontok-scim` extend Core through explicit one-way dependencies. Do not move module concepts into Core simply because they are useful.

## The module is the specification

Each module's meaning is stated once, in the module: the class is the kind, the docstring is the meaning, the fields are the mandatory dependencies. No specification is written beside it. A portable rendering, for another language's realization or for interchange, is projected from the module when a consumer needs one and is never kept in the repository.

Prefer the smallest model that makes the intended distinction explicit. Avoid generic metadata bags, speculative abstraction layers, duplicate representations, and convenience fields whose only purpose is to recover meaning already carried by the class structure.

## Python

The Python realization lives under `packages/python/` as a `uv` workspace using the shared `ontok` namespace.

```text
ontok-core  → ontok.core
ontok-vsm   → ontok.vsm
ontok-scim  → ontok.scim
```

Use strict Pydantic models. Preserve immutability and `extra="forbid"` unless the semantics explicitly require otherwise. Prefer construction-time invalidity over conventions documented only in prose.

Tests should prove semantic invariants, not merely exercise lines of code.

## Standards

ONTOK may align or project to standards including RDF, OWL, SHACL, SKOS, and SCIM where they provide useful interoperability. Those standards do not automatically define ONTOK's programming model.

Use standards as semantic and interchange assets, not as reasons to import unnecessary complexity into Core.

## Before changing the model

Ask what semantic distinction the change makes explicit, whether an existing primitive already expresses it, whether refinement is sufficient, whether the capability belongs in Core or a module, and whether the change preserves ONTOK's ability to remain implementation-independent.

If the answer requires inventing a second way to express something ONTOK already knows, the design is probably wrong.
