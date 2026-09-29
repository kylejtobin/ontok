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
- The design is settled. No discovery phase precedes the build. Every construct is routed through the python-development skill. Every provider behavior it depends on is confirmed against the NATS Server v2.14.6 source, the NATS documentation, or the `nats-py` source, as recorded below.

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

- Every identified kind a program declares is a refinement of a Core primitive: its events refine `Event`, its reactions refine `Work`, and a reaction kind's action, role, and goal refine `Action`, `Role`, and `Goal`.
- Identityless facts and values are python-development constructs, not Core kinds, as Core's own `NodeId`, `Timestamp`, `Instant`, and `Interval` are. The retained event, the delivery, the attempt, a response's deferral and rejection, and every outcome are such facts.
- The skill's effect actions describe external effects. They are not Core `Action`s.
- Core primitives are not used raw where a narrower meaning exists.
- There is no `Event(Event)`. Core `Event` remains the universal occurrence, and Core `Work` remains the persistent undertaking.
- The class is the kind. The only discriminators are an event's `event_type` and a reaction kind's `work_type`. Each is interchange identity: `event_type` travels on the wire and in subjects, and `work_type` travels in causation, subjects, and provider names. Neither substitutes for class identity. No other `type`, `kind`, `TypeId`, URI, or registry field exists.
- Standard event-sourcing vocabulary is used unless a different meaning requires a different name.
- Core does not change in this work.

### Construction is the program

- The reaction graph is the class-and-field dependency graph. No separate graph value, registration table, or subject-to-class dispatch exists.
- A genuine alternative is a union. Fan-out is several reactions consuming the same event type. A join is one reaction that consumes two event types in one stream.
- No scheduler, readiness flag, pending state, enabled set, or next-step field duplicates constructibility.
- No mapper, parser pipeline, handler chain, or orchestrator performs work that belongs to construction.
- A construction failure is not a workflow status.

### The live edge

- Frozen values hold no client, process, or handle.
- SDK objects are foreign evidence at the boundary and never cross the provider contract.
- A provider binding performs transport calls and serialization only.
- Consumption is a push subscription whose callback is registered once at the composition root. There is no receive loop.
- An arrival is an ordered union of the delivery of the reaction's consumed event union and `Unconstructible`. No construction failure is caught.
- Transport facts, such as a delivery's token, never enter a reaction. The callback reads the token from its route input.
- Every action carries only its own semantic input. An outcome couples the action that produced it, and an outcome that authorizes a further effect derives that effect's action.
- An action that follows an outcome union holds that union and derives what it authorizes through a failure-exhaustive ordered union: the strong variant requires the authorizing outcome, and the fallback authorizes nothing.
- Each delivery reads what it needs from the log through interpreters nested in its terminal expression. The log is the state. There is no mutable consistency model and no current-state holder.
- The clock and randomness are effects, read through interpreters.
- Programming defects are not caught. A defect crashes the process, and redelivery makes it visible.

### Pydantic substrate

- Every semantic value is a strict, frozen Pydantic construction under the python-development standard. Refinements of Core primitives carry the finished configuration.
- No `dict`, untyped header map, metadata bag, or `bytes` payload carries meaning.
- Serialization occurs exactly once, at the provider binding, as the JSON of the event.
- An arrival is constructed whole from the delivered message. Its payload constructs as the reaction's consumed event union, discriminated by `event_type`.
- In a union that is not discriminated and is constructed from raw input, every variant except the last carries a fact no other variant carries. Only the final variant may be empty, because an empty model has no refusal.
- No program code reads class metadata, except subscription compilation, which lifts Pydantic's JSON Schema of a reaction kind and its consumed union through foreign models.

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
   - An **emitted** event is derived by a reaction. It carries `causation: Causation`, which holds the reaction kind's `work_type`, the `trigger` (the id of the event that caused it), and its `position` among the reaction's emissions.
