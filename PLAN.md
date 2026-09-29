# ONTOK event system plan

## Status

- Branch: `module/ontok-events`, rooted on `main`.
- Distributions and namespaces:

| Distribution | Namespace | Owns | Depends on |
|---|---|---|---|
| `ontok-bus` | `ontok.bus` | provider-independent transport meaning and the provider contract | `ontok-core` |
| `ontok-nats` | `ontok.nats` | the NATS JetStream realization of the bus contract | `ontok-bus`, `nats-py` |
| `ontok-ex` | `ontok.ex` | executing `Work` over the bus | `ontok-core`, `ontok-bus` |

- `ontok-bus` is a rendered skeleton. `ontok-nats` does not exist yet.
- `ontok-ex` currently holds a data-directory config and a bundled NATS server from earlier planning. The config is removed. The server, its license, and its manifest move to `ontok-nats`, where they are not used by this build.
- The design is settled. No discovery phase precedes the build. The provider behaviors it depends on are confirmed against the NATS Server v2.14.6 source and documentation, recorded below.

## Telos

ONTOK systems are event driven. This work gives an organization's program an event system in ONTOK's own terms: events are refinements of Core `Event`, handlers are refinements of Core `Work`, and the class graph is the execution graph.

The architecture is standard event sourcing:
- an append-only log of immutable events;
- durable at-least-once subscriptions;
- idempotent handling;
- prior state read from the log;
- read models rebuilt by replay.

## Acceptance

A program that uses only `ontok-core`, `ontok-bus`, `ontok-nats`, and `ontok-ex` proves five functions against a real NATS server:

1. **Publish.** An event it publishes lands on the log.
2. **Handle.** A work kind receives the events of the kinds it consumes.
3. **Emit.** Events a work emits reach the next work kind.
4. **Read latest.** The latest event under a kind and key is returned.
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
- A conjunction of consumed events is a product of required fields. A genuine alternative is a union.
- Fan-out is several work kinds consuming the same kind. A join is one work kind whose required fields own all joined events.
- No scheduler, readiness flag, pending state, enabled set, or next-step field duplicates constructibility.
- No mapper, parser pipeline, handler chain, or orchestrator performs work that belongs to construction.
- A construction failure is not a workflow status.

### The live edge

- Frozen values hold no client, process, or handle.
- SDK objects are foreign evidence at the boundary and never cross the provider contract.
- A provider binding performs transport calls and serialization only.
- Consumption is a push subscription whose callback is registered once at the composition root. There is no receive loop.
- An arrival is an ordered union of the work's consumed kinds and `Unconstructible`. No construction failure is caught.
- Each delivery reads what it needs from the log through read interpreters nested in its construction. The log is the state. There is no mutable consistency model and no current-state holder.
- The clock and randomness are effects, read through interpreters.
- Programming defects are not caught. A defect crashes the process, and redelivery makes the defect visible.

### Pydantic substrate

- Every semantic value is a strict, frozen Pydantic construction under the python-development standard. Primitive refinements carry the finished configuration.
- No `dict`, untyped header map, metadata bag, or `bytes` payload carries meaning.
- Serialization occurs exactly once, at the provider binding, as JSON of the event.
- An arrival is constructed whole from the delivered message. Its address selects among the work's declared consumed kinds, and its payload constructs as that kind.

## Decisions

### Events

1. **The published thing is the event itself.** The log is the only durable store of events. Large originals live outside the log, and the event carries their digest.
2. **A publishable kind is a refinement of Core `Event`** that declares a `key` derivation returning a stream key. The bus's publication accepts any kind that satisfies this structural contract.
3. **Kind name.** The kind's ontology namespace, which is the top-level package declaring it, followed by its class name. Moving a class between modules does not change its kind name. Renaming a class creates a new kind. Class names are unique within an ontology namespace, and publishable kinds are not nested classes.
4. **Stream key.** A bus scalar naming the stream an event belongs to, safe as a single subject token: a canonical lowercase UUIDv7 or a lowercase hex digest. An event that is its own stream uses its own id.
5. **Identity is deterministic from causes.**
   - The bus constructs UUIDv7s from a millisecond timestamp and 74 bits. Python 3.13 has no `uuid7`.
   - An emitted event's id takes the latest cause's timestamp. Its remaining bits are SHA-256 over the work kind name, the sorted cause ids, and the event's position among the work's emitted events. The id is identical on every retry.
   - An originating event, which no work emits, mints its id once at its source. Minting is a bus effect interpreter that reads the clock and `os.urandom`.
   - The derivation for emitted events is a bus transformation model, not a free function.

