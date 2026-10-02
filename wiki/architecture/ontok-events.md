---
type: Architecture
title: ontok-events
description: How event sourcing is composed as refinements of Core, how a fact comes to exist in it, and why each choice is what it is.
generated:
  by: claude-code/claude-fable-5-1
  at: 2026-10-01T22:00:00Z
sources:
  - id: package
    resource: ../../packages/python/ontok-events/src/ontok/events
    title: Events realization
  - id: distribution
    resource: ../../packages/python/ontok-events/pyproject.toml
    title: Events distribution
  - id: core
    resource: ./ontok-core.md
    title: The kinds Events refines
verified:
  by: claude-code/claude-fable-5-1
  at: 2026-10-02T00:30:00Z
  how: every quality scenario constructed or refused against ontok.events; the import-linter layers contract kept with ontok.nats above ontok.events above ontok.core
---

# ontok-events

Events is event sourcing stated in ONTOK: an organization's memory of what occurred, and its work upon that memory, as refinements of Core's primitives. It declares the things, a stream, a version, an occurrence, an event, an expected version, a condition, a read model, a subscription, a checkpoint, a delivery, and the actions upon them with the outcome each can have. It performs no effect. The actions and their outcomes are its whole interface: a provider realizes Events by holding one interpreter per action that constructs that action's outcome from the provider's own replies. Read this page before any structural change and edit the section the change lands in, in the same commit as the code.

## Constraints

- Every declaration is a refinement of a Core primitive or a form of the python-development standard, and carries Core's mandatory configuration unchanged.
- Events depends on `ontok-core` and Pydantic and on nothing else. No declaration names a provider, a transport, or an application.
- Events sits above Core and below every provider in the workspace's import-linter layers contract.
- An event's stream is referenced by `NodeId`; a stream's events are not its constituents.
- `Event.occurrence` and `State.prior` are `SerializeAsAny`: an organization's refinement renders whole, and only the organization's kind constructs it back.
- `Delivery` inherits `action` typed `Action`. That the action is a `Subscription` is not established by construction.
- The occurrences of one `Append` share its stream. That agreement is not established by construction.
- Python 3.14 or later; `pydantic>=2.9,<3`.

## Context

```mermaid
C4Context
  Person(organization, "The organization", "Refines Occurrence, Subscription, and State into the kinds it has")
  System(events, "ontok-events", "Event sourcing as refinements of Core: the things, the actions, the outcomes")
  System_Ext(core, "ontok-core", "The fourteen primitives Events refines")
  System_Ext(provider, "Provider module", "One interpreter per action, constructing its outcome from the provider's replies; ontok-nats first")
  System_Ext(programs, "Organizational programs", "Construct actions and fold outcomes at their composition root")
  Rel(events, core, "Refines")
  Rel(provider, events, "Realizes")
  Rel(organization, events, "Refines")
  Rel(programs, events, "Construct")
```

## Building blocks

```mermaid
classDiagram
  class Version { root: int ≥ 0 }
  class Position { root: int ≥ 0 }
  class Expectation { NO_STREAM; ANY }
  class AtVersion { version: Version }
  class VersionMismatch { expected: AtVersion | NO_STREAM }
  class VersionMismatchAt { actual: AtVersion | NO_STREAM }
  class Stream
  class Occurrence
  class Event { occurrence: Occurrence; stream: NodeId; position: Position }
  class Events { root: tuple~Event~ ≥ 1 }
  class Occurrences { root: tuple~Occurrence~ ≥ 1 }
  class StateIdentity { stream: NodeId; version: Version }
  class DeliveryIdentity { subscription: NodeId; event: NodeId; attempt: Attempt }
  class DispositionIdentity { delivery: NodeId; end: End }
  class IdentityInterpreter { action: Identity; derive; execute() NodeId }
  class Append { stream: NodeId; expected: ExpectedVersion; occurrences: Occurrences }
  class Read { stream: NodeId }
  class Initial { stream: NodeId; version() }
  class State { prior: Initial | State; event: Event; version() }
  class ReadModel { state: States; position: Position; persistence() }
  class PersistReadModel { read_model: ReadModel }
  class ReadModelLookup { id: NodeId }
  class NoReadModel { id: NodeId }
  class Start { BEGINNING; NOW }
  class FromPosition { position: Position }
  class Subscription { begins: FromPosition | Start }
  class StreamSubscription { stream: NodeId }
  class Attempt { root: int ≥ 1 }
  class Delivery { event: Event; attempt: Attempt }
  class Outcome { COMPLETE; RETURNED; PARKED }
  class Ending { delivery: Delivery; outcome: Outcome }
  class Disposition { delivery: Delivery; outcome: Outcome }
  class DispositionIdentity { delivery: NodeId; outcome: Outcome }
  class End { ACKNOWLEDGE; REJECT; PARK }
  class Ending { delivery: Delivery; end: End }
  class Disposition { delivery: Delivery; end: End }
  core_Entity <|-- Stream
  core_Entity <|-- ReadModel
  core_Event <|-- Occurrence
  core_State <|-- Initial
  core_State <|-- State
  core_Action <|-- Append
  core_Action <|-- Read
  core_Action <|-- Subscription
  Subscription <|-- StreamSubscription
  core_Work <|-- Delivery
  core_State <|-- Disposition
  VersionMismatch <|-- VersionMismatchAt
  core_Event <|-- Disposition
```