6. **Publication identity.** An originating event's publication identity is its id. An emitted event's publication identity is its causation.
7. **Node ids.**
   - The bus constructs UUIDv7s from a millisecond timestamp and 74 bits. Python 3.13 has no `uuid7`.
   - A source mints each originating event's id through the minting interpreter, from a clock instant and random bits.
   - Each delivery mints exactly one id, the reaction's.
   - An emitted event's id is the reaction's id with its position in the low 16 bits.
   - A retry mints a different reaction id. Its emissions carry new ids but share the same causation, so they share a publication identity with the first attempt.
8. **Occurrence.** A delivery reads the clock once. Its reaction, and every event it emits, occurs at that instant.

### Addresses

9. **An address locates one publication in the log.**
   - An originating event's address is its stream, its event type, and its id.
   - An emitted event's address is its stream, its event type, and its causation.
   - An address holds at most one event.
10. Accounts isolate organizations, so addresses carry no organization prefix.

### Appends

11. **Every appended event carries exactly one expectation:**

| Expectation | Holds when |
|---|---|
| `ExpectAny` | nothing is at the event's own address |
| `ExpectNoStream` | the stream holds no event |
| `ExpectSequence(sequence)` | the latest event in the stream has that sequence |

12. **Two append actions.** `Origination[E]` appends one originating event. `AppendBatch[A]` appends a reaction's emissions atomically: every emission lands or none does. It holds the emissions and their `authority`, the response or performed fact that authorized them. A batch holds at most 1,000 emissions, the provider's atomic batch limit.
13. **Expectations in a batch.** Within one batch, only the first emission into a stream may carry a stream expectation. Every other emission carries `ExpectAny`.
14. **The provider's answer** couples its append action and is one of three:
    - `Written(append, sequences)`: every event landed;
    - `Contested(append)`: an expectation failed;
    - `Unavailable(reason)`: the provider did not complete the append.

    An empty batch makes no provider call and is `Written` with no sequences.
15. **Settling a contest.** `AppendCheck` holds the provider's answer. Through a failure-exhaustive ordered union, a `Contested` answer authorizes one `ReadAddress` of the first appended event's address, and every other answer authorizes none. Because a batch is atomic, one address answers for the whole batch. The address-read interpreter returns `AppendSettlement(check, readings)`, which derives the append's outcome as an ordered union:

| Outcome | Constructs when | Meaning |
|---|---|---|
| `Written` | the answer was `Written` | the events were appended |
| `AlreadyPresent(append, existing)` | the answer was `Contested` and the address holds an event | this publication is already on the log; this is success |
| `Conflict(append)` | the answer was `Contested` and the address is empty | another event holds the position the expectation required |
| `AppendUnavailable` | anything else | the answer or the address read was unavailable |

    A retry therefore never appends a second copy, even when other events have landed in the stream since the first attempt.
16. There is no deduplication window. Idempotence holds for the life of the log.
17. **Events do not embed their prior.** Succession is enforced by `ExpectSequence`. The state-transition shape with a `prior` field is the in-memory fold a reaction uses to decide what to emit, never a wire shape.

### Reads

18. **The latest read.** `ReadLatest` names a stream and a scope. The scope is `OfType(event_type)`, which reads the latest event of one type in the stream, or `EveryType`, which reads the latest event in the stream. `ReadAddress` names one address.
    - The outcome is `Retained[S]`, the event and its log sequence, where `S` is the union read.
    - When nothing matches, the outcome is `Absent(stream)`.
    - On provider failure, the outcome is `Unavailable(reason)`.
    - The outcome is constructed through the `TypeAdapter` declared beside `S`.
19. **Reads see the log as it is now.** The provider has no latest read as of an earlier sequence.
20. **Readings.** A read interpreter executes a tuple of authorized reads and returns `Readings[S]`, the collection of their outcomes in the same order. Readings derive their `completeness` through a failure-exhaustive ordered union: `AllRead` requires every outcome to be `Retained` or `Absent`, and `SomeUnavailable` is the fallback.

### Subscriptions