### Addresses

6. An address is `<kind name>.<stream key>.<event id>`. The provider maps it to its own syntax.
7. Accounts isolate organizations. Addresses carry no organization prefix.

### Publication

8. **Every append carries exactly one expectation,** chosen by the producer:

| Expectation | Meaning |
|---|---|
| `Any` | nothing is at the event's own address |
| `NoStream` | nothing is under `<kind>.<key>.*` |
| `Exact(sequence)` | the latest under `<kind>.<key>.*` has that sequence |

9. **The outcome is one of three:**
   - **Written,** with the log sequence.
   - **Already present:** the event with this id is on the log. This counts as success.
   - **Conflict:** another event holds the position the expectation required.
10. **Recognizing "already present".**
    - Under `Any`, a failed expectation means the event is already at its own address.
    - Under `NoStream` or `Exact`, the latest event under the key is read. The same id means already present, and a different id means conflict.
11. There is no deduplication window. Idempotence holds for the life of the log.

### Reads

12. **The latest read** returns the last event under a kind and key together with its log sequence, as a value object, or the bus's absence variant.

### Subscriptions

13. **A subscription is a work kind's standing interest** in all of its consumed kinds, together with its progress. Each work kind has exactly one. It exists independently of any process. The program creates it, and creating it again with the same configuration is idempotent.
14. **Start point:** from the beginning of the log or from the next event, declared by the work kind. The default is from the beginning.
15. **Order:** one event at a time, in log order across all of the work's consumed kinds. The cost is throughput.
16. **Storage is infrastructure,** declared by the deployment and not created by the program. `ontok-nats` states the required stream specification, and its conformance suite verifies a deployment against it.

### Delivery and disposition

17. **A delivery is the provider handing one event to one subscription,** possibly more than once. The work receives the event together with its position. EX holds the delivery.
18. **Dispositions, exactly three:**

| Disposition | Meaning | Used when |
|---|---|---|
| Complete | every consequence of the event is durable | the delivery run finished |
| Retry | deliver again | a conflict under `NoStream` or `Exact`, or `Unavailable` from any interpreter |
| Reject | the delivery is terminal | the arrival is `Unconstructible` |

19. **The record of a rejection is the provider's own account.** The bus reads it and invents no second record.
20. **Failures.** Every provider and effect interpreter translates its documented nonfatal failures into `Unavailable`. Anything else is a defect.

### Work

21. **An executable unit is a refinement of Core `Work`.**
    - Its required fields typed as the event-with-position value of a publishable kind are its consumed events.
    - A field typed as that value or the absence variant is a read of the latest event of that kind under the work's key.
22. **The work's key** is the stream key of its consumed events. Joined events share it.
23. **Joins.** When any joined event arrives, EX reads the latest of each other joined kind under the key.
    - If all are present, the work constructs.
    - If any is absent, the delivery completes without work, and the later arrival constructs it.
    - When two arrivals race, both derive identical emitted event ids, and the second append is already present.
24. **Action.** A work kind narrows `action` to its own `Action` refinement, whose `role` and `goal` are narrowed to its own `Role` and `Goal` refinements. EX constructs that action with an id derived from the work kind name.
25. **Emission.** A work's emitted events are a derivation on the work, returning a tuple of constructed events.
    - Their ids come from the identity derivation.
    - Each carries a causation value holding the cause ids and the work kind name.
    - Each occurs at the delivery's instant.
26. **Effects.** A work's effects outside the log are actions derived from the work and executed by effect interpreters.
    - They are idempotent by event id or log sequence.
    - A read model's writes apply only when the incoming sequence is newer than the one stored.
    - EX sends an in-progress acknowledgement before each effect it executes.
