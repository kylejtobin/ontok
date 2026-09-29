# ONTOK event system plan

## Status

- Branch: `module/ontok-events`, rooted on `main`.
- Distributions and namespaces:

| Distribution | Namespace | Owns | Depends on |
|---|---|---|---|
| `ontok-bus` | `ontok.bus` | provider-independent transport meaning and the provider contract | `ontok-core` |
| `ontok-nats` | `ontok.nats` | the NATS JetStream realization of the bus contract | `ontok-bus`, `nats-py` |
| `ontok-ex` | `ontok.ex` | executing `Work` over the bus | `ontok-core`, `ontok-bus` |

- `ontok-bus` is a rendered skeleton. `ontok-ex` holds a data-directory config and a bundled NATS server from earlier planning. `ontok-nats` does not exist yet.
- The design is settled. No discovery phase precedes the build. The provider behaviors it depends on are confirmed against the NATS Server v2.14.6 source, recorded below.

## Telos

ONTOK systems are event driven. This work gives an organization's program an event system in ONTOK's own terms: facts are refinements of Core kinds, handlers are refinements of Core `Work`, and the class graph is the execution graph.

The architecture is event sourcing:
- an append-only log of immutable facts;
- durable at-least-once subscriptions;
- idempotent handling;
- prior state read from the log;
- read models rebuilt by replay.

## Acceptance

A program that uses only `ontok-core`, `ontok-bus`, `ontok-nats`, and `ontok-ex` proves five functions against a real NATS server:

1. **Publish.** A fact it publishes lands on the log.
2. **Handle.** A work kind receives the facts of the kind it consumes.
3. **Emit.** Facts a work emits reach the next work kind.
4. **Read latest.** The latest fact under a kind and key is returned.
5. **Replay.** A read model rebuilt from the start of the log is identical.

## Invariants

### One ontology

- Every semantic class in these packages is a kind of a Core primitive.
- A name with no Core parent is not modeled.
- Core primitives are not used raw where a narrower meaning exists.
- There is no `Event(Event)`. Core `Event` remains the universal occurrence, and Core `Work` remains the persistent undertaking.
- No instance `type`, `kind`, `TypeId`, URI discriminator, or registry field recovers meaning the class carries.
- Standard event-driven vocabulary is used unless a different meaning requires a different name.
- Core does not change in this work.

### Construction is the program

- The work graph is the class-and-field dependency graph. No separate graph value, registration table, or subject-to-class dispatch exists.
- A conjunction of consumed facts is a product of required fields. A genuine alternative is a union.
- Fan-out is several work kinds consuming the same kind. A join is one work kind whose required fields own all joined facts.
- No scheduler, readiness flag, pending state, enabled set, or next-step field duplicates constructibility.
- No mapper, parser pipeline, handler chain, or orchestrator performs work that belongs to construction.
- A construction failure is not a workflow status.

### The live edge

- Frozen facts hold no client, process, or handle.
- SDK objects are foreign evidence at the boundary and never cross the provider contract.
- A provider binding performs transport calls and serialization only.
- Each delivery reads what it needs from the log through read interpreters nested in its construction. The log is the state. There is no mutable consistency model and no current-state holder.
- Programming defects are not caught. A defect in a work's construction crashes the process, and redelivery makes the defect visible.

### Pydantic substrate

- Every semantic value is a strict, frozen Pydantic construction under the python-development standard. Primitive refinements carry the finished configuration.
- No `dict`, untyped header map, metadata bag, or `bytes` payload carries meaning.
- Serialization occurs exactly once, at the provider binding, as JSON of the fact.
- An arriving representation is constructed whole as the kind its address names.

## Decisions

### Facts

1. **The published thing is the fact itself.** The log is the only durable store of facts. Large originals live outside the log, and the fact carries their digest.
2. **A publishable fact is a refinement of Core `Event`** that satisfies the bus's publishable-kind contract:
   - its **kind name**;
   - its **key**, a derivation stating what the fact is about;
   - its **discipline**, one of three, declared by the kind.