21. **A subscription is a reaction kind's standing interest** in every event type it consumes, together with its progress.
    - It is the value `Subscription(work_type, event_types, start)`.
    - Each reaction kind has exactly one.
    - It exists independently of any process.
    - Its name and its deliver group are the reaction kind's `work_type`, so each delivery reaches exactly one running instance.
    - Its deliver subject is `_INBOX.ontok.<work_type>`, fixed so that a callback stays bound across deletion and recreation.
    - `EnsureSubscription(subscription)` creates it, and creating it again with the same configuration is idempotent. `DeleteSubscription(subscription)` removes it.
22. **Start point:** from the beginning of the log or from the next event, set in the subscription at the composition root.
23. **Order:** one event at a time, in log order across all of the reaction kind's consumed types.
24. **Storage is infrastructure,** declared by the deployment and not created by the program. `ontok-nats` states the required stream specification, and its conformance suite verifies a deployment against it.
25. **The specification** of a reaction kind is compiled at registration.
    - The composition root lifts Pydantic's JSON Schema of the reaction kind and of its consumed union through foreign models.
    - The reaction kind's `work_type` comes from its schema's `const`.
    - The consumed event types come from the union's discriminator mapping, or from its `event_type` `const` when it is a single kind.
    - The composition root constructs the matching specification explicitly:
      - a `ReactionSpecification` for a reaction that emits;
      - a `JoinSpecification` for a join, which requires exactly two consumed types;
      - a `ProjectionSpecification` for a projection.
    - Each specification derives `scopes`, the reads every delivery of that kind requires:
      - `EveryType` for a reaction;
      - `OfType` for each of a join's two consumed types, in the consumed union's declared order;
      - none for a projection.

### Delivery

26. **A delivery is the provider handing one event to one subscription,** possibly more than once. `Delivery[C]` carries a `DeliveryToken`, the provider's acknowledgement address, and the event as `Retained[C]`. `Unconstructible` carries only the token. Each derives `streams`: the delivered event's stream, or none.
27. **Dispositions, exactly three:**

| Disposition | Meaning | Derived by |
|---|---|---|
| Complete | every consequence of the event is durable | a reaction, or a performed response whose effects all held, whose appends were `Written` or `AlreadyPresent` |
| Retry | deliver again | a deferral, an unavailable effect, a `Conflict`, or an `AppendUnavailable` |
| Reject | the delivery is terminal | a rejection |

28. **The provider keeps its own record of rejections** for operators. The bus reads no rejection record.
29. **Failures.** Every transport interpreter translates its documented nonfatal failures into `Unavailable`, so every transport outcome is a union that includes it. The clock and minting have no documented failures, so their outcomes are plain. The application's effect outcomes are each a union of its own success variants and `Unavailable`. Anything else is a defect.
30. **The acknowledgement wait bounds the whole delivery.** A delivery that runs longer is redelivered while it runs, and idempotence absorbs the repetition.

### The delivery's facts

31. **`Inquiry(specification, arrival)`** derives the delivery's `reads`: one `ReadLatest` for each of the arrival's streams and each of the specification's scopes. An `Unconstructible` arrival has no streams, so it authorizes no reads.
32. **`Attempt(arrival, minted, readings)`** is one delivery attempt: the arrival, the delivery's minted instant and id, and the readings of its inquiry.
33. **The response** is constructed from the attempt through the `TypeAdapter` declared beside the reaction kind's response union. That union is a plain union:
    - the reaction kind's own variants, each requiring a `Delivery` arrival and `AllRead` readings;
    - `Deferred`, requiring `SomeUnavailable` readings;
    - `Rejected`, requiring an `Unconstructible` arrival.

    Exactly one variant constructs. A reaction that refuses for any other reason constructs nothing, and the process crashes as a defect.
34. **Every response variant derives** its `emissions`, its `effects`, its `batch` as `AppendBatch(emissions, authority)`, and its `disposition`:
    - a reaction variant derives Complete;
    - `Deferred` derives Retry;
    - `Rejected` derives Reject.

    `Deferred` and `Rejected` authorize no emissions and no effects.
