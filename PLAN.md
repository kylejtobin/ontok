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
- The design is settled. No discovery phase precedes the build. Every provider and substrate behavior it depends on is confirmed against the NATS Server v2.14.6 source, the NATS documentation, the `nats-py` source, or the Pydantic documentation, as recorded below.

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
- The class is the kind. The only discriminators are an event's `event_type` and a reaction's `work_type`. Each is interchange identity, carried on the wire and in provider names, and is not a substitute for class identity. No other `type`, `kind`, `TypeId`, URI, or registry field exists.
- Standard event-sourcing vocabulary is used unless a different meaning requires a different name.
- Core does not change in this work.

### Construction is the program

- The reaction graph is the class-and-field dependency graph. No separate graph value, registration table, or subject-to-class dispatch exists.
- A genuine alternative is a union. Fan-out is several reactions consuming the same event type. A join is one reaction that consumes one event type and reads its counterpart.
- No scheduler, readiness flag, pending state, enabled set, or next-step field duplicates constructibility.
- No mapper, parser pipeline, handler chain, or orchestrator performs work that belongs to construction.
- A construction failure is not a workflow status.

### The live edge

- Frozen values hold no client, process, or handle.
- SDK objects are foreign evidence at the boundary and never cross the provider contract.
- A provider binding performs transport calls and serialization only.
- Consumption is a push subscription whose callback is registered once at the composition root. There is no receive loop.
- An arrival is an ordered union of the reaction's consumed event union and `Unconstructible`. No construction failure is caught.
- Transport facts, such as a delivery's token, stay in the delivery's values and never enter a reaction.
- Each delivery reads what it needs from the log through interpreters nested in its terminal expression. The log is the state. There is no mutable consistency model and no current-state holder.
- Every interpreter returns an outcome that carries its action, so the next stage is constructed from that outcome alone.
- The clock and randomness are effects, read through interpreters.
- Programming defects are not caught. A defect crashes the process, and redelivery makes it visible.

### Pydantic substrate

- Every semantic value is a strict, frozen Pydantic construction under the python-development standard. Refinements of Core primitives carry the finished configuration.
- No `dict`, untyped header map, metadata bag, or `bytes` payload carries meaning.
- Serialization occurs exactly once, at the provider binding, as the JSON of the event.
- An arrival is constructed whole from the delivered message. Its payload constructs as the reaction's consumed event union, discriminated by `event_type`.
- In a union that is not discriminated, every variant except the last carries a fact no other variant carries. Only the final variant may be empty, because an empty model has no refusal.
- No program code reads class metadata. What a kind declares is read through its published JSON Schema, constructed as a foreign model.

## Decisions

### Events

1. **The published thing is the event itself.** The log is the only durable store of events. Large originals live outside the log, and the event carries their digest.
2. **Event type.**
   - Every publishable kind is a refinement of Core `Event` carrying `event_type: Literal["<namespace>-<Class>"]`. The namespace is the top-level package that declares the kind.
   - The hyphen follows NATS naming guidance, so the name is valid as both a subject token and a consumer name, and it never occurs in a Python identifier.
   - An event type is interchange identity: renaming the class does not change it.
3. **Versioning.** An event type's shape never changes. A new shape is a new event type. Readers keep constructing every event type that exists in the log.
4. **Stream.** Every publishable kind derives `stream`, a `StreamKey` naming what the event is about. A stream key is a canonical lowercase UUIDv7 or a lowercase hex digest. An event that is its own stream uses its own id.
5. **Two acts of publication.**
   - An **originating** event is created by a source. It carries no causation.
   - An **emitted** event is derived by a reaction. It carries `causation: Causation`, which holds the reaction's `work_type`, the `trigger` (the id of the event that caused it), and its `position` among the reaction's emissions.
6. **Publication identity.** An originating event's publication identity is its id. An emitted event's publication identity is its causation.
7. **Node ids.**
   - The bus constructs UUIDv7s from a millisecond timestamp and 74 bits. Python 3.13 has no `uuid7`.
   - A source mints each originating event's id through the minting interpreter, from a clock instant and random bits.
   - Each delivery mints exactly one id, the reaction's.
   - An emitted event's id is the reaction's id with its position in the low 16 bits. A reaction emits at most 65,536 events.
   - A retry mints a different reaction id. Its emissions carry new ids but share the same causation, so they share a publication identity with the first attempt.
8. **Occurrence.** A delivery reads the clock once. Its reaction, and every event it emits, occurs at that instant.

