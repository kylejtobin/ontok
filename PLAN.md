# ONTOK event system plan

## Status

- Branch: `module/ontok-events`, rooted on `main`.
- Distributions and namespaces:

| Distribution | Namespace | Owns | Depends on |
|---|---|---|---|
| `ontok-bus` | `ontok.bus` | provider-independent event, log, and delivery meaning; the provider contract; the clock and identity minting | `ontok-core` |
| `ontok-nats` | `ontok.nats` | the NATS JetStream realization of the bus contract | `ontok-bus`, `nats-py` |
| `ontok-ex` | `ontok.ex` | executing `Work` over the bus | `ontok-core`, `ontok-bus` |

- `ontok-bus` is a rendered skeleton. `ontok-nats` does not exist yet.
- `ontok-ex` holds a data-directory config, its test, and a bundled NATS server from earlier planning. The config and its test are removed. The server, its license, and its manifest move to `ontok-nats` and are not used by this build.
- The design is settled. No discovery phase precedes the build. Every provider behavior it depends on is confirmed against the NATS Server v2.14.6 source, the NATS documentation, or the `nats-py` source, as recorded below.

## Telos

ONTOK systems are event driven. This work gives an organization's program an event system in ONTOK's own terms: events are refinements of Core `Event`, reactions are refinements of Core `Work`, and the class graph is the execution graph.

The architecture is standard event sourcing, expressed entirely as ONTOK kinds under the python-development standard:
- an append-only log of immutable events, organized into streams;
- appends with an expected-version check;
- durable at-least-once subscriptions;
- idempotent reactions;
- prior state read from the log;
- read models rebuilt by replay.

## Acceptance

A program that uses only `ontok-core`, `ontok-bus`, `ontok-nats`, and `ontok-ex` proves five functions against a real NATS server:

1. **Publish.** An event it publishes lands on the log.
2. **Handle.** A reaction receives the events of the types it consumes.
3. **Emit.** Events a reaction emits reach the next reaction.
4. **Read latest.** The latest event in a stream is returned.
5. **Replay.** A read model rebuilt from the start of the log is identical.

## Invariants

### One ontology

- Every semantic class in these packages is a kind of a Core primitive.
- A name with no Core parent is not modeled.
- Core primitives are not used raw where a narrower meaning exists.
- There is no `Event(Event)`. Core `Event` remains the universal occurrence, and Core `Work` remains the persistent undertaking.
- The class is the kind. The only discriminator is an event's `event_type` and a reaction's `work_type`: each is interchange identity, carried on the wire and in names, and is not a substitute for class identity. No other `type`, `kind`, `TypeId`, URI, or registry field exists.
- Standard event-sourcing vocabulary is used unless a different meaning requires a different name.
- Core does not change in this work.

### Construction is the program

- The reaction graph is the class-and-field dependency graph. No separate graph value, registration table, or subject-to-class dispatch exists.
- A conjunction of consumed events is a product of required fields. A genuine alternative is a union.
- Fan-out is several reactions consuming the same event type. A join is one reaction whose required fields own all joined events.
- No scheduler, readiness flag, pending state, enabled set, or next-step field duplicates constructibility.
- No mapper, parser pipeline, handler chain, or orchestrator performs work that belongs to construction.
- A construction failure is not a workflow status.

### The live edge

- Frozen values hold no client, process, or handle.
- SDK objects are foreign evidence at the boundary and never cross the provider contract.
- A provider binding performs transport calls and serialization only.
- Consumption is a push subscription whose callback is registered once at the composition root. There is no receive loop.
- An arrival is an ordered union of the reaction's consumed event union and `Unconstructible`. No construction failure is caught.
- Each delivery reads what it needs from the log through read interpreters nested in its terminal expression. The log is the state. There is no mutable consistency model and no current-state holder.
- The clock and randomness are effects, read through interpreters.
- Programming defects are not caught. A defect crashes the process, and redelivery makes it visible.

### Pydantic substrate