3. **Kind name.** The kind's ontology namespace, which is the top-level package declaring it, followed by its class name. Moving a class between modules does not change its kind name. Renaming a class creates a new kind. Class names are unique within an ontology namespace, and publishable kinds are not nested classes.
4. **Key.** A bus scalar, safe as a single subject token: a canonical lowercase UUIDv7 or a lowercase hex digest. A fact about itself uses its own id as its key.
5. **Discipline.** Each publishable kind declares exactly one:

| Discipline | Meaning | Expectation on publish |
|---|---|---|
| Accumulating | many facts of the kind under one key | nothing at the fact's own address |
| Unique per key | at most one fact of the kind under one key | nothing under `<kind>.<key>.*` |
| Succession | each fact succeeds the latest under its key | the latest under `<kind>.<key>.*` is the fact's prior |

6. **Identity is deterministic from causes.**
   - A fact emitted by work has a UUIDv7 id. Its timestamp is the cause's timestamp. Its remaining bits are a hash of the work kind name, the cause's id, and the fact's position among the work's emitted facts. The id is a valid v7, time-ordered by cause, and identical on every retry.
   - An originating fact, which no work emits, mints its id once at its source.
   - A work fact's id is derived in the same way from the work kind name and the sorted ids of the facts it consumed.
   - The derivation is a bus transformation model. It is not a free function.

### Addresses

7. An address is `<kind name>.<key>.<fact id>`. The provider maps it to its own syntax.
8. Accounts isolate organizations. Addresses carry no organization prefix.

### Publication

9. **Every publication carries exactly one expectation,** chosen by the kind's discipline.
10. **The outcome is one of three:**
    - **Written,** with the log sequence.
    - **Already present:** the expectation failed and the fact at the governing address has the same id. This counts as success.
    - **Conflict:** the expectation failed and the governing fact has another id.
11. **Recognizing "already present".**
    - For accumulating kinds, a failed expectation on the fact's own address means the fact is already there.
    - For unique and succession kinds, the latest fact under the key is read and its id compared.
12. There is no deduplication window. Idempotence holds for the life of the log.

### Reads

13. The latest read returns the last fact under a kind and key, or none, with its sequence. It is constructed as the kind.

### Subscriptions

14. **A subscription is a work kind's standing interest** in each kind it consumes, together with its progress. It exists independently of any process. Its name is the work kind name. The program creates it, and creating it again with the same configuration is idempotent.
15. **Start point:** from the beginning of the log or from the next fact, declared by the work kind. The default is from the beginning.
16. **Order:** one fact at a time, in log order, per subscription. The cost is throughput.
17. **Storage is infrastructure,** declared by the deployment and not created by the program. `ontok-nats` states the required stream specification, and its conformance suite verifies a deployment against it.

### Delivery and disposition

18. **A delivery is the provider handing one fact to one subscription,** possibly more than once. The work receives the fact. EX holds the delivery.
19. **Dispositions, exactly three:**

| Disposition | Meaning | Used when |
|---|---|---|
| Complete | every consequence of the fact is durable | the delivery run finished |
| Retry | deliver again | a succession conflict, or a provider transport failure |
| Reject | the delivery is terminal | the arrival does not construct as the consumed kind |

20. **The record of a rejection is the provider's own account.** The bus reads it and invents no second record.

### Work

21. **An executable unit is a refinement of Core `Work`.**
    - Its required fields typed as publishable kinds are its consumed facts.
    - A field typed as a union of a publishable kind and the bus's absence variant is a read of the latest fact of that kind under the work's key.
22. **The work's key** is the key of its consumed facts. Joined facts share it.
23. **Joins.** When any joined fact arrives, EX reads the latest of each other joined kind under the key.
    - If all are present, the work constructs.
    - If any is absent, the delivery completes without work, and the later arrival constructs it.
    - When two arrivals race, both derive the same work id, and the second publication is already present.