### Addresses

9. **An address locates one publication in the log.**
   - An originating event's address is its stream, its event type, and its id.
   - An emitted event's address is its stream, its event type, and its causation.
   - An address holds at most one event.
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
| `AlreadyPresent` | `existing`, the sequence already holding it | this publication is already on the log; this is success |
| `Conflict` | `latest`, the stream's latest sequence | another event holds the position the expectation required |
| `Unavailable` | `reason` | the provider could not complete the append |

13. **Recognizing "already present".** When an expectation fails, the interpreter reads the event's own exact address.
    - If the address holds this publication, the outcome is `AlreadyPresent`.
    - If it is empty, the outcome is `Conflict`.

    This holds under every expectation. A retry therefore never appends a second copy, even when other events have landed in the stream since the first attempt.
14. There is no deduplication window. Idempotence holds for the life of the log.
15. **Events do not embed their prior.** Succession is enforced by `ExpectSequence`. The state-transition shape with a `prior` field is the in-memory fold a reaction uses to decide what to emit, never a wire shape.

### Reads

16. **The latest read.** `ReadLatest` names a stream and a scope. The scope is `OfType(event_type)`, which reads the latest event of one type in the stream, or `EveryType`, which reads the latest event in the stream.
    - The outcome is `Retained[S]`, the event and its log sequence, where `S` is the union read.
    - When nothing matches, the outcome is `Absent(stream)`.
    - On provider failure, the outcome is `Unavailable(reason)`.
    - The outcome is constructed through the `TypeAdapter` declared beside `S`.

### Subscriptions

17. **A subscription is a reaction's standing interest** in every event type it consumes, together with its progress.
    - Each reaction kind has exactly one.
    - It exists independently of any process.
    - Its name is the reaction's `work_type`.
    - Its deliver subject is `_INBOX.ontok.<work_type>`, fixed so that a callback stays bound across deletion and recreation.
    - The program creates it, and creating it again with the same configuration is idempotent.
18. **Start point:** from the beginning of the log or from the next event, declared by the reaction kind as `start: Literal[StartPoint.<member>]`.
19. **Order:** one event at a time, in log order across all of the reaction's consumed types. One ordered subscription makes joins race-free. The cost is throughput.
20. **Storage is infrastructure,** declared by the deployment and not created by the program. `ontok-nats` states the required stream specification, and its conformance suite verifies a deployment against it.
21. **The reaction specification** is constructed at registration from the JSON Schemas of three types the composition root binds: the reaction, its consumed union, and its counterpart when it declares one.
    - The `work_type` and `start` come from the reaction schema's `const` values.
    - The consumed event types come from the consumed union schema's discriminator mapping, or from its `event_type` `const` when it is a single kind.
    - The counterpart event type comes from the counterpart schema's `const`.

    Each schema is constructed as a foreign model. The specification is a value object, and the subscription and read actions derive from it.

### Delivery and disposition

22. **A delivery is the provider handing one event to one subscription,** possibly more than once. The delivery carries a `DeliveryToken`, the provider's acknowledgement address, and the event with its position.
23. **Dispositions, exactly three:**

| Disposition | Meaning | Used when |
|---|---|---|
| Complete | every consequence of the event is durable | the reaction was ready, every effect succeeded, and every append was `Written` or `AlreadyPresent` |
| Retry | deliver again | a `Conflict`, or an `Unavailable` from any interpreter |
| Reject | the delivery is terminal | the arrival is `Unconstructible` |

24. **The record of a rejection is the provider's own account.** The bus reads it and invents no second record.
25. **Failures.** Every interpreter translates its documented nonfatal failures into `Unavailable`. The application's effect outcomes are each a union of its own success variants and `Unavailable`. Anything else is a defect.
26. **Lease.** Before the effects of a delivery run, the delivery sends one in-progress acknowledgement. The acknowledgement wait therefore bounds the effects of one delivery, not the whole delivery.

### Reactions

27. **A reaction is a refinement of `Reaction(Work)`.**
    - It carries `work_type: Literal["<namespace>-<Class>"]` and `start: Literal[StartPoint.<member>]`.
    - It narrows `action` to its own `Action` refinement, whose `role` and `goal` are narrowed to its own `Role` and `Goal` refinements.
    - Its fields are its trigger, the retained consumed event; its `at`, the delivery's instant; its `id`, the delivery's minted id; and, for a join, its `counterpart`.
    - Each field is constructed from the delivery's `Circumstances` through an `AliasPath`.