27. **Causation.** An emitted event references the events it was derived from and the kind of work that derived it. Work is never published. Causation is a relation between events and is never inferred from temporal order.
28. **The delivery run,** in this order:
    1. read the clock;
    2. construct the work from the arrival, its reads, and the instant;
    3. for each effect, send in-progress, then execute it;
    4. publish the emitted events in order;
    5. dispose of the delivery by decision 18.

    A crash at any point is followed by redelivery, which produces the same ids and converges.
29. **Replay.** EX deletes a work kind's subscription, runs the work kind's declared reset effect to clear its read model, then recreates the subscription from the beginning. A work kind without a read model declares no reset.
30. **The composition root** binds configuration, the provider's clients, and the tuple of work kinds the process runs. It registers each work kind's subscription callback once. Each delivery is one terminal expression.
31. **Rules and contexts** are domain facts that a work reads through its fields. They are never scheduler state. Evaluating them is not an execution concern of this work.

### Idempotence and ownership

32. Idempotence has one home per layer:
    - the bus owns idempotent publication;
    - EX owns deterministic identity for emitted events;
    - the domain owns pure construction.

### Provider contract

33. The bus defines each operation as an action with a constructed outcome: publication, latest read, id minting, subscription creation with its callback, subscription deletion, disposition, and in-progress. A provider implements them as effect interpreters.
34. Contracts accept and return constructed events, never SDK objects. There is no generic publish or subscribe surface.
35. A bus provider offers:
    - conditional append on an exact address and on a wildcard under a key;
    - the latest read under a wildcard;
    - durable ordered push subscriptions with explicit disposition and in-progress;
    - an account of rejected deliveries.

    A provider without them is not a bus provider. The bus does not simulate what a provider lacks.
36. Provider vocabulary, configuration, and policy stay in the provider package.

### NATS realization

37. The subject for an address is `event.<kind name>.<stream key>.<event id>`.
38. Stream specification:
    - the stream `EVENTS` per account, holding `event.>`;
    - file storage;
    - limits retention with no limits;
    - `deny_delete` and `deny_purge`;
    - `allow_direct`.
39. Conditional publish headers:
    - `Any` sends `Nats-Expected-Last-Subject-Sequence: 0` on the exact subject;
    - `NoStream` and `Exact` add `Nats-Expected-Last-Subject-Sequence-Subject: event.<kind>.<key>.*`, with `0` or the sequence.
40. The latest read is a direct get with `{"last_by_subj": "event.<kind>.<key>.*"}` in the request body.
41. Consumer settings:
    - a durable push consumer named for the work kind, with `.` replaced by `-`;
    - `filter_subjects` of `event.<consumed kind>.>` for each consumed kind;
    - a deliver subject on an inbox;
    - explicit acknowledgement;
    - `max_ack_pending` of 1;
    - an acknowledgement wait of 30 seconds;
    - unlimited deliveries;
    - deliver-all or deliver-new, following the start point;
    - no flow control.
42. Dispositions map to a synchronous acknowledgement, a negative acknowledgement, and a terminate. In-progress is `+WPI`. Rejections are read from `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.EVENTS.<consumer>`.
43. A program identity needs exactly these permissions, and no stream administration:
    - publish on `event.>`;
    - publish on `$JS.API.INFO`;
    - publish on `$JS.API.STREAM.INFO.EVENTS`;
    - publish on `$JS.API.DIRECT.GET.EVENTS`;
    - publish on `$JS.API.CONSUMER.CREATE.EVENTS` and `$JS.API.CONSUMER.CREATE.EVENTS.>`;
    - publish on `$JS.API.CONSUMER.INFO.EVENTS.*` and `$JS.API.CONSUMER.DELETE.EVENTS.*`;
    - publish on `$JS.ACK.EVENTS.>` and `$JS.ACK.*.*.EVENTS.>`;
    - subscribe on `_INBOX.>` and on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.EVENTS.>`.
44. The bundled NATS server, its license, and its manifest move from `ontok-ex` to `ontok-nats` and are not used by this build. `ontok-ex`'s data-directory config and its test are removed, because EX starts no server and stores no data.

## Verified provider behavior

Confirmed against the NATS Server v2.14.6 source and documentation:

- **Latest read across a wildcard.** Direct get serves `last_by_subj` through `store.LoadLastMsg`, at `stream.go` line 6093. The file store's `loadLastLocked` branches on `subjectHasWildcard` and scans every matching subject, and request validation does not reject a wildcard. The wildcard is carried in the request body, because a request subject cannot contain one.
- **Conditional publish across a wildcard.** `Nats-Expected-Last-Subject-Sequence-Subject` replaces the checked subject and calls the same `store.LoadLastMsg`, at `stream.go` lines 6453 to 6479. An expected `0` with no match passes.
- **Consumer creation.** A consumer with several `filter_subjects`, available from server 2.10, is created on `$JS.API.CONSUMER.CREATE.<stream>`, so its permission is scoped by stream. A single-filter consumer is created on `$JS.API.CONSUMER.CREATE.<stream>.<consumer>.<filter>`.
- **Terminate advisory.** A terminate publishes on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.<stream>.<consumer>`. Its payload carries the stream, the consumer, the stream sequence, the consumer sequence, and the delivery count.