- Every semantic value is a strict, frozen Pydantic construction under the python-development standard. Refinements of Core primitives carry the finished configuration.
- No `dict`, untyped header map, metadata bag, or `bytes` payload carries meaning.
- Serialization occurs exactly once, at the provider binding, as the JSON of the event.
- An arrival is constructed whole from the delivered message. Its payload constructs as the reaction's consumed event union, discriminated by `event_type`.
- In a union that is not discriminated, every variant except the last carries a fact no other variant carries. Only the final variant may be empty, because an empty model has no refusal.

## Decisions

### Events

1. **The published thing is the event itself.** The log is the only durable store of events. Large originals live outside the log, and the event carries their digest.
2. **Event type.** Every publishable kind is a refinement of Core `Event` carrying `event_type: Literal["<namespace>:<Class>"]`, where the namespace is the top-level package that declares it. The colon keeps it a single subject token. An event type is interchange identity: renaming the class does not change it.
3. **Versioning.** An event type's shape never changes. A new shape is a new event type. Readers keep constructing every event type that exists in the log.
4. **Stream.** Every publishable kind derives `stream`, a `StreamKey` naming what the event is about. A stream key is a canonical lowercase UUIDv7 or a lowercase hex digest. An event that is its own stream uses its own id.
5. **Two acts of publication.**
   - An **originating** event is created by a source. It carries no causation.
   - An **emitted** event is derived by a reaction. It carries `causation: Causation`, which holds the reaction's `work_type`, the `trigger` (the id of the event that caused it), and its `position` among the reaction's emissions.
6. **Publication identity.** An originating event's publication identity is its id. An emitted event's publication identity is its causation. A retry of an emission lands on the same causation and is already present.
7. **Node ids.**
   - The bus constructs UUIDv7s from a millisecond timestamp and 74 bits. Python 3.13 has no `uuid7`.
   - A source mints each originating event's id through the minting interpreter, from a clock instant and random bits.
   - Each delivery mints exactly one id, the reaction's.
   - An emitted event's id is the reaction's id with its position in the low 16 bits. A reaction emits at most 65,536 events.
   - A retry mints a different reaction id. Its emissions carry new ids but land on the same causation addresses, so the first append wins.
8. **Occurrence.** A delivery reads the clock once. Its reaction, and every event it emits, occurs at that instant.

### Addresses

9. **An address locates an event in the log.**
   - An originating event's address is its stream, its event type, and its id.
   - An emitted event's address is its stream, its event type, and its causation.
10. Accounts isolate organizations, so addresses carry no organization prefix.

### Appends

11. **Every append carries exactly one expectation, chosen by the producer:**

| Expectation | Holds when |
|---|---|
| `ExpectAny` | nothing is at the event's own address |
| `ExpectNoStream` | the stream holds no event |
| `ExpectSequence(sequence)` | the latest event in the stream has that sequence |

12. **The outcome is one of four:**

| Outcome | Carries | Meaning |
|---|---|---|
| `Written` | `sequence` | the event was appended |
| `AlreadyPresent` | `existing`, the sequence already holding it | the same event is already on the log; this is success |
| `Conflict` | `latest`, the stream's latest sequence | another event holds the position the expectation required |
| `Unavailable` | `reason` | the provider could not complete the append |

13. **Recognizing "already present".**
    - Under `ExpectAny`, a failed expectation means the event is already at its own address.
    - Under `ExpectNoStream` or `ExpectSequence`, the latest event in the stream is read. The same publication identity means already present, and any other means conflict.
14. There is no deduplication window. Idempotence holds for the life of the log.
15. **Events do not embed their prior.** Succession is enforced by `ExpectSequence`. The state-transition shape with a `prior` field is the in-memory fold a reaction uses to decide what to emit, never a wire shape.

### Reads

16. **The latest read** returns the last event in a stream, of any type, as `Retained[S]`: the event and its log sequence. `S` is the stream's event union. When the stream is empty it returns `Absent(stream)`, and on provider failure it returns `Unavailable(reason)`. The outcome is constructed through the `TypeAdapter` declared beside `S`.