28. **A reaction consumes one event union and reads at most one counterpart.** A join over more than two events is out of scope.
29. **Derivations,** each a transformation on the reaction:
    - `stream`, its trigger's stream;
    - `emits`, the tuple of `Emission` actions it authorizes;
    - `effects`, the tuple of the application's effect actions it authorizes.
30. **Readiness.** `Circumstances.readiness` is an ordered union. It tries the reaction kind's variants first, then `Unready`, then `Unconstructed`.
    - Domain alternatives are modeled as the reaction's own variants, so the reaction refuses only when the arrival is `Unconstructible` or the counterpart read is `Unavailable`.
    - `Unready` requires a delivered arrival, so it refuses only when the arrival is `Unconstructible`.
    - `Unconstructed` holds the `Unconstructible` arrival and is last.

    Every readiness variant derives `effects` and `emits`. `Unready` and `Unconstructed` derive empty tuples.
31. **Joins.** A join's reaction variants are `Joined`, whose counterpart is `Retained`, and `Partial`, whose counterpart is `Absent`. `Partial` emits nothing. The later arrival reads the earlier one and constructs `Joined`.
32. **Causation.** An emitted event references its trigger and the reaction kind that derived it. Reactions are never published. Causation is a relation between events and is never inferred from temporal order.
33. **Effects.** A reaction's effects outside the log are the application's actions, executed by the application's effect interpreters.
    - They are idempotent by event id or log sequence.
    - A read model's writes apply only when the incoming sequence is newer than the one stored.

### The delivery's terminal expression

34. **Each stage is an action whose interpreter returns an outcome carrying that action,** and each next action is a derivation on the previous outcome:

| Stage | Action | Interpreter | Outcome |
|---|---|---|---|
| 1 | `ReadClock` | bus clock | `Instant` |
| 2 | `MintIdentity(at)` | bus minting | `Minted(at, id)` |
| 3 | `ReadCounterpart(arrival, specification, minted)`; it derives zero or one `ReadLatest` from the arrival's variant | NATS | `Circumstances(arrival, minted, counterpart)`, where `counterpart` is a tuple of zero or one read outcomes |
| 4 | `ExtendLease(circumstances)`; it derives zero or one token from the arrival's variant | NATS | `LeaseExtended(extension, outcomes)` |
| 5 | `PerformEffects[A](lease, effects)`, with `effects` taken from the readiness | application | `EffectsSucceeded[S] \| EffectsFailed`, attempted in that order; `EffectsSucceeded[S]` requires every outcome to be a success variant `S` |
| 6 | `AppendEmissions(performed, emissions)`; its emissions come from the readiness when the effects succeeded, and are empty when they failed | NATS | `EmissionsAppended(appending, outcomes)` |
| 7 | `Dispose(token, disposition)`, derived as the settlement's `disposal` | NATS | `Disposed` |

35. **Settlement.** `EmissionsAppended.settlement` is an ordered union.
    - `Rejected` is attempted first. It requires the readiness to be `Unconstructed`, so it refuses whenever the arrival was delivered.
    - `Completed` is next. It requires a ready reaction, `EffectsSucceeded`, and appends that are all `Written` or `AlreadyPresent`. Given a delivered arrival, its only refusal is deferral.
    - `Deferred` is last.
    - Each variant derives `disposal`.
36. **The whole delivery is one expression,** stages 1 to 7 nested by data dependency, registered once per reaction kind at the composition root. A crash at any stage is followed by redelivery. The causation addresses and the rule in decision 13 make it converge.

### Replay

37. **Replay is a chain of three actions,** each derived from the previous action's outcome:
    1. `DeleteSubscription(work_type)` returns `SubscriptionDeleted`;
    2. the projection's `reset` action, derived from `SubscriptionDeleted`, returns the application's reset outcome;
    3. `EnsureSubscription`, derived from that outcome with the start point set to the beginning, returns `SubscriptionEnsured`.

    Deleting the subscription first stops deliveries before the read model is cleared. The fixed deliver subject keeps the registered callback receiving after recreation.
38. **Replay is evaluated at the composition root** as one expression, on the application's operator instruction. How that instruction arrives belongs to the application. The acceptance test evaluates it directly.
39. `Projection(Reaction)` is a reaction that maintains a read model and derives `reset`, the action that clears it.

### Composition root

40. **The composition root binds, once:**
    - configuration and the provider client;
    - the application's effect interpreters;
    - for each reaction kind, its specification, its subscription through the `EnsureSubscription` interpreter, and its callback, registered through the client's push subscription on the fixed deliver subject with manual acknowledgement.

    The callback's body is the delivery's terminal expression.