The unions: `ExpectedVersion` is `AtVersion | Expectation`; `StartingPoint` is `FromPosition | Start`; `Identity` is `StateIdentity | DeliveryIdentity | DispositionIdentity`. One file holds each meaning: `position`, `value`, `stream`, `event`, `append`, `read`, `state`, `read_model`, `subscription`, `delivery`, `identity`.

The interface, one row per action:

| Action | Outcome |
|--------|---------|
| `Append` | `AppendOutcome`: `Events \| VersionMismatch` |
| `Read` | `ReadOutcome`: `Events \| Literal[Expectation.NO_STREAM]` |
| `Subscription` | the `Subscription` |
| `Ending` | the `Disposition` |
| `PersistReadModel` | the `ReadModel` |
| `ReadModelLookup` | `LookupOutcome`: `ReadModel \| NoReadModel` |

Each bare union has a `TypeAdapter` beside it, named for it with the suffix `Constructor`.

## Construction

A fact comes to exist in three moves and no others.

1. **Refine.** An organization declares its occurrences by subclassing `Occurrence` and adding the fields each carries; its conditions by subclassing `State`; its interests by subclassing `Subscription` or `StreamSubscription`. A refinement adds and never redeclares.
2. **Construct.** An `Occurrence` exists when its identity and when it occurred are proven. An `Event` exists when its `Occurrence`, its stream, and its `Position` are proven. An `Append` exists when its `Role`, `Goal`, stream, `ExpectedVersion`, and `Occurrences` are proven, it performs nothing. A determined fact's `NodeId` exists when `IdentityInterpreter` derives a UUID version 8 from the rendering of its `Identity`. A `State` exists when its prior, an `Initial` or a `State`, and the `Event` folded into it are proven; the fold of a stream is the chain of these, and its `version` is the count of events folded, derived. A `VersionMismatch` holds what was expected; `VersionMismatchAt` adds what was true, for a provider that knows it. A `Delivery` holds the `Subscription` it undertakes, the `Event` handed to it, and which `Attempt` this is; an `Ending` holds the `Delivery` to end and the `Outcome` it is to be in; a `Disposition` is the condition a delivery is in once ended, holding the `Delivery` and its `Outcome`. A `ReadModel` holds `States` and the `Position` they are as of, and derives its own `PersistReadModel`. An outcome exists when its `TypeAdapter` constructs one variant from a provider's reply.
3. **Refuse.** A negative `Version` or `Position`, an `Attempt` of zero, an `Events` or `Occurrences` with no member, a `VersionMismatch` whose actual is `ANY`, a `ReadOutcome` of `ANY`, a `State` without a prior, a `Delivery` without its event or attempt, and any field Core refuses are each refused at construction.

## Decisions

Each is stated as it stands. To change one, change it here and in the code in one commit.

**Event sourcing is refinements of Core.** An occurrence is a Core `Event`, a condition is a Core `State`, an append, a read, and a subscription are Core `Action`s with their `Role` and `Goal`, a delivery is Core `Work`, because the pattern's things are organizational things and Core already distinguishes them. This rules out a parallel vocabulary of event-sourcing types beside the primitives.

**The actions and their outcomes are the interface.** Every duty a provider performs is one action and one outcome union, and nothing else crosses, because a provider is complete when it holds one interpreter per action and that is checkable. This rules out a provider inventing a request, and rules out a separate statement of what a provider must prove.

**An occurrence and an event are two things.** `Occurrence` is what the organization declares; `Event` holds an `Occurrence` with its stream and position, because only memory knows where an occurrence sits, and what is appended is not yet what is held. This rules out one type that is sometimes without a position.

**Version and Position are two scalars.** A place in one stream and a place in the log of every stream are different meanings, because an event holds both and they move independently. This rules out one position type serving both.

**Expected version is a model beside a vocabulary.** `AtVersion` carries a fact; no stream and any carry none and form the closed vocabulary `Expectation`, because two empty models cannot be told apart from input while a model and an enum member can. `StartingPoint` has the same shape for the same reason. This rules out empty variants that differ only by class name.

**A mismatch states what was expected; a provider that knows adds what was true.** `VersionMismatch` carries `expected` and `VersionMismatchAt` refines it with `actual`, each `AtVersion | Literal[Expectation.NO_STREAM]`, because every provider can prove the first and only some the second, and refinement is how a kind is stated with more established. This rules out a nullable actual and a second effect to manufacture one.

**An event references its stream; a stream holds no events.** `Event.stream` is a `NodeId` and `Stream` adds nothing to `Entity`, because a stream exists before its first event and is identified independently of them. This rules out a stream that embeds its history.