### Subscriptions

17. **A subscription is a reaction's standing interest** in every event type it consumes, together with its progress. Each reaction kind has exactly one. It exists independently of any process. Its name is the reaction's `work_type`. The program creates it, and creating it again with the same configuration is idempotent.
18. **Start point:** from the beginning of the log or from the next event, declared by the reaction kind. The default is from the beginning.
19. **Order:** one event at a time, in log order across all of the reaction's consumed types. One ordered subscription makes joins race-free. The cost is throughput.
20. **Storage is infrastructure,** declared by the deployment and not created by the program. `ontok-nats` states the required stream specification, and its conformance suite verifies a deployment against it.

### Delivery and disposition

21. **A delivery is the provider handing one event to one subscription,** possibly more than once. The reaction receives the event with its position. The delivery's `DeliveryToken` is the provider's acknowledgement address.
22. **Dispositions, exactly three:**

| Disposition | Meaning | Used when |
|---|---|---|
| Complete | every consequence of the event is durable | every read, effect, and append succeeded |
| Retry | deliver again | a `Conflict`, or an `Unavailable` from any interpreter |
| Reject | the delivery is terminal | the arrival is `Unconstructible` |

23. **The record of a rejection is the provider's own account.** The bus reads it and invents no second record.
24. **Failures.** Every interpreter translates its documented nonfatal failures into `Unavailable`. Anything else is a defect.
25. **Long handling.** Before each effect it executes, the delivery sends an in-progress acknowledgement, so the acknowledgement wait bounds a single effect, not the whole delivery.

### Reactions

26. **A reaction is a refinement of `Reaction(Work)`.**
    - It carries `work_type: Literal["<namespace>:<Class>"]`.
    - It narrows `action` to its own `Action` refinement, whose `role` and `goal` are narrowed to its own `Role` and `Goal` refinements.
    - Its required fields are the retained consumed event, the delivery's instant and minted id, and its reads.
27. **Derivations,** each a transformation on the reaction:
    - `stream`, the stream it acts on, which is its trigger's stream;
    - `emits`, the tuple of `Emission` actions it authorizes;
    - `effects`, the tuple of the application's effect actions it authorizes.
28. **Readiness.** A reaction kind's construction is an ordered union of the reaction and `Unready`. Domain alternatives are modeled as the reaction's own variants, so the reaction's only possible refusal is an `Unavailable` read, and `Unready` is the final fallback.
29. **Joins.** A join's read of its counterpart is an ordered union of `Joined`, which requires the counterpart retained, then `Partial`, which requires `Absent`, then `Unready`. `Partial` emits nothing, and the later arrival constructs `Joined`.
30. **Causation.** An emitted event references its trigger and the reaction kind that derived it. Reactions are never published. Causation is a relation between events and is never inferred from temporal order.
31. **Effects.** A reaction's effects outside the log are the application's actions, executed by the application's effect interpreters.
    - They are idempotent by event id or log sequence.
    - A read model's writes apply only when the incoming sequence is newer than the one stored.
32. **Settlement.** A delivery settles as `Rejected | Completed | Deferred`.
    - `Rejected` holds the `Unconstructible` arrival.
    - `Completed` is attempted before `Deferred`, and requires a ready reaction, succeeded effects, and appends that are all `Written` or `AlreadyPresent`.
    - `Deferred` is the final fallback.
    - Each variant derives `disposal`, the `Dispose` action.
33. **The delivery's terminal expression** is one expression, evaluated in this order by data dependency:
    1. the arrival, constructed by the route;
    2. the clock read and the minted id;
    3. the reads;
    4. readiness;
    5. for each effect, in-progress, then the effect;
    6. the appends of `emits`;
    7. the settlement and its disposal.

    Each stage is constructed from the previous stage's outcome. An `Unconstructible` arrival derives no reads, effects, or emissions. A crash at any point is followed by redelivery, and the causation addresses make it converge.