41. **Rules and contexts** are domain facts a reaction reads through its fields. They are never scheduler state. Evaluating them is not an execution concern of this work.

### Idempotence and ownership

42. Idempotence has one home per layer:
    - the bus owns idempotent appends;
    - `ontok-ex` owns causation for every emitted event;
    - the domain owns pure construction.

### Provider contract

43. **The bus defines each operation as an action with a constructed outcome:**
    - `Origination[E]` and `Emission[E]`, each with an expectation;
    - `ReadLatest`;
    - `EnsureSubscription` and `DeleteSubscription`;
    - `ExtendLease` and `Dispose`;
    - `ReadClock` and `MintIdentity`.

    A provider implements the transport actions as effect interpreters. The bus implements the clock and minting itself.
44. Contracts accept and return constructed events, never SDK objects. There is no generic publish or subscribe surface.
45. **A bus provider offers:**
    - conditional append on an exact address and on a whole stream;
    - the latest read of one type or of every type in a stream, and of one exact address;
    - durable ordered push subscriptions on a fixed deliver address, with explicit disposition and lease extension;
    - an account of rejected deliveries.

    A provider without them is not a bus provider. The bus does not simulate what a provider lacks.
46. Provider vocabulary, configuration, and policy stay in the provider package.

### NATS realization

47. **Subjects.**
    - An originating event's subject is `event.<stream>.<event_type>.<id>`.
    - An emitted event's subject is `event.<stream>.<event_type>.<work_type>.<trigger>.<position>`.
48. **Stream specification:**
    - the stream `EVENTS` per account, holding `event.>`;
    - file storage;
    - limits retention with no limits;
    - `deny_delete` and `deny_purge`;
    - `allow_direct`.
49. **Conditional publish headers:**
    - `ExpectAny` sends `Nats-Expected-Last-Subject-Sequence: 0` on the event's exact subject;
    - `ExpectNoStream` and `ExpectSequence` add `Nats-Expected-Last-Subject-Sequence-Subject: event.<stream>.>`, with `0` or the sequence.
50. **Reads** are requests to `$JS.API.DIRECT.GET.EVENTS` in the body form, `{"last_by_subj": "<subject>"}`:
    - `OfType` reads `event.<stream>.<event_type>.>`;
    - `EveryType` reads `event.<stream>.>`;
    - the own-address check in decision 13 reads the event's exact subject.

    A 404 status is `Absent`.
51. **Consumer settings:**
    - a durable push consumer named with the reaction's `work_type`;
    - `filter_subjects` of `event.*.<event_type>.>` for each consumed event type;
    - the deliver subject `_INBOX.ontok.<work_type>`;
    - explicit acknowledgement;
    - `max_ack_pending` of 1;
    - an acknowledgement wait of 30 seconds;
    - unlimited deliveries;
    - deliver-all or deliver-new, following the start point;
    - no flow control.

    `EnsureSubscription` creates it through the JetStream consumer API. The composition root binds the callback with the client's `subscribe_bind` and manual acknowledgement.
52. **Dispositions through the delivery token:**
    - Complete is a request of `+ACK` to the token, which confirms it;
    - Retry is a publish of `-NAK`;
    - Reject is a publish of `+TERM`;
    - lease extension is a publish of `+WPI`.

    Rejections are read from `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.EVENTS.<consumer>`.