35. **Performing effects.** `PerformEffects(response)` carries the response as its idempotency key and requests the effects it authorizes.
    - The application's effect interpreter executes them through its one capability and returns `Performed(action, outcomes)`.
    - `Performed` derives its `completeness` through a failure-exhaustive ordered union: `EffectsHeld` requires every outcome to be a success variant, and `EffectsUnavailable` is the fallback.
    - `EffectsHeld` derives the response's emissions and disposition.
    - `EffectsUnavailable` derives no emissions and Retry.
    - `Performed` derives its `batch` with itself as the authority.
36. **Effects precede emissions.** An emission announces a consequence, so the effect outcome authorizes it.
37. **The final disposition.**
    - `Written` and `AlreadyPresent` derive their batch authority's disposition.
    - `Conflict` and `AppendUnavailable` derive Retry.
38. **The terminal fact is `Disposed`.** The callback constructs `Dispose(token, disposition)` from the route's arrival token and the final disposition. The dispose interpreter publishes it.
39. **The terminal expression** nests, by data dependency:
    - the clock and minting interpreters;
    - the read interpreter over the inquiry's reads;
    - the attempt and its response;
    - for a kind with effects, the effect interpreter;
    - for a kind that emits, the batch append interpreter and the address-read interpreter;
    - the dispose interpreter.

    Each kind's callback nests only the interpreters its declarations need. A crash at any point is followed by redelivery, and the causation addresses and the settling of contests make it converge.

### Reactions

40. **A reaction kind is a refinement of `Reaction(Work)`.**
    - It carries `work_type: Literal["<namespace>-<Class>"]`.
    - It narrows `action` to its own `Action` refinement, whose `role` and `goal` narrow to its own `Role` and `Goal` refinements.
    - The action, role, and goal default to the kind's single instances, each with a fixed UUIDv7 id. The omission meaning is that a reaction of this kind undertakes this kind's action.
    - The reaction's fields are constructed from the attempt through `AliasPath`s: its trigger, as the retained consumed event; its `at`, as the minted instant; its `id`, as the minted id; and the retained readings it declares.
41. **Derivations,** each a transformation on the reaction:
    - `stream`, its trigger's stream;
    - `emissions`, the tuple of `Emission` actions it authorizes;
    - `effects`, the application's effect actions it authorizes.
42. **Emission expectations.**
    - A reaction reads the latest event of any type in its trigger's stream. Its first emission into that stream expects that event's sequence.
    - Every other emission, including every join emission, expects nothing at its own address.
43. **Joins.**
    - A join consumes two event types in one stream and reads the latest event of each.
    - Its variants take those readings by position.
    - `Joined` requires both retained. Each `Partial` variant requires one absent, and emits nothing.
    - Because reads see the log as it is now, a lagging subscription can construct `Joined` at both arrivals. `Joined` therefore takes as its causation trigger the later of its two events by log sequence. Both arrivals produce the same publication, and the log keeps one.
    - A join across streams, or over more than two event types, is out of scope.
44. **Causation.** An emitted event references its trigger and the reaction kind that derived it. Reactions are never published. Causation is a relation between events and is never inferred from temporal order.
45. **Effects.**
    - A reaction kind's effects run through exactly one capability. Effects on two systems are two reaction kinds consuming the same event.
    - Effects are idempotent by event id or log sequence.
    - A read model's writes apply only when the incoming sequence is newer than the one stored, and each write sets its key to the value at that sequence.
46. **`Projection(Reaction)`** is a reaction kind that maintains a read model. It performs effects and emits nothing. Its application declares the reset action that clears the read model.

### Replay

47. **Replay is three effects, each authorized by the previous outcome:**
    - `DeleteSubscription(subscription)` returns `SubscriptionDeleted(subscription)`, which authorizes the projection's reset;
    - the reset's outcome authorizes `EnsureSubscription` of the same subscription from the beginning of the log;
    - that returns `SubscriptionEnsured`.

    Each step derives its successor through the failure-exhaustive ordered union in the live-edge invariant, so an unavailable step authorizes nothing further.