**A condition is the transition shape, and the version is its derivation.** `State` holds its prior and one `Event`, `Initial` is the condition before any event, and `version` is `Version(0)` on `Initial` and the prior's plus one on `State`, because the fold of a stream is each prior condition plus one event and the version is the count of them. This rules out a state computed by a procedure over a list and rules out a version stored on an occurrence or event.

**Interest in a kind of occurrence is refinement.** `Subscription` carries no field naming kinds; an organization subclasses it, because the class is the kind and a field of kinds is a registry. This rules out a subscription that filters by a type name.

**Events has no checkpoint.** The position a subscription has reached is held by the provider, derived from the deliveries it has acknowledged, and resumed from unasked, because no sentence of event sourcing names the organization holding it. This rules out a checkpoint fact, a checkpoint write, and a checkpoint read in this module.

**A disposition is the condition a delivery is in; an ending is the action toward it.** `Disposition` is a Core `State` on the `Delivery` carrying an `Outcome`, and `Ending` is the action carrying the same, because what event sourcing names is that a delivery is complete, returned, or parked, which is a condition and not an occurrence, so it needs no time. The three conditions carry the same fact and are one closed vocabulary. This rules out a disposition as an event, a clock to stamp it, a disposition field on `Delivery`, and variants that cannot be told apart from input.

**A delivery knows which attempt it is.** `Delivery.attempt` is at least one, because the first delivery is a delivery and a redelivery is a fact a subscription acts on. This rules out at-least-once living only in a provider's promise.

**A read model is an Entity of States at a Position, and it authorizes its own recording.** It reuses Core's `States` and derives `PersistReadModel`, because conditions as of a position are what a read model holds, and the fact that authorizes an effect derives the action for it. This rules out a read model with its own state type and rules out a caller deciding to persist one.

**A determined fact's identity is derived from its content.** `StateIdentity`, `DeliveryIdentity`, and `DispositionIdentity` name the content, and `IdentityInterpreter` derives the UUID version 8 through the standard library's `uuid5`, because Core says a thing identified by its content has a version 8 identifier and hashing is outside the derivation algebra, so the one admitted form is an interpreter over an imported capability. This rules out minting an identity for a fact its constituents determine.

**Events names no provider.** No declaration carries a subject, a sequence header, a consumer, a revision, or any provider's word, because an entry here is true of event sourcing on any provider. This rules out provider shapes in this module.

## Quality scenarios

| Scenario | Expected |
|----------|----------|
| An organization subclasses `Occurrence` with a field, and an `Event` holds it | Constructs |
| A `Version`, `Position`, or `Attempt` is below its bound | Refused |
| An `ExpectedVersion` constructs from `"no_stream"`, `"any"`, and `{"version": 3}` | Three distinct facts |
| A `VersionMismatch` is given `ANY` as its actual | Refused |
| An `Append` is constructed with `NO_STREAM` and one occurrence | Constructs |
| The same `StateIdentity` is given to `IdentityInterpreter` twice | The same version 8 `NodeId` |
| Two `StateIdentity` values differing in version | Different `NodeId`s |
| An `Occurrences` or `Events` has no member | Refused |
| `AppendOutcome` is given an `Events` and then a `VersionMismatch` | Each constructs as itself |
| `ReadOutcome` is given `"no_stream"` and then `"any"` | Constructs, then refused |
| A `State` is constructed from an `Initial` and an `Event` | Constructs |
| A `State` is constructed without a prior | Refused |
| An `Ending` and a `Disposition` are constructed from one `Delivery` and serialized | Each constructs back with its `Outcome` |
| A `State` folds two events onto an `Initial` | `version` is 2 |
| A `VersionMismatchAt` is given where a `VersionMismatch` is declared | Constructs; it is a kind of one |
| A `ReadModel` derives its `PersistReadModel` | Holds the read model |
| `LookupOutcome` is given a `NoReadModel` | Constructs as itself |
| Core imports `ontok.events` | The import-linter layers contract fails |

## Glossary

| Term | Meaning |
|------|---------|
| Stream | The events about one entity, identified independently of them. |
| Version | The place an event holds in its stream. |
| Position | The place an event holds in the log of every stream. |
| Occurrence | What the organization declares happened. |
| Event | An occurrence as memory holds it, in its stream at its position. |
| Expected version | What an append asserts of a stream: at a version, no stream, or any. |
| Append | Occurrences declared for a stream under an expected version. |
| Read | A stream asked for whole. |
| Fold | The condition reached by applying a stream's events in order, each to the prior condition. |
| Read model | Conditions held as of a position. |
| Subscription | A role's standing interest in events, toward a goal, from a starting point. |
| Delivery | A subscription's undertaking of one event, on a numbered attempt. |
| Outcome | The condition a delivery is in once ended: complete, returned, or parked. |
| Ending | A delivery to be ended, in the condition it is to be in. |
| Disposition | The condition a delivery is in once ended. |
| Outcome | The union of facts that can exist after an action; a provider constructs one variant. |
| Identity | The content a determined fact's `NodeId` is derived from. |