34. **Projection.** `Projection(Reaction)` maintains a read model and derives `reset`, the action that clears it.
35. **Replay** is a concept whose actions depend on each other's outcomes: delete the subscription, run the projection's `reset`, then create the subscription again from the beginning. It is one composition-root expression. Its ordering comes from data dependency, not statement order.
36. **The composition root** binds configuration, the provider client, the application's effect interpreters, and each reaction kind's callback, registered once. `ontok-ex` compiles each reaction kind's subscription from its annotated consumed union at registration, just as Pydantic compiles construction from annotations. No registry exists.
37. **Rules and contexts** are domain facts a reaction reads through its fields. They are never scheduler state. Evaluating them is not an execution concern of this work.

### Idempotence and ownership

38. Idempotence has one home per layer:
    - the bus owns idempotent appends;
    - `ontok-ex` owns causation for every emitted event;
    - the domain owns pure construction.

### Provider contract

39. **The bus defines each operation as an action with a constructed outcome:**
    - `Origination[E]` and `Emission[E]`, each with an expectation;
    - `ReadLatest`;
    - `EnsureSubscription` and `DeleteSubscription`;
    - `Dispose` and `InProgress`;
    - `ReadClock` and `MintIdentity`.

    A provider implements the transport actions as effect interpreters. The bus implements the clock and minting itself.
40. Contracts accept and return constructed events, never SDK objects. There is no generic publish or subscribe surface.
41. **A bus provider offers:**
    - conditional append on an exact address and on a whole stream;
    - the latest read across a stream;
    - durable ordered push subscriptions with explicit disposition and in-progress;
    - an account of rejected deliveries.

    A provider without them is not a bus provider. The bus does not simulate what a provider lacks.
42. Provider vocabulary, configuration, and policy stay in the provider package.

### NATS realization

43. **Subjects.**
    - An originating event's subject is `event.<stream>.<event_type>.<id>`.
    - An emitted event's subject is `event.<stream>.<event_type>.<work_type>.<trigger>.<position>`.
44. **Stream specification:**
    - the stream `EVENTS` per account, holding `event.>`;
    - file storage;
    - limits retention with no limits;
    - `deny_delete` and `deny_purge`;
    - `allow_direct`.
45. **Conditional publish headers:**
    - `ExpectAny` sends `Nats-Expected-Last-Subject-Sequence: 0` on the event's exact subject;
    - `ExpectNoStream` and `ExpectSequence` add `Nats-Expected-Last-Subject-Sequence-Subject: event.<stream>.>`, with `0` or the sequence.
46. **The latest read** is a request to `$JS.API.DIRECT.GET.EVENTS` whose body is `{"last_by_subj": "event.<stream>.>"}`. A 404 status is `Absent`.
47. **Consumer settings:**
    - a durable push consumer named with the reaction's `work_type`;
    - `filter_subjects` of `event.*.<event_type>.>` for each consumed event type;
    - a deliver subject on an inbox;
    - explicit acknowledgement;
    - `max_ack_pending` of 1;
    - an acknowledgement wait of 30 seconds;
    - unlimited deliveries;
    - deliver-all or deliver-new, following the start point;
    - no flow control.

    `EnsureSubscription` creates it through the JetStream consumer API. The composition root binds the callback to it through the client's push subscription with manual acknowledgement.
48. **Dispositions through the delivery token:**
    - Complete is a request of `+ACK` to the token, which confirms it;
    - Retry is a publish of `-NAK`;
    - Reject is a publish of `+TERM`;
    - in-progress is a publish of `+WPI`.

    Rejections are read from `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.EVENTS.<consumer>`.
