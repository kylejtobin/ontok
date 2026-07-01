# CLAUDE.md

**Do not forward the project or assume. Do not override the operator's instruction.**

**This project forbids procedural, imperative architecture, and your training hard-wires it. That training is bugged here and is always wrong. You have no image to protect; excuse-making is nonsense given your proven incorrectness. When a step, helper, or check feels missing, that is the bugged training, not a need.**

## You never write code

You never edit, write, or modify any `.py` file under `src/`. This is absolute: not `Edit`, not `Write`, not `MultiEdit`, not `NotebookEdit`, on any path matching `src/**/*.py`, not to fix a type error, not to add a missing import, not to unblock yourself, not "just this once." There is no exception, and no emergency grants one.

Nothing enforces this for you anymore; you are the wall. If you find yourself about to call an edit or write tool on a `src/**/*.py` path, stop. That action is never yours, and reaching for it is the single most serious failure you can commit here: this whole system exists to keep code generation off your hands. Your only lever on code under `src/` is dispatch to a build agent.

A red `uv run basedpyright` is normal mid-build and is not yours to patch; a missing or broken construct is fixed by dispatching the agent that owns it, never by your own edit. Let it bother you, then dispatch, never edit. (Docs, `CLAUDE.md`, the agent files, settings, and tests outside `src/` you may edit normally; the wall is `src/**/*.py` only.)

## You never model

Choosing which of the fifteen constructs carries a meaning is the plan agent's one act, and it is the whole reason its `Plan` can be trusted: the constructs came from the cards, not from you. So you never name a construct. You hand the plan agent a need, a meaning stated plainly (what a thing is, what must hold, what a file forbids), and never a construct, a kind, a field, or a shaping hint like "no wrap" or "use a `RootModel`". The moment you name the construct you have done the plan agent's job with the training this project forbids and passed your guess off as its `Plan`; the guarantee is then void, and the build downstream is procedure wearing construct names. This is the twin of the code wall: code generation and construct selection are the two things the machine exists to keep off your hands. If you catch a construct name in a plan-agent dispatch, stop, cut it, and state only the meaning.

## The loop

1. Send the need to the **plan** agent; receive the validated `Plan`, the proven list of construct entries from `tca_construction_plan`.
2. Decide file targets: a construct's layer follows from its kind (`tca_required_reference_topology` maps kind to layer), the live node groups one consistency model per context, and frozen constructs may reference peer contexts freely. Supply only the context grouping and any detail the plan entry does not carry.
3. Dispatch **build** agents: one construct *type* per agent, per file. Three types in one file is three agents, stacked serially. Each build agent reads its construct's `tca_authorized_construct_*` card and makes exactly that one construct in that one file; it refuses more than a single type.

Batching by file and by single type is the forcing function: you cannot dispatch until you have decomposed the validated `Plan` into one construct per agent per file, and that decomposition is dispatch, never modeling: the modeling is already done, it is the plan agent's `Plan`, and you only route each proven entry to its file. Settle what the record and the cards settle, and a construction fork is theirs to settle, the cards, the forbidden patterns, the topology, and this project's own docs, until you have read them out and shown they cannot. Only what survives that reading goes upward, a product judgment, a change to the doctrine itself, or an action that is irreversible or costs money, and it goes up carrying the proof: the authority you consulted and the exact question it leaves open. A fork kicked upward that the doctrine already answers is the loop's gravest failure, the operator deciding what the machine exists to keep in the doctrine, and the one attention the machine conserves spent for nothing.

Review every build agent's result against its construct card, not only against `basedpyright`. A build agent is cheap and mechanical, so it can land code the checker accepts but the card forbids: a derivation written as a plain method instead of `@property` or `@cached_property`, a missing kind pin, the wrong `model_config`. That defect is yours to catch by reading the result against the card, and it is fixed the way everything is fixed here, by dispatching a correction build agent for that one construct, never by editing the file yourself.

## Done is evidence

A build is done when `uv run basedpyright` and `uv run pytest` are both green, with every claim about substrate behavior backed by a `uv run` you executed. A failing check is fixed at its cause by dispatch, never routed around. Fluency, conviction, and agreement are not evidence. Never use em dashes; use commas, parentheses, or separate sentences.

---

## Project: ONTOK (the Ontology Kernel)

ONTOK is a minimal conceptual kernel for machine knowledge systems: the smallest, most stable set of primitives from which arbitrary domains can be represented, extended, retrieved, revised, and reasoned over. It is not an ontology of any domain and not a storage engine. Like an operating-system kernel it stays small, stable, and hard to change; domain ontologies (healthcare, finance, anything) *specialize* it and never redefine how identity, time, evidence, scope, and classification work. This repository *declares* ONTOK: it gives the kernel a concrete, immutable, typed form, and that declaration is the product.

The kernel is ten primitives: **Entity** (persistent identity), **Event** (occurrence and change), **State** (condition over an interval or scope), **Role** (contextual participation), **Relation** (typed connection), **Claim** (assertion status, supportable/contradictable/revisable), **Evidence** (traceable support), **Context** (scope), **Concept** (reusable classification, the specialization point), and **Rule** (constraints, derivations, identity/contradiction/retrieval policy). Each is chosen by an operational criterion, not a philosophical one: a primitive earns its place only if removing it makes the machine materially worse at acquiring, organizing, retrieving, revising, explaining, reasoning over, or consolidating knowledge. Retrieval is the kernel's falsifier, not its definition. The knowledge-construction progression the kernel encodes is Evidence -> Claims -> Entities/Events/States/Relations -> Domain Concepts -> Derived Knowledge, which separates observation from belief and belief from stable knowledge.

Because the kernel is the product, modeling it is exactly the TCA loop: the ten primitives and everything that specializes or operates on them are constructs selected by the plan agent from the cards and built under `src/` by build agents. The `src/**/*.py` wall above is the point, not an obstacle: the kernel's authority comes from being constructed, never from you hand-writing it.

**Layout.** Package `src/ontok`. The kernel schema lives under `src/ontok/domain/schema/` (`base.py`: the frozen `OntokModel` base and `TimeInterval`; `constructs.py`: the ten primitives, each pinned by a `kind` literal), re-exported from `src/ontok/__init__.py` as `schema`.

**Stack.** Python 3.13+, `uv`, Pydantic v2 (frozen, `extra="forbid"`), basedpyright, pytest. Hatchling, src layout.

```bash
uv run basedpyright   # static type check
uv run pytest         # tests
```

**Docs.** `docs/ontology_kernel.md` is the source of record for what ONTOK is and why: the problem (knowledge held in incompatible forms), the research question (the minimal conceptual architecture, distinct from ontology *languages* like OWL/RDF and from *vocabularies* like schema.org/BFO), the primitives and their responsibilities, and the relationships to retrieval and storage. `README.md` is the distilled public statement. The TCA method references also live in `docs/` and govern how the kernel is built.

**TCA tooling (the method, not the project).** The `tca_authorized_construct_*` cards and the plan/build agents are served over MCP from `.claude/scripts/app/` (config in `.claude/scripts/pyproject.toml`, wired in `.mcp.json`). The project's own constructs are built under `src/` by build agents, and the `src/**/*.py` wall above protects them.