48. **The in-flight race is harmless.** A delivery still running during replay can write after the reset. Its write sets its key to the value at its sequence, which is the value replay itself produces there. Acknowledgements sent to a deleted consumer are dropped.
49. **Replay is evaluated at the composition root** as one expression, on the application's operator instruction. How that instruction arrives belongs to the application. The acceptance test evaluates it directly.

### Composition root

50. **The composition root binds, once:**
    - configuration and the provider client;
    - the clock, minting, and provider interpreters, and the application's effect interpreters;
    - for each reaction kind, its specification, its subscription through the `EnsureSubscription` interpreter, and its callback, registered with the client's push binding on the fixed deliver subject with manual acknowledgement.

    The callback's input is the delivery route. Its body is the delivery's terminal expression.
51. **Rules and contexts** are domain facts a reaction reads through its fields. They are never scheduler state. Evaluating them is not an execution concern of this work.

### Idempotence and ownership

52. Idempotence has one home per layer:
    - the bus owns idempotent appends and the settling of contests;
    - `ontok-ex` owns causation for every emitted event;
    - the domain owns pure construction.

### Provider contract

53. **The bus defines each operation as an action with a constructed outcome:**
    - `Origination[E]` and `AppendBatch[A]`;
    - `ReadLatest` and `ReadAddress`;
    - `EnsureSubscription` and `DeleteSubscription`;
    - `Dispose`;
    - `ReadClock` and `MintIdentity`.

    A provider implements the transport actions as effect interpreters. The bus implements the clock and minting itself.
54. Contracts accept and return constructed events, never SDK objects. There is no generic publish or subscribe surface.
55. **A bus provider offers:**
    - conditional append on an exact address and on a whole stream;
    - atomic batch append;
    - the latest read of one type or of every type in a stream, and of one exact address;
    - durable ordered push subscriptions on a fixed deliver address with a deliver group and explicit disposition.

    A provider without them is not a bus provider. The bus does not simulate what a provider lacks.
56. Provider vocabulary, configuration, and policy stay in the provider package.

### NATS realization

57. **Subjects.**
    - An originating event's subject is `event.<stream>.<event_type>.<id>`.
    - An emitted event's subject is `event.<stream>.<event_type>.<work_type>.<trigger>.<position>`.
58. **Stream specification:**
    - the stream `EVENTS` per account, holding `event.>`;
    - file storage;
    - limits retention with no limits;
    - `deny_delete` and `deny_purge`;
    - `allow_direct`;
    - `allow_atomic`.
59. **Conditional publish headers:**
    - `ExpectAny` sends `Nats-Expected-Last-Subject-Sequence: 0` on the event's exact subject;
    - `ExpectNoStream` and `ExpectSequence` add `Nats-Expected-Last-Subject-Sequence-Subject: event.<stream>.>`, with `0` or the sequence.
60. **Atomic batches.** Each emission is published with `Nats-Batch-Id`, `Nats-Batch-Sequence` from 1, and, on the last, `Nats-Batch-Commit: 1`. The commit is a request, and its reply is the acknowledgement for the whole batch. `nats-py` has no batch call, so the interpreter sets these headers itself.
61. **Answers.** A publish acknowledgement is `Written`. API error `10071`, wrong last sequence, is `Contested`. Every other documented failure is `Unavailable`.
62. **Reads** are requests to `$JS.API.DIRECT.GET.EVENTS` in the body form, `{"last_by_subj": "<subject>"}`:
    - `OfType` reads `event.<stream>.<event_type>.>`;
    - `EveryType` reads `event.<stream>.>`;
    - `ReadAddress` reads the address's exact subject.

    A 404 status is `Absent`.
63. **Consumer settings:**
    - a durable push consumer named with the reaction kind's `work_type`;
    - `filter_subjects` of `event.*.<event_type>.>` for each consumed event type;
    - the deliver subject `_INBOX.ontok.<work_type>`;
    - the deliver group `<work_type>`;
    - explicit acknowledgement;
    - `max_ack_pending` of 1;
    - an acknowledgement wait of 30 seconds;
    - unlimited deliveries;
    - deliver-all or deliver-new, following the start point;
    - no flow control.

    `EnsureSubscription` creates it through the JetStream consumer API. The composition root binds the callback with the client's `subscribe_bind` and manual acknowledgement, which subscribes with the deliver group as its queue.