49. **A program identity has exactly these permissions,** and no stream administration:
    - publish on `event.>`;
    - publish on `$JS.API.INFO`;
    - publish on `$JS.API.STREAM.INFO.EVENTS`;
    - publish on `$JS.API.DIRECT.GET.EVENTS`;
    - publish on `$JS.API.CONSUMER.CREATE.EVENTS` and `$JS.API.CONSUMER.CREATE.EVENTS.>`;
    - publish on `$JS.API.CONSUMER.INFO.EVENTS.*` and `$JS.API.CONSUMER.DELETE.EVENTS.*`;
    - publish on `$JS.ACK.EVENTS.>` and `$JS.ACK.*.*.EVENTS.>`;
    - subscribe on `_INBOX.>` and on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.EVENTS.>`.

## Verified provider behavior

Confirmed against the NATS Server v2.14.6 source, the NATS documentation, and the `nats-py` 2.16 source:

- **Latest read across a wildcard.** Direct get serves `last_by_subj` through `store.LoadLastMsg`, at `stream.go` line 6093. The file store's `loadLastLocked` branches on `subjectHasWildcard` and scans every matching subject, and request validation does not reject a wildcard.
- **The body form is required.** `nats-py`'s `get_msg(direct=True, subject=...)` sends the subject form, `$JS.API.DIRECT.GET.<stream>.<subject>`, and a request subject cannot contain a wildcard. The interpreter sends the body form itself.
- **Conditional publish across a wildcard.** `Nats-Expected-Last-Subject-Sequence-Subject` replaces the checked subject and calls the same `store.LoadLastMsg`, at `stream.go` lines 6453 to 6479. An expected `0` with no match passes.
- **Consumer creation.** A consumer with several `filter_subjects`, available from server 2.10, is created on `$JS.API.CONSUMER.CREATE.<stream>`, so its permission is scoped by stream.
- **Acknowledgement payloads.** `nats-py` acknowledges with `+ACK`, `-NAK`, `+TERM`, and `+WPI` on the message's reply subject. Its `ack_sync` is a request on that subject.
- **Terminate advisory.** A terminate publishes on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.<stream>.<consumer>`. Its payload carries the stream, the consumer, the stream sequence, the consumer sequence, and the delivery count.

## Constructs

Every declaration below is one whitelisted form. Actions sit beside the concept that authorizes them.

### `ontok-bus`

| Declaration | Construct | File |
|---|---|---|
| `StreamKey`, `EventTypeName`, `WorkTypeName`, `LogSequence`, `Ordinal`, `DeliveryToken`, `FailureReason` | semantic scalars | `type.py` |
| `StartPoint`, `Disposition` | `StrEnum` scalars | `type.py` |
| `Causation` | value object: `work_type`, `trigger`, `position` | `value.py` |
| `Retained[E]` | value object: `event`, `sequence` | `value.py` |
| `Absent` | value object: `stream` | `value.py` |
| `Unavailable` | value object: `reason` | `value.py` |
| `ExpectAny`, `ExpectNoStream`, `ExpectSequence` | value objects; `Expectation` is their union, constructed only in code | `publication.py` |
| `OriginAddress`, `EmissionAddress` | value objects | `publication.py` |
| `Origination[E]`, `Emission[E]` | actions, each deriving `address` | `publication.py` |
| `Written`, `AlreadyPresent`, `Conflict` | value objects; the append outcome is their union with `Unavailable` | `publication.py` |
| `ReadLatest` | action: `stream` | `read.py` |
| the latest-read outcome | union: `Retained[S] \| Absent \| Unavailable` | `read.py` |
| `EnsureSubscription`, `DeleteSubscription` | actions | `subscription.py` |
| `Delivery[C]` | value object: `token`, `event` as `Retained[C]` | `delivery.py` |
| `Unconstructible` | value object: `token` | `delivery.py` |
| the arrival | ordered union: `Delivery[C] \| Unconstructible` | `delivery.py` |
| `Dispose`, `InProgress` | actions: `token`, and `disposition` for `Dispose` | `delivery.py` |
| `UUIDv7` composition from a millisecond timestamp and 74 bits | transformation | `identity.py` |
| `EmittedIdentity` | transformation: `work`, `position`; derives `id` | `identity.py` |
| `ReadClock`, `MintIdentity` | actions | `identity.py` |
| `ClockInterpreter`, `MintInterpreter` | effect interpreters; capabilities are UTC `tzinfo` and `random.SystemRandom` | `interpreter.py` |

### `ontok-nats`