24. **Action.** A work kind narrows `action` to its own `Action` refinement, whose `role` and `goal` are narrowed to its own `Role` and `Goal` refinements. EX constructs that action with an id derived from the work kind name, so every work of a kind references the identical declared doing.
25. **Emission.** A work's emitted facts are a derivation on the work, returning a tuple of constructed facts whose ids come from the identity derivation.
26. **Effects.** A work's effects outside the log are actions derived from the work and executed by effect interpreters. They are idempotent by fact id or log sequence. A read model's writes apply only when the incoming sequence is newer than the one stored.
27. **Provenance.** The work fact is published, with the accumulating discipline, under its own kind name and key.
28. **Causation.**
    - An emitted fact references the work that produced it.
    - The work references the facts it consumed.
    - Causation is a relation between events and is never inferred from temporal order.
29. **The delivery run,** in this order:
    1. construct the work from the arrival and its reads;
    2. execute its effects;
    3. publish the work fact;
    4. publish its emitted facts in order;
    5. complete the delivery.

    A crash at any point is followed by redelivery, which produces the same ids and converges.
30. **Replay.** EX deletes a work kind's subscription and recreates it from the beginning. Read-model effects are idempotent by sequence, so a replay reproduces the model.
31. **The composition root** binds configuration, the provider's clients, and the tuple of work kinds the process runs. Each delivery is one terminal expression.
32. **Rules and contexts** are domain facts that a work reads through its fields. They are never scheduler state. Evaluating them is not an execution concern of this work.

### Idempotence and ownership

33. Idempotence has one home per layer:
    - the bus owns idempotent publication;
    - EX owns deterministic identity for work and emissions;
    - the domain owns pure construction.

### Provider contract

34. The bus defines each operation as an action with a constructed outcome: publication, latest read, subscription creation and deletion, fetch, and disposition. A provider implements them as effect interpreters.
35. Contracts accept and return constructed facts, never SDK objects. There is no generic publish or subscribe surface.
36. A bus provider offers:
    - conditional append on an exact address and on a wildcard under a key;
    - the latest read under a wildcard;
    - durable ordered subscriptions with explicit disposition;
    - an account of rejected deliveries.

    A provider without them is not a bus provider. The bus does not simulate what a provider lacks.
37. Provider vocabulary, configuration, and policy stay in the provider package.

### NATS realization

38. The subject for an address is `fact.<kind name>.<key>.<fact id>`.
39. Stream specification:
    - one stream per account holding `fact.>`;
    - file storage;
    - limits retention with no limits;
    - `deny_delete` and `deny_purge`;
    - `allow_direct`.
40. Conditional publish headers:
    - an exact-address expectation is `Nats-Expected-Last-Subject-Sequence: 0`;
    - a key expectation adds `Nats-Expected-Last-Subject-Sequence-Subject: fact.<kind>.<key>.*` with `0` or the prior's sequence.
41. The latest read is a direct get with `{"last_by_subj": "fact.<kind>.<key>.*"}` in the request body.
42. Consumer settings:
    - a durable pull consumer named after the work kind;
    - a filter of `fact.<consumed kind>.>`;
    - explicit acknowledgement;
    - `max_ack_pending` of 1;
    - an acknowledgement wait of 30 seconds;
    - unlimited deliveries;
    - deliver-all or deliver-new, following the start point.

    A work consuming several kinds has one consumer per consumed kind.
43. Dispositions map to a synchronous acknowledgement, a negative acknowledgement, and a terminate. Rejections are read from `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.<stream>.<consumer>`.
44. A program identity needs:
    - publish on `fact.>`;
    - JetStream info;
    - stream info and direct get on the fact stream;
    - consumer create, info, delete, and next-message on the fact stream;
    - acknowledgement subjects;
    - subscribe on inboxes and on the terminate advisory.

    It needs no stream administration.
45. The bundled NATS server, its license, and its manifest move from `ontok-ex` to `ontok-nats`. They are used only to start a real server for tests. `ontok-ex`'s data-directory config is removed, because EX starts no server and stores no data.

## Verified provider behavior

Confirmed against the NATS Server v2.14.6 source:

- **Latest read across a wildcard.** Direct get serves `last_by_subj` through `store.LoadLastMsg`, at `stream.go` line 6093. The file store's `loadLastLocked` branches on `subjectHasWildcard` and scans every matching subject, and request validation does not reject a wildcard. The wildcard is carried in the request body, because a request subject cannot contain one.
- **Conditional publish across a wildcard.** `Nats-Expected-Last-Subject-Sequence-Subject` replaces the checked subject and calls the same `store.LoadLastMsg`, at `stream.go` lines 6453 to 6479. An expected `0` with no match passes.
- **Scoped consumer creation.** A single-filter consumer is created on `$JS.API.CONSUMER.CREATE.<stream>.<consumer>.<filter>`. Permissions can scope that subject to one stream and filter.
- **Terminate advisory.** A terminate publishes on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.<stream>.<consumer>`. Its payload carries the stream, the consumer, the stream sequence, the consumer sequence, and the delivery count.

## Order

1. **`ontok-bus`.** The publishable-kind contract, key, discipline, the identity derivation, address, publication with its expectation and three outcomes, the latest read with its absence variant, subscription with its start point, delivery with its three dispositions, and the provider contract as actions and outcomes.
2. **`ontok-nats`.**
   - The realization in decisions 38 to 44.
   - The stream specification as a value.
   - The bundled server moved in, with a test fixture that starts it with accounts and a scoped identity.
   - The conformance suite against that server, covering:
     - routing by kind;
     - idempotent publication under each discipline;
     - a succession conflict;
     - the latest read;
     - ordering;
     - durability across a restart;
     - the three dispositions and the terminate advisory;
     - replay from the beginning;
     - refusal of stream administration to a program identity.
3. **`ontok-ex`.**
   - Work refinements, subscriptions derived from field types, the join and read rules, action narrowing, emission, effects, provenance, the delivery run, replay, and the composition root.
   - Tests against the real server, covering chaining, fan-out, a join, an alternative, redelivery without duplication, a crash before completion, rejection, a succession retry, and replay.
   - The data-directory config removed.
4. **Acceptance.** A test-owned ontology, refining these packages, proves the five functions. The test ontology imports EX; EX imports none of it.
5. **Specification.** `spec/ontok-bus.xml` and `spec/ontok-ex.xml` from the built model, `spec/README.md` updated, and this plan updated to what was built.

## Final gates

- Ruff check and format.
- basedpyright strict.
- import-linter, with `ontok.bus`, `ontok.nats`, and `ontok.ex` added:
  - `ontok.ex` never imports `ontok.nats`;
  - `ontok.bus` never imports `ontok.nats` or `ontok.ex`.
- Every package's tests, and the acceptance tests, against a real server.
- XML parsing of the new specifications.
- Wheel and sdist content inspection.
- A four-break audit for every construct: escaped, duplicated, vacuous, fused.

## Out of scope

- Delayed retry and poison thresholds beyond the three dispositions.
- Multiple providers.
- Cross-platform wheels and distributing the bundled server.
- Clustering, federation, leaf nodes, and gateways.
- Key-value and object stores, and request and reply.
- Tracing.
- Liveness.
- Evaluating rules and contexts.

## Interchange standards

CloudEvents, AsyncAPI, and W3C Trace Context are projections and interoperability assets. They do not define this programming model and are not copied into these packages.

## Open for Core

Core `Work` embeds a whole `Action`, and under decision 24 every work fact of one kind embeds the identical action. Core `Connection` embeds its endpoints in the same way. Whether a primitive embeds a node or references it by identity is decided from the evidence this work produces, not within it.

## Forbidden substitutions

- Do not replace modeling with a NATS wrapper.
- Do not replace event-driven meaning with "it is events".
- Do not match an IT noun to a Core noun in place of refinement.
- Do not model the whole NATS API.
- Do not invent vocabulary to avoid standard event-driven words.
- Do not build a one-off organizational workflow as EX.
- Do not claim exactly-once delivery.
- Do not add a deduplication window, a second database, or a mutable consistency model.
- Do not add a registration table or subject-to-class dispatch.
- Do not catch programming defects.
- Do not flatten logs, queues, streams, subjects, and consumers into one string field.
- Do not turn provider configuration into bus semantics.