53. **A program identity has exactly these permissions,** and no stream administration:
    - publish on `event.>`;
    - publish on `$JS.API.INFO`;
    - publish on `$JS.API.STREAM.INFO.EVENTS`;
    - publish on `$JS.API.DIRECT.GET.EVENTS`;
    - publish on `$JS.API.CONSUMER.CREATE.EVENTS` and `$JS.API.CONSUMER.CREATE.EVENTS.>`;
    - publish on `$JS.API.CONSUMER.INFO.EVENTS.*` and `$JS.API.CONSUMER.DELETE.EVENTS.*`;
    - publish on `$JS.ACK.EVENTS.>` and `$JS.ACK.*.*.EVENTS.>`;
    - subscribe on `_INBOX.>` and on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.EVENTS.>`.

## Verified behavior

- **Latest read across a wildcard.** NATS Server v2.14.6 serves direct get's `last_by_subj` through `store.LoadLastMsg`, at `stream.go` line 6093. The file store's `loadLastLocked` branches on `subjectHasWildcard` and scans every matching subject, and request validation does not reject a wildcard.
- **The body form is required.** `nats-py` 2.16's `get_msg(direct=True, subject=...)` sends the subject form, `$JS.API.DIRECT.GET.<stream>.<subject>`, and a request subject cannot contain a wildcard. The interpreter sends the body form itself.
- **Conditional publish across a wildcard.** `Nats-Expected-Last-Subject-Sequence-Subject` replaces the checked subject and calls the same `store.LoadLastMsg`, at `stream.go` lines 6453 to 6479. An expected `0` with no match passes.
- **Consumer creation.** A consumer with several `filter_subjects`, available from server 2.10, is created on `$JS.API.CONSUMER.CREATE.<stream>`, so its permission is scoped by stream.
- **Names.** NATS stream and consumer names cannot contain whitespace, `.`, `*`, `>`, path separators, or non-printable characters. The documentation recommends alphanumeric characters, `-`, and `_`.
- **Acknowledgement payloads.** `nats-py` acknowledges with `+ACK`, `-NAK`, `+TERM`, and `+WPI` on the message's reply subject. Its `ack_sync` is a request on that subject.
- **Push binding.** `nats-py`'s `subscribe_bind` binds a callback to an existing consumer's deliver subject. `ConsumerConfig` carries `filter_subjects`, `deliver_subject`, `max_ack_pending`, `ack_wait`, and `deliver_policy`.
- **Terminate advisory.** A terminate publishes on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.<stream>.<consumer>`. Its payload carries the stream, the consumer, the stream sequence, the consumer sequence, and the delivery count.
- **Schemas.** Pydantic's JSON Schema renders a `Literal` field as a `const`, and a discriminated union with a `discriminator` whose `mapping` keys are the discriminator values.

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
| `ExpectSequence`, `ExpectNoStream`, `ExpectAny` | value objects; `Expectation` is their union, constructed only in code | `publication.py` |
| `OriginAddress`, `EmissionAddress` | value objects | `publication.py` |
| `Origination[E]`, `Emission[E]` | actions, each deriving `address` | `publication.py` |
| `Written`, `AlreadyPresent`, `Conflict` | value objects; the append outcome is their union with `Unavailable` | `publication.py` |
| `OfType`, `EveryType` | value objects; the read scope is their union | `read.py` |
| `ReadLatest` | action: `stream`, `scope` | `read.py` |
| the latest-read outcome | union: `Retained[S] \| Absent \| Unavailable` | `read.py` |
| `EnsureSubscription`, `DeleteSubscription` | actions | `subscription.py` |
| `SubscriptionEnsured`, `SubscriptionDeleted` | value objects | `subscription.py` |
| `Delivery[C]` | value object: `token`, `event` as `Retained[C]` | `delivery.py` |
| `Unconstructible` | value object: `token` | `delivery.py` |
| the arrival | ordered union: `Delivery[C] \| Unconstructible` | `delivery.py` |
| `ExtendLease`, `Dispose` | actions | `delivery.py` |
| `LeaseExtended`, `Disposed` | value objects | `delivery.py` |
| UUIDv7 composition from a millisecond timestamp and 74 bits | transformation | `identity.py` |
| `EmittedIdentity` | transformation: `work`, `position`; derives `id` | `identity.py` |
| `ReadClock`, `MintIdentity` | actions | `identity.py` |
| `Minted` | value object: `at`, `id` | `identity.py` |
| `ClockInterpreter`, `MintInterpreter` | effect interpreters; capabilities are UTC `tzinfo` and `random.SystemRandom` | `interpreter.py` |

### `ontok-nats`

| Declaration | Construct | File |
|---|---|---|
| `NatsSettings` | config, prefix `ONTOK_NATS_`: URL, user, and password as `SecretStr` | `config.py` |
| `StreamSpecification` | value object | `stream.py` |
| the publish acknowledgement, the API error with its wrong-last-sequence code, the direct-get reply, the terminate advisory | foreign models | `model.py` |
| `DeliveryRoute` | route: lifted from the NATS message with `from_attributes=True`; the token from `reply`, the payload through `Json[C]`, the sequence through an `AliasPath` into the message metadata | `route.py` |
| append, latest read, counterpart read, lease extension, subscription creation, subscription deletion, disposal | one effect interpreter per action meaning; each returns an outcome carrying its action, composes its subject at the client call, and catches only its documented errors | `interpreter.py` |

### `ontok-ex`