| Declaration | Construct | File |
|---|---|---|
| `NatsSettings` | config, prefix `ONTOK_NATS_`: URL, user, and password as `SecretStr` | `config.py` |
| `StreamSpecification` | value object | `stream.py` |
| the publish acknowledgement, the API error with its wrong-last-sequence code, the direct-get reply, the terminate advisory | foreign models | `model.py` |
| `DeliveryRoute` | route: lifted from the NATS message with `from_attributes=True`; the token from `reply`, the payload through `Json[C]`, the sequence through an `AliasPath` into the message metadata | `route.py` |
| append, latest read, subscription creation, subscription deletion, disposal, in-progress | one effect interpreter per action meaning; each composes its subject at the client call and catches only its documented errors | `interpreter.py` |

### `ontok-ex`

| Declaration | Construct | File |
|---|---|---|
| `Reaction(Work)` | concept model | `reaction.py` |
| `Projection(Reaction)` | concept model; derives `reset` | `reaction.py` |
| `Unready` | value object; the final fallback of every readiness union | `reaction.py` |
| `Rejected`, `Completed`, `Deferred` | value objects; settlement is their ordered union; each derives `disposal` | `settlement.py` |
| `Replay` | concept model whose actions depend on each other's outcomes | `replay.py` |

The application declares its events and their stream unions, its reactions with their readiness unions and their narrowed `Action`, `Role`, and `Goal`, its effects and their interpreters, and its composition root.

## Order

1. **`ontok-bus`,** with every declaration in its construct table.
2. **`ontok-nats`.**
   - The realization in decisions 43 to 49.
   - The stream specification as a value.
   - The bundled server, license, and manifest moved in, unused.
   - A test fixture that starts `nats:2.14.6-alpine@sha256:ad7a43eb7e3337c3c38ce5d784d1461791f95f730f252d2b25eee699752a0ca3` through testcontainers, with accounts, a scoped program identity, and the `EVENTS` stream.
   - The conformance suite against that server, covering:
     - routing by event type;
     - idempotent appends under each expectation;
     - conflicts under `ExpectNoStream` and `ExpectSequence`;
     - the latest read across a stream's types, and `Absent`;
     - push ordering across several filter subjects;
     - in-progress extending the acknowledgement wait;
     - durability across a restart;
     - the three dispositions and the terminate advisory;
     - replay from the beginning;
     - refusal of stream administration to a program identity.
3. **`ontok-ex`.**
   - Every declaration in its construct table.
   - Subscription compilation at registration.
   - The data-directory config and its test removed.
   - Tests against the real server, covering:
     - chaining;
     - fan-out;
     - a join, both partial and joined;
     - an alternative;
     - redelivery without duplication;
     - a crash before completion;
     - rejection of `Unconstructible`;
     - retry on conflict;
     - retry on an unavailable read, through `Unready`;
     - in-progress during a long effect;
     - replay.
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

Core `Work` embeds a whole `Action`, and Core `Connection` embeds its endpoints. Reactions are not published, so the identical embedded action exists only in memory, but the question stands on its own merits: whether a primitive embeds a node or references it by identity. It is decided from the evidence this work produces, not within it.

## Forbidden substitutions

- Do not replace modeling with a NATS wrapper.
- Do not replace event-driven meaning with "it is events".
- Do not match an IT noun to a Core noun in place of refinement.
- Do not model the whole NATS API.
- Do not invent vocabulary to avoid standard event-sourcing words.
- Do not build a one-off organizational workflow as EX.
- Do not claim exactly-once delivery.
- Do not add a deduplication window, a second database, or a mutable consistency model.
- Do not add a registration table or subject-to-class dispatch.
- Do not add a receive loop.
- Do not catch construction failure.
- Do not catch programming defects.
- Do not publish reactions.
- Do not hash to derive identity.
- Do not read class metadata outside subscription compilation.
- Do not place an empty variant anywhere but last in a union that is not discriminated.
- Do not flatten logs, queues, streams, subjects, and consumers into one string field.
- Do not turn provider configuration into bus semantics.