64. **Dispositions** are publishes to the delivery token:
    - Complete publishes `+ACK`;
    - Retry publishes `-NAK`;
    - Reject publishes `+TERM`.
65. **A program identity has exactly these permissions,** and no stream administration:
    - publish on `event.>`;
    - publish on `$JS.API.INFO`;
    - publish on `$JS.API.STREAM.INFO.EVENTS`;
    - publish on `$JS.API.DIRECT.GET.EVENTS`;
    - publish on `$JS.API.CONSUMER.CREATE.EVENTS` and `$JS.API.CONSUMER.CREATE.EVENTS.>`;
    - publish on `$JS.API.CONSUMER.INFO.EVENTS.*` and `$JS.API.CONSUMER.DELETE.EVENTS.*`;
    - publish on `$JS.ACK.EVENTS.>` and `$JS.ACK.*.*.EVENTS.>`;
    - subscribe on `_INBOX.>`.

## Verified behavior

- **Latest read across a wildcard.** NATS Server v2.14.6 serves direct get's `last_by_subj` through `store.LoadLastMsg`, at `stream.go` line 6093. The file store's `loadLastLocked` branches on `subjectHasWildcard` and scans every matching subject, and request validation does not reject a wildcard.
- **Reads are as of now.** A single `last_by_subj` read calls `LoadLastMsg` and ignores `up_to_seq`. Only `multi_last` honors `up_to_seq`, and it returns the last message of every distinct matching subject, which here is every event.
- **The body form is required.** `nats-py` 2.16's `get_msg(direct=True, subject=...)` sends the subject form, `$JS.API.DIRECT.GET.<stream>.<subject>`, and a request subject cannot contain a wildcard. The interpreter sends the body form itself.
- **Conditional publish across a wildcard.** `Nats-Expected-Last-Subject-Sequence-Subject` replaces the checked subject and calls the same `store.LoadLastMsg`, at `stream.go` lines 6453 to 6479. An expected `0` with no match passes.
- **Wrong last sequence.** A failed expectation answers with API error code 400 and `err_code` 10071. The API error has only `code`, `err_code`, and `description`, and the latest sequence appears only in the description text.
- **Atomic batches.** A stream with `allow_atomic` accepts `Nats-Batch-Id`, `Nats-Batch-Sequence`, and `Nats-Batch-Commit`. The default batch limit is 1,000 messages. A per-subject expectation is allowed on a subject not already written in the batch. The only refused expectation header is `Nats-Expected-Last-Msg-Id`. `nats-py` supports the `allow_atomic` stream setting but has no batch publish call.
- **Consumer creation.** A consumer with several `filter_subjects`, available from server 2.10, is created on `$JS.API.CONSUMER.CREATE.<stream>`, so its permission is scoped by stream.
- **Names.** NATS stream and consumer names cannot contain whitespace, `.`, `*`, `>`, path separators, or non-printable characters. The documentation recommends alphanumeric characters, `-`, and `_`.
- **Acknowledgement payloads.** `nats-py` acknowledges with `+ACK`, `-NAK`, and `+TERM` on the message's reply subject.
- **Push binding.** `nats-py`'s `subscribe_bind` binds a callback to an existing consumer's deliver subject and subscribes with the consumer's `deliver_group` as its queue. `ConsumerConfig` carries `filter_subjects`, `deliver_subject`, `deliver_group`, `max_ack_pending`, `ack_wait`, and `deliver_policy`.
- **Terminate advisory.** A terminate publishes on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.<stream>.<consumer>` for operators.

## Constructs

Every declaration below is one whitelisted form. Actions sit beside the concept that authorizes them.

### `ontok-bus`

| Declaration | Construct | File |
|---|---|---|
| `StreamKey`, `EventTypeName`, `WorkTypeName`, `LogSequence`, `Ordinal`, `DeliveryToken`, `FailureReason` | semantic scalars | `type.py` |
| `StartPoint`, `Disposition` | `StrEnum` scalars | `type.py` |
| `Causation` | value object: `work_type`, `trigger`, `position` | `value.py` |
| `Absent` | value object: `stream` | `value.py` |
| `Unavailable` | value object: `reason` | `value.py` |
| `Retained[E]` | concept model: `event`, `sequence` | `log.py` |
| `ExpectSequence`, `ExpectNoStream`, `ExpectAny` | value objects; `Expectation` is their union, constructed only in code | `publication.py` |
| `OriginAddress`, `EmissionAddress` | value objects; `Address` is their union | `publication.py` |
| `Origination[E]` | action; derives `address` | `publication.py` |
| `Emission[E]` | value object: `event`, `expectation`; derives `address` | `publication.py` |
| `AppendBatch[A]` | action: `emissions`, `authority`; derives `disposition` from its authority | `publication.py` |
| `Written`, `Contested` | concept models coupling their append; the provider's answer is their union with `Unavailable` | `publication.py` |
| `AppendCheck` | concept model: `answer`; derives its authorized address reads through the ordered union `ContestedAppend \| UncontestedAppend` | `publication.py` |
| `AppendSettlement` | concept model: `check`, `readings`; derives `outcome` | `publication.py` |
| `AlreadyPresent`, `Conflict`, `AppendUnavailable` | concept models; the append outcome is the ordered union `Written \| AlreadyPresent \| Conflict \| AppendUnavailable`; each derives `disposition` | `publication.py` |
| `OfType`, `EveryType` | value objects; the read scope is their union | `read.py` |
| `ReadLatest`, `ReadAddress` | actions | `read.py` |
| the latest-read outcome | union: `Retained[S] \| Absent \| Unavailable` | `read.py` |
| `Readings[S]` | collection; derives `completeness` through the ordered union `AllRead \| SomeUnavailable` | `read.py` |
| `Subscription` | value object: `work_type`, `event_types`, `start` | `subscription.py` |
| `EnsureSubscription`, `DeleteSubscription` | actions | `subscription.py` |
| `SubscriptionEnsured`, `SubscriptionDeleted` | concept models coupling their subscription; each outcome is a union with `Unavailable` | `subscription.py` |
| `Delivery[C]` | concept model: `token`, `event` as `Retained[C]`; derives `streams` | `delivery.py` |
| `Unconstructible` | value object: `token`; derives `streams` | `delivery.py` |
| the arrival | ordered union: `Delivery[C] \| Unconstructible` | `delivery.py` |
| `Dispose` | action: `token`, `disposition` | `delivery.py` |
| `Disposed` | value object; the dispose outcome is its union with `Unavailable` | `delivery.py` |
| UUIDv7 composition from a millisecond timestamp and 74 bits | transformation | `identity.py` |
| `EmittedIdentity` | transformation: `work`, `position`; derives `id` | `identity.py` |
| `ReadClock`, `MintIdentity` | actions | `identity.py` |
| `Minted` | value object: `at`, `id` | `identity.py` |
| `ClockInterpreter` | effect interpreter; its capability is the standard library's `datetime` class | `interpreter.py` |
| `MintInterpreter` | effect interpreter; its capability is `random.SystemRandom` | `interpreter.py` |

### `ontok-nats`

| Declaration | Construct | File |
|---|---|---|
| `NatsSettings` | config, prefix `ONTOK_NATS_`: URL, user, and password as `SecretStr` | `config.py` |
| `StreamSpecification` | value object | `stream.py` |
| the publish acknowledgement, the wrong-last-sequence error, the other API errors, the direct-get reply | foreign models | `model.py` |
| `DeliveryRoute` | route: lifted from the NATS message with `from_attributes=True`; the token from `reply`, the payload through `Json[C]`, the sequence through an `AliasPath` into the message metadata | `route.py` |
| `OriginateInterpreter`, `AppendBatchInterpreter`, `ReadLatestInterpreter`, `ReadAddressInterpreter`, `EnsureSubscriptionInterpreter`, `DeleteSubscriptionInterpreter`, `DisposeInterpreter` | effect interpreters, one per action meaning; each composes its subject at the client call and catches only its documented errors | `interpreter.py` |

### `ontok-ex`

| Declaration | Construct | File |
|---|---|---|
| the reaction schema and the consumed-union schema | foreign models over Pydantic's JSON Schema | `schema.py` |
| `ReactionSpecification`, `JoinSpecification`, `ProjectionSpecification` | value objects: `work_type`, `event_types`; each derives `scopes` | `specification.py` |
| `Inquiry` | transformation: `specification`, `arrival`; derives `reads` | `attempt.py` |
| `Attempt` | concept model: `arrival`, `minted`, `readings` | `attempt.py` |
| `Deferred`, `Rejected` | concept models; each derives `emissions`, `effects`, `batch`, and `disposition` | `response.py` |
| `Reaction(Work)` | concept model: `work_type` | `reaction.py` |
| `Projection(Reaction)` | concept model | `reaction.py` |
| `PerformEffects[R]` | action: `response` | `effects.py` |
| `Performed` | concept model: `action`, `outcomes`; derives `completeness` through the ordered union `EffectsHeld \| EffectsUnavailable`, and `batch` | `effects.py` |

The application declares:
- its events and their stream unions;
- its reaction kinds, their variants, and their narrowed `Action`, `Role`, and `Goal`;
- each kind's response union with its `TypeAdapter`;
- its effect actions, their outcome unions, and their interpreters;
- its projections' reset actions;
- its composition root.

## Order

1. **`ontok-bus`,** with every declaration in its construct table.
2. **`ontok-nats`.**
   - The realization in decisions 57 to 65.
   - The stream specification as a value.
   - The bundled server, license, and manifest moved in, unused.
   - A test fixture that starts `nats:2.14.6-alpine@sha256:ad7a43eb7e3337c3c38ce5d784d1461791f95f730f252d2b25eee699752a0ca3` through testcontainers, with accounts, a scoped program identity, and the `EVENTS` stream.
   - The conformance suite against that server, covering:
     - routing by event type;
     - idempotent appends under each expectation, including a retry after another event has landed in the stream;
     - conflicts under `ExpectNoStream` and `ExpectSequence`;
     - an atomic batch landing whole or not at all;
     - a contested batch settling as already present;
     - the latest read of one type, of every type, and of an exact address, and `Absent`;
     - push ordering across several filter subjects;
     - one delivery per event across two instances in the deliver group;
     - durability across a restart;
     - the three dispositions;
     - a callback bound to the fixed deliver subject surviving consumer deletion and recreation;
     - refusal of stream administration to a program identity.
3. **`ontok-ex`.**
   - Every declaration in its construct table.
   - The data-directory config and its test removed.
   - Tests against the real server, covering:
     - chaining;
     - fan-out;
     - a join, both partial and joined;
     - a join on a lagging subscription producing one joined event;
     - an alternative;
     - effects preceding emissions;
     - redelivery without duplication;
     - a crash before completion;
     - rejection of `Unconstructible`;
     - retry on conflict;
     - retry on an unavailable read;
     - retry on an unavailable effect;
     - replay.
4. **Acceptance.** A test-owned ontology, refining these packages, proves the five functions. Its projection writes to a SQLite file through an effect interpreter whose one capability is the standard library's SQLite connection. Replay identity compares the table before and after. The test ontology imports EX; EX imports none of it.
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
- A delivery running longer than the 30-second acknowledgement wait.
- More than 1,000 emissions from one reaction.
- A join across streams, or over more than two event types.
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
- Do not carry a fact in an action that its effect does not need.
- Do not stage a callback local; nest the terminal expression.
- Do not hash to derive identity.
- Do not read class metadata outside subscription compilation.
- Do not place an empty variant anywhere but last in a union that is not discriminated and is constructed from raw input.
- Do not flatten logs, queues, streams, subjects, and consumers into one string field.
- Do not turn provider configuration into bus semantics.