| Declaration | Construct | File |
|---|---|---|
| the reaction schema, the consumed-union schema, the counterpart schema | foreign models over Pydantic's JSON Schema | `model.py` |
| `ReactionSpecification` | value object: `work_type`, consumed event types, counterpart event type, `start`; derives `subscription` and `deletion` | `specification.py` |
| `Reaction(Work)` | concept model | `reaction.py` |
| `Projection(Reaction)` | concept model; derives `reset` | `reaction.py` |
| `ReadCounterpart` | action | `circumstances.py` |
| `Circumstances` | value object: `arrival`, `minted`, `counterpart`; derives `readiness` | `circumstances.py` |
| `Unready` | value object: `arrival` as `Delivery`, `counterpart` | `circumstances.py` |
| `Unconstructed` | value object: `arrival` as `Unconstructible` | `circumstances.py` |
| `PerformEffects[A]` | action | `effects.py` |
| `EffectsSucceeded[S]`, `EffectsFailed` | value objects; the effects outcome is their ordered union | `effects.py` |
| `AppendEmissions` | action | `emissions.py` |
| `EmissionsAppended` | value object; derives `settlement` | `emissions.py` |
| `Rejected`, `Completed`, `Deferred` | value objects; settlement is their ordered union; each derives `disposal` | `settlement.py` |

The application declares its events and their stream and counterpart unions, its reactions with their variants and their narrowed `Action`, `Role`, and `Goal`, its effect actions with their outcome unions and interpreters, and its composition root.

## Order

1. **`ontok-bus`,** with every declaration in its construct table.
2. **`ontok-nats`.**
   - The realization in decisions 47 to 53.
   - The stream specification as a value.
   - The bundled server, license, and manifest moved in, unused.
   - A test fixture that starts `nats:2.14.6-alpine@sha256:ad7a43eb7e3337c3c38ce5d784d1461791f95f730f252d2b25eee699752a0ca3` through testcontainers, with accounts, a scoped program identity, and the `EVENTS` stream.
   - The conformance suite against that server, covering:
     - routing by event type;
     - idempotent appends under each expectation, including a retry after another event has landed in the stream;
     - conflicts under `ExpectNoStream` and `ExpectSequence`;
     - the latest read of one type, of every type, and of an exact address, and `Absent`;
     - push ordering across several filter subjects;
     - lease extension;
     - durability across a restart;
     - the three dispositions and the terminate advisory;
     - a callback bound to the fixed deliver subject surviving consumer deletion and recreation;
     - refusal of stream administration to a program identity.
3. **`ontok-ex`.**
   - Every declaration in its construct table.
   - Specification construction from schemas.
   - The data-directory config and its test removed.
   - Tests against the real server, covering:
     - chaining;
     - fan-out;
     - a join, both partial and joined;
     - an alternative;
     - redelivery without duplication;
     - a crash at each stage before completion;
     - rejection of `Unconstructible`;
     - retry on conflict;
     - retry on an unavailable counterpart read, through `Unready`;
     - retry on an unavailable effect, through `EffectsFailed`;
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
- The effects of one delivery running longer than the 30-second acknowledgement wait.
- A join over more than two events.
- Multiple providers.
- Cross-platform wheels and distributing the bundled server.
- Clustering, federation, leaf nodes, and gateways.
- Key-value and object stores, and request and reply.
- How an application delivers an operator's replay instruction.
- Tracing.
- Liveness.
- Evaluating rules and contexts.

## Interchange standards

CloudEvents, AsyncAPI, and W3C Trace Context are projections and interoperability assets. They do not define this programming model and are not copied into these packages.

## Open for Core

- **Embedding versus reference.** Core `Work` embeds a whole `Action`, and Core `Connection` embeds its endpoints. Reactions are not published, so the identical embedded action exists only in memory. The question stands on its own merits: whether a primitive embeds a node or references it by identity.
- **Configuration of Core's finished values.** `NodeId`, `Timestamp`, `PositiveDuration`, `Instant`, `Interval`, and `States` are finished values, not bases for refinement, and they declare only `frozen` and `extra`. Events embed them as Core constructs them.

Both are decided from the evidence this work produces, not within it.

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
- Do not pass a delivery token or any other transport fact into a reaction.
- Do not hash to derive identity.
- Do not read class metadata. Read a kind's declarations through its JSON Schema.
- Do not place an empty variant anywhere but last in a union that is not discriminated.
- Do not flatten logs, queues, streams, subjects, and consumers into one string field.
- Do not turn provider configuration into bus semantics.