## Order

1. **`ontok-bus`.**
   - The stream-key contract and the stream key scalar.
   - The expectation union, the three publication outcomes, and the event-with-position value.
   - The absence variant and the latest read.
   - UUIDv7 construction, the emitted-event identity derivation, and the minting interpreter.
   - The causation value.
   - The push subscription with its start point, the three dispositions, and in-progress.
   - The provider contract as actions and outcomes.
2. **`ontok-nats`.**
   - The realization in decisions 37 to 43.
   - The stream specification as a value.
   - The bundled server, license, and manifest moved in, unused.
   - A test fixture that starts `nats:2.14.6-alpine@sha256:ad7a43eb7e3337c3c38ce5d784d1461791f95f730f252d2b25eee699752a0ca3` through testcontainers, with accounts, a scoped program identity, and the `EVENTS` stream.
   - The conformance suite against that server, covering:
     - routing by kind;
     - idempotent publication under each expectation;
     - conflicts under `NoStream` and `Exact`;
     - the latest read;
     - push ordering across several filter subjects;
     - in-progress extending the acknowledgement wait;
     - durability across a restart;
     - the three dispositions and the terminate advisory;
     - replay from the beginning;
     - refusal of stream administration to a program identity.
3. **`ontok-ex`.**
   - Work refinements, one subscription per work kind derived from its field types, and push subscription callbacks.
   - The arrival ordered union with `Unconstructible`.
   - The join and read rules, action narrowing, the clock interpreter, emission with causation, effects with in-progress, reset effects, the delivery run, replay, and the composition root.
   - Tests against the real server, covering:
     - chaining;
     - fan-out;
     - a join;
     - an alternative;
     - redelivery without duplication;
     - a crash before completion;
     - rejection of `Unconstructible`;
     - retry on conflict;
     - retry on `Unavailable`;
     - in-progress during a long effect;
     - replay.
   - The data-directory config and its test removed.
4. **Acceptance.** A test-owned ontology, refining these packages, proves the five functions. The test ontology imports EX; EX imports none of it.
5. **Specification.** `spec/ontok-bus.xml` and `spec/ontok-ex.xml` from the built model, `spec/README.md` updated, and this plan updated to what was built.

## Final gates

- Ruff check and format.
- basedpyright strict.
- import-linter, with `ontok.nats` and `ontok.ex` added to `root_packages` and to the layers:
  - `ontok.ex` never imports `ontok.nats`;
  - `ontok.bus` never imports `ontok.nats` or `ontok.ex`.
- Every package's tests, and the acceptance tests, against a real server. They require Docker.
- `testcontainers` and `nats-py` in the workspace development dependencies.
- XML parsing of the new specifications.
- Wheel and sdist content inspection.
- A four-break audit for every construct: escaped, duplicated, vacuous, fused.

## Out of scope

- Delayed retry and poison thresholds beyond the three dispositions.
- A single effect that runs longer than the 30-second acknowledgement wait.
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

Core `Work` embeds a whole `Action`, and Core `Connection` embeds its endpoints. Work is not published, so the identical embedded action exists only in memory, but the question stands on its own merits: whether a primitive embeds a node or references it by identity. It is decided from the evidence this work produces, not within it.

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
- Do not add a receive loop.
- Do not catch construction failure.
- Do not catch programming defects.
- Do not publish work.
- Do not flatten logs, queues, streams, subjects, and consumers into one string field.
- Do not turn provider configuration into bus semantics.
