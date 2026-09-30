# ONTOK event system plan

## Status

- Branch: `module/ontok-events`, rooted on `main`.
- Distributions and namespaces:

| Distribution | Namespace | Owns | Depends on |
|---|---|---|---|
| `ontok-core` | `ontok.core` | the twelve primitives, which adopt the mandatory configuration and drop their type parameters in this work | — |
| `ontok-bus` | `ontok.bus` | provider-independent event, log, and delivery meaning; the provider contract; the clock and identity minting | `ontok-core` |
| `ontok-nats` | `ontok.nats` | the NATS JetStream realization of every bus action that holds no application type | `ontok-bus`, `nats-py`, `pydantic-settings` |
| `ontok-ex` | `ontok.ex` | executing `Work` over the bus | `ontok-core`, `ontok-bus` |

- `ontok-bus` is a rendered skeleton. `ontok-nats` does not exist yet.
- The workspace requires Python 3.14, because the minting capability is the standard library's `uuid.uuid7`.
- `ontok-ex` holds a data-directory config, its test, and a bundled NATS server from earlier planning. The config and its test are removed. The server, its license, and its manifest move to `ontok-nats` and are not used by this build.
- The design is settled. No discovery phase precedes the build. Every declaration below is routed through the python-development skill's construct selection, with the rule that proves it. Every provider behavior it depends on is confirmed against the NATS Server v2.14.6 source, the NATS documentation, or the `nats-py` source, as recorded below.

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

- Every identified kind a program declares is a refinement of a Core primitive: its events refine `Event`, its reactions refine `Work` through `Policy` or `Projection`, and a reaction kind's action, role, and goal are refinements of `Action`, `Role`, and `Goal`.
- A refinement inherits every parent field, configuration, and derivation unchanged and only adds facts. No refinement redeclares an inherited field.
- Identityless facts and values are python-development constructs, not Core kinds, as Core's own `NodeId`, `Timestamp`, `Instant`, and `Interval` are. The retained event, the delivery, the attempt, a response's deferral and rejection, and every outcome are such facts.
- In the application, Core primitives are not used raw where a narrower meaning exists. A library fact types an event as Core `Event` because no narrower meaning exists at its layer.
- The skill's effect actions describe external effects. They are not Core `Action`s.
- There is no `Event(Event)`. Core `Event` remains the universal occurrence, and Core `Work` remains the persistent undertaking.
- The class is the kind. The only discriminator is an event's `event_type`, which is interchange identity: it travels on the wire and in subjects. A reaction kind's `work_type` is a value in its specification, not a class field. No other `type`, `kind`, `TypeId`, URI, or registry field exists.
- Standard event-sourcing vocabulary is used unless a different meaning requires a different name.
- Core adopts the mandatory configuration and drops its type parameters, and changes in no other way: `Connection(source: Node, target: Node)`, and `Relation(Connection)` adds `id: RelationId`. Refinements only add facts. The Core specification is updated with its realization.

### Construction is the program

- The reaction graph is the class-and-field dependency graph. No separate graph value, registration table, or subject-to-class dispatch exists.
- A genuine alternative is a union. Fan-out is several reactions consuming the same event type. A join is one reaction that consumes two event types in one stream.
- No scheduler, readiness flag, pending state, enabled set, or next-step field duplicates constructibility.
- No mapper, parser pipeline, handler chain, or orchestrator performs work that belongs to construction.
- A construction failure is not a workflow status.

### Layers

- A construct whose field holds an application type is declared in the application. The library packages never name an application type and hold no type parameter.
- A library fact that holds an event types it as Core `Event`. An application event enters it as an existing instance, which is prior construction proof.
- A library fact reads an event's facts by constructing its own values from the event with `from_attributes=True`.
- Raw input constructs an application event only in the application: in its delivery route and in its read interpreters.

### The live edge

- Frozen values hold no client, process, or handle.
- SDK objects are foreign evidence at the boundary and never cross the provider contract.
- A provider binding performs transport calls and serialization only.
- Consumption is a push subscription whose callback is registered once at the composition root. There is no receive loop.
- An arrival is an ordered union of a delivery and `Unconstructible`. No construction failure is caught.
- Transport facts, such as a delivery's token, never enter a reaction. The callback reads the token from its route.
- Every action carries every semantic input its effect needs. A completed immutable value may also be an effect input, so that the outcome coupling the action carries it forward.
- An outcome couples its action when a later construction reads that action. An outcome that authorizes a further effect derives that effect's action.
- An action that follows an outcome union is derived through a failure-exhaustive ordered union: the strong variant requires the authorizing outcome, and the fallback authorizes nothing.
- Each delivery reads what it needs from the log through interpreters nested in its terminal expression. The log is the state. There is no mutable consistency model and no current-state holder.
- The clock and randomness are effects, read through interpreters.
- Programming defects are not caught. A defect crashes the process, and redelivery makes it visible.

### Pydantic substrate

- Every semantic value is a strict, frozen Pydantic construction with the skill's mandatory configuration for its category.
- Past the route, no `dict`, untyped header map, metadata bag, or `bytes` payload carries meaning.
- Serialization occurs exactly once, at the provider binding, as the JSON of the event.
- In a union that is not discriminated and is constructed from raw input, every variant except the last carries a fact no other variant carries. Only the final variant may be empty, because an empty model has no refusal.
- No program code reads class metadata.

## Decisions

### Events

1. **The published thing is the event itself.** The log is the only durable store of events. Large originals live outside the log, and the event carries their digest.
2. **Event type.**
   - The application declares its event-type vocabulary as a `StrEnum` whose values are `"<namespace>-<Class>"`. The namespace is the top-level package that declares the kind.
   - Every publishable kind is a refinement of Core `Event` carrying `event_type: Literal[<member>]`.
   - The hyphen follows NATS naming guidance, so the name is valid as both a subject token and a consumer name, and it never occurs in a Python identifier.
   - An event type is interchange identity: renaming the class does not change it.
3. **Versioning.** An event type's shape never changes. A new shape is a new event type. Readers keep constructing every event type that exists in the log.
   - The log holds the events of every program in the account. A consumer constructs only the kinds it declares; a delivered body that is not one of them is `Unconstructible`.
4. **Stream.** Every publishable kind derives `stream`, a `StreamKey` naming what the event is about. A stream key is a canonical lowercase UUIDv7 or a lowercase hex digest. An event that is its own stream uses its own id.
5. **Two acts of publication.**
   - An **originating** event is created by a source. It carries no causation.
   - An **emitted** event is derived by a reaction. It carries its causation: `Causation(work_type, trigger, position)` for a policy, naming the reaction kind, the id of the event that caused it, and its position among the emissions; `JoinCausation(work_type, first, second, position)` for a join, naming the ids of both events it joined, in the join's declared type order. Causation is a relation to the events that caused the emission, so a join names both.
6. **Publication identity.** An originating event's publication identity is its id. An emitted event's publication identity is its causation.
7. **Node ids.**
   - Minting reads randomness, so it is an effect. The minting interpreters' capability is the standard library's `uuid.uuid7`, which composes a UUIDv7 from the current millisecond and random bits. Its reply lifts through `Uuid`, the source-owned scalar over the standard library's `UUID`, and is serialized at the interpreter into `NodeId`.
   - `MintIdentity` carries nothing and returns `Minted(id)`: a source's or a projection's id.
   - `MintEmissionIdentities` carries nothing and returns `EmissionMinted(id, emitted)`: a policy's id, and `EmittedIdentities`, exactly 1,000 independently minted UUIDv7s, one for each position from 0 to 999.
   - An emitted event's id is `emitted` at its position. The key is proven because the collection's length is exactly the ordinal's range; a per-kind count would leave the selection unproven, and deriving the ids from the reaction's id is outside the transformation algebra.
   - A retry mints a different id. Its emissions carry new ids but share the same causation, so they share a publication identity with the first attempt.
8. **Occurrence.** A delivery reads the clock once. Its reaction, and every event it emits, occurs at that instant.

### Addresses

9. **An address locates one publication in the log.**
   - An originating event's address is `OriginAddress(stream, event_type, id)`.
   - An emitted event's address is `EmissionAddress(stream, event_type, causation)`, where `causation` is `Causation | JoinCausation`.
   - `Address` is the ordered union `EmissionAddress | OriginAddress`, constructed from an event instance with `from_attributes=True` through `AddressConstructor`. The only refusal of `EmissionAddress` over a constructed event is an event with no `causation`, which decision 5 makes an originating event.
   - An address holds at most one event.
10. Accounts isolate organizations, so addresses carry no organization prefix.

### Appends

11. **Expectations:**

| Expectation | Holds when |
|---|---|
| `ExpectAny` | nothing is at the event's own address |
| `ExpectSequence(sequence)` | the latest event in the stream has that sequence |

12. **Two append actions.**
    - `Origination(event, expectation)` appends one originating event and derives its `address`.
    - `AppendBatch(expectation, events, authorized)` appends a reaction's emitted events atomically: every event lands or none does.
      - The expectation applies to the first event. Every later event expects `ExpectAny`.
      - `events` holds from 0 to 1,000 events, the provider's atomic batch limit.
      - `authorized` is the disposition the authorizing response derived. The action carries it forward exactly as the skill's `PersistPosition` carries the position: the response is constructed once, flows into this action, and the settlement that couples the action carries its authority to the conclusion.
13. **The settling read.** Each append action derives `reads`, the address reads that settle a contest over it.
    - `Origination` derives one `ReadAddress` of its event's address.
    - `AppendBatch` derives `lead` through the ordered union `Lead | NoLead`, constructed from the batch with `from_attributes=True`. `Lead` reads the first event through `AliasPath("events", 0)` and derives one `ReadAddress` of its address. The events are constructed instances, so its only refusal is an empty tuple, which is what `NoLead`, deriving no reads, means. `AppendBatch.reads` is its lead's reads.
    - Because a batch is atomic, one address answers for the whole batch.
14. **The provider's answer** couples its append action and is one of three:
    - `Written(append)`: every event landed;
    - `Contested(append)`: an expectation failed;
    - `Unavailable(reason)`: the provider did not complete the append.

    An empty batch makes no provider call and is `Written`: an atomic commit needs a message.
15. **Settling a contest.** `AppendAnswer(answer)` derives its authorized address reads through the ordered union `ContestedAppend | UncontestedAppend`.
    - `ContestedAppend` requires a `Contested` answer and authorizes its append's `reads`. The answer is a constructed instance, so its only refusal is an answer that is not `Contested`, which is what `UncontestedAppend`, authorizing nothing, means.
    - The settle interpreter's action is the `AppendAnswer`: settling an answer is one action meaning. It executes each of the answer's `reads` through the provider's direct get and returns `AppendSettlement(answer, readings)`, coupling its action, so the callback never holds the answer to pass it twice. It constructs application events, so the application declares it.
    - `AppendSettlement` derives `outcome` through this ordered union, constructed from the settlement with `from_attributes=True`; each strong variant holds its proof through an `AliasPath`:

| Outcome | Holds | Constructs when | Meaning |
|---|---|---|---|
| `Appended(written)` | the `Written` answer | the answer was `Written` | the events were appended |
| `AlreadyPresent(contested, existing)` | the `Contested` answer and the `Retained` address read | the answer was `Contested` and the address holds an event | this publication is already on the log; this is success |
| `Conflict(contested, absent)` | the `Contested` answer and the `Absent` address read | the answer was `Contested` and the address is empty | another event holds the position the expectation required |
| `AppendUnavailable` | nothing | anything else | the answer or the address read was unavailable |

    - A retry never appends a second copy, even when other events have landed in the stream since the first attempt.
16. There is no deduplication window. Idempotence holds for the life of the log.
17. **Events do not embed their prior.** Succession is enforced by `ExpectSequence`.
    - A stream's state is the fold of its history: the state-transition chain in which each event succeeds the state before it. No event stores it, and the chain is in memory, never a wire shape.
    - A policy reads its trigger's stream history through `ReadStream` and folds it. The folded state already contains the trigger, and the policy derives its emissions from that state. The emitted events become the next steps of the same chain when they are folded in turn, so there is one transition, not a fold and a separate successor.

### Reads

18. **The latest read.** `ReadLatest(stream, scope)` names a stream and a scope. The scope is `OfType(event_type)`, which reads the latest event of one type in the stream, or `EveryType`, which reads the latest event in the stream. `ReadAddress(address)` names one address. `ReadStream(stream)` names a stream's whole history.
    - The outcome is `Retained(event, sequence)`, the event and its log sequence.
    - When nothing matches, the outcome is `Absent(stream)`.
    - On provider failure, the outcome is `Unavailable(reason)`.
    - A history read's outcome is `History`, the collection of the stream's events as `Retained` in log order with at least one member, or `Absent(stream)`, or `Unavailable(reason)`. `History` derives `latest`, its last member, a selection by a proven key.
19. **Reads see the log as it is now.** The provider has no latest read as of an earlier sequence.
20. **Readings.** Each read executes through its own interpreter, one per action meaning. `Readings` is the collection of their outcomes in the order of the reads, constructed at the composition root from each interpreter's outcome. Readings derive their `completeness` through the ordered union `AllRead | SomeUnavailable`. `AllRead` requires every outcome to be `Retained`, `History`, or `Absent`. The outcomes are constructed instances, so its only refusal is an `Unavailable` outcome, which is what `SomeUnavailable` means.

### Subscriptions

21. **A subscription is a reaction kind's standing interest** in every event type it consumes, together with its progress.
    - It is the value `Subscription(work_type, event_types)`, with at least one event type.
    - Each reaction kind has exactly one.
    - It exists independently of any process.
    - Its name and its deliver group are the reaction kind's `work_type`, so each delivery reaches exactly one running instance.
    - Its deliver subject is `_INBOX.ontok.<work_type>`, fixed so that a callback stays bound across deletion and recreation.
    - `EnsureSubscription(subscription)` creates it, and creating it again with the same configuration is idempotent. `DeleteSubscription(subscription)` removes it.
22. **Start:** every subscription delivers from the beginning of the log.
23. **Order:** one event at a time, in log order across all of the reaction kind's consumed types.
24. **Storage is infrastructure,** declared by the deployment and not created by the program. `ontok-nats` states the required stream specification, and its conformance suite verifies a deployment against it.
25. **The specification** of a reaction kind is declared once, at the composition root, and is the single home of the kind's `work_type`, its consumed event types, and its `Action`.
    - A `PolicySpecification(work_type, event_types, action)` is for a policy.
    - A `JoinSpecification(work_type, first, second, action)` is for a join. It derives `event_types` from its two types.
    - A `ProjectionSpecification(work_type, event_types, action)` is for a projection.
    - `event_types` holds at least one type.
    - Each derives `subscription`.
    - The action is the kind's single `Action` refinement instance, with its `Role` and `Goal` refinement instances, each with a fixed UUIDv7 id.

### Delivery

26. **A delivery is the provider handing one event to one subscription,** possibly more than once.
    - The application's delivery route is one model, `DeliveryRoute`, constructed from the provider's message with `from_attributes=True`:
      - `token` through the alias `reply`;
      - `sequence` through an `AliasPath` into the message metadata;
      - `event` through the alias `data`, as the ordered union `Json[<its event union>] | MessageBody`.
    - `MessageBody` is the source-owned scalar over the message's bytes, declared in `ontok-nats`. Every refusal of the program's event union, whether an undeclared type, a malformed event, or a body that is not JSON, means the body is not one of this program's events, which is what `MessageBody` means. The arrival refuses it, and nothing retains it.
    - The bus arrival is the ordered union `Delivery | Unconstructible`, constructed from the route with `from_attributes=True` through `ArrivalConstructor`.
      - `Delivery(token, event, sequence)` holds the event as Core `Event`, and derives `address` and `streams`.
      - `Unconstructible(token)` derives no streams.
      - `Delivery.event` refuses only a `MessageBody`, which is what `Unconstructible` means.
27. **Dispositions, exactly three:**

| Disposition | Meaning | Derived by |
|---|---|---|
| Complete | every consequence of the event is durable | a batch authorizing Complete that was `Appended` or `AlreadyPresent` |
| Retry | deliver again | a batch authorizing Retry, or a `Conflict` or `AppendUnavailable` |
| Reject | the delivery is terminal | a batch authorizing Reject that was `Appended` |

28. **The provider keeps its own record of rejections** for operators. The bus reads no rejection record.
29. **Failures.** Every transport interpreter translates its documented nonfatal failures into an unavailable variant: `Unavailable(reason)`, or one coupling its action where a later construction reads that action. Every transport outcome is a union that includes one. The clock and minting have no documented failures, so their outcomes are plain. The application's effect outcomes are each a union of its own success variants and `Unavailable`. Anything else is a defect.
30. **The acknowledgement wait bounds the whole delivery.** A delivery that runs longer is redelivered while it runs, and idempotence absorbs the repetition.

### The delivery's facts

31. **The inquiry** derives the delivery's `reads` from its specification and arrival. Each kind's callback constructs its own inquiry:
    - `PolicyInquiry(specification, arrival)` derives one `ReadStream` for each of the arrival's streams;
    - `JoinInquiry(specification, arrival)` derives, for each of the arrival's streams, a `ReadLatest` of `OfType(first)`, then of `OfType(second)`;
    - `ProjectionInquiry(specification, arrival)` derives no reads.

    An `Unconstructible` arrival has no streams, so it authorizes no reads. Each inquiry's reads share one action meaning, so the callback executes each through that meaning's interpreter and constructs `Readings` from the outcomes.
32. **`Attempt(inquiry, at, minted, readings)`** is one delivery attempt: the inquiry, the delivery's instant and minted ids, and the readings of its inquiry. It derives `id` from its minted identity, and `action` and `work_type` from its inquiry's specification, so that a reaction constructs its inherited fields from the attempt by name.
33. **The response** is constructed from the attempt through the `TypeAdapter` the application declares beside the reaction kind's response union. That union is a plain union:
    - the reaction kind's own variants, each requiring a `Delivery` arrival, its trigger's event types, and `AllRead` readings;
    - `Deferred`, requiring `SomeUnavailable` readings;
    - `Rejected`, requiring an `Unconstructible` arrival.

    Exactly one variant constructs. A reaction that refuses for any other reason constructs nothing, and the process crashes as a defect.
34. **Every response variant derives** its `batch` and its `disposition`:
    - a reaction variant that emits derives its `batch` from its `expectation`, its `events`, and its `disposition` as `authorized`;
    - a reaction variant that emits nothing, a projection, `Deferred`, and `Rejected` derive a `batch` with no events and their `disposition` as `authorized`;
    - a reaction variant and a projection derive Complete, `Deferred` derives Retry, and `Rejected` derives Reject.
35. **Performing effects.** For a kind with effects, the application declares `PerformEffects(response)`, which carries the response as its idempotency key and requests the effects it derives.
    - The application's effect interpreter executes them through its one capability and returns `Performed(action, outcomes)`.
    - `Performed` derives its `completeness` through the ordered union `EffectsHeld | EffectsUnavailable`. `EffectsHeld` requires every outcome to be a success variant. The outcomes are constructed instances, so its only refusal is an `Unavailable` outcome, which is what `EffectsUnavailable` means.
    - `EffectsHeld` derives the response's `batch` and disposition. `EffectsUnavailable` derives a `batch` with no events, authorizing Retry, and Retry.
36. **Effects precede emissions.** An emission announces a consequence, so the effect outcome authorizes it.
37. **The final disposition.** `Conclusion(settlement)` holds the batch's settlement and derives `disposition` through the ordered union `DurableAppended | DurablePresent | NotDurable`, constructed from the conclusion with `from_attributes=True`.
    - `DurableAppended` holds the batch through `AliasPath("settlement", "outcome", "written", "append")`, and `DurablePresent` through `AliasPath("settlement", "outcome", "contested", "append")`. Each derives its batch's `authorized`.
    - `NotDurable` derives Retry. The settlement is a constructed instance, so the strong variants refuse only a `Conflict` or `AppendUnavailable` outcome, both of which mean Retry.
    - The batch is typed `AppendBatch`, and only a delivery constructs a conclusion.
38. **The terminal fact is `Disposed`.** The callback constructs `Dispose(token, disposition)` from the route's token and the final disposition. The dispose interpreter publishes it.
39. **The terminal expression** nests, by data dependency:
    - the clock interpreter, and the emission-minting interpreter for a policy or the minting interpreter for a projection;
    - the read interpreter over each of the inquiry's reads, and the readings;
    - the attempt and its response;
    - for a kind with effects, the effect interpreter;
    - the append interpreter and the settle interpreter;
    - the conclusion;
    - the dispose interpreter.

    Each kind's callback nests only the interpreters its declarations need. Pure facts, such as the arrival and the inquiry, are constructed from the route at each use. Every effect outcome couples its action, so each interpreter executes once and later facts read its action through the outcome. A crash at any point is followed by redelivery, and the causation addresses and the settling of contests make it converge.

### Reactions

40. **A reaction kind is a refinement of `Policy(Reaction)` or `Projection(Reaction)`.**
    - `Reaction(Work)` adds `work_type` and `at`, and inherits `id` and `action` unchanged.
    - `Policy(Reaction)` adds `emitted`. A policy derives events from events, and a join is a policy.
    - Its inherited fields, `id` and `action`, and its added fields, `work_type` and `at`, construct by name from the attempt's same-named fields and derivations. An inherited field carries no alias.
    - Its own fields construct through `AliasPath`s:
      - a policy's `emitted`, from the minted identities;
      - its trigger, as the delivered event, typed as the event kinds the variant reacts to;
      - the readings it declares, by position.
41. **Derivations,** each a transformation on the reaction:
    - `stream`, its trigger's stream;
    - `expectation` and `events`, for a variant that emits;
    - the application's effect actions, for a kind with effects.
42. **Emission expectations.**
    - A policy's batch's first event is its emission into its trigger's stream and expects the sequence of its history's `latest`.
    - A batch whose first event goes to another stream, and every join batch, expects `ExpectAny`.
43. **Joins.**
    - A join consumes two event types in one stream and reads the latest event of each.
    - Its variants take those readings by position.
    - `Joined` requires both retained. Each `Partial` variant requires one absent, and emits nothing.
    - Because reads see the log as it is now, a lagging subscription can construct `Joined` at both arrivals. `Joined` emits with `JoinCausation` naming both events in declared type order, so both arrivals produce the same publication identity and the log keeps one.
    - A join across streams, or over more than two event types, is out of scope.
44. **Causation.** An emitted event references its trigger and the reaction kind that derived it. Reactions are never published. Causation is a relation between events and is never inferred from temporal order.
45. **Effects.**
    - A reaction kind's effects run through exactly one capability. Effects on two systems are two reaction kinds consuming the same event.
    - Effects are idempotent by event id or log sequence.
    - A read model's writes apply only when the incoming sequence is newer than the one stored, and each write sets its key to the value at that sequence.
46. **`Projection(Reaction)`** is a reaction kind that maintains a read model. It performs effects and emits nothing. Its application declares the reset action that clears the read model.

### Replay

47. **Replay is three effects, each authorized by the previous outcome,** declared by the application:
    - `DeleteSubscription(subscription)` returns `SubscriptionDeleted(subscription)`;
    - the application's fact holding that outcome authorizes the projection's reset;
    - the reset's outcome authorizes `EnsureSubscription` of the same subscription, which returns `SubscriptionEnsured`.

    Each step derives its successor through a failure-exhaustive ordered union, so an unavailable step authorizes nothing further.
48. **The in-flight race is harmless.** A delivery still running during replay can write after the reset. Its write sets its key to the value at its sequence, which is the value replay itself produces there. Acknowledgements sent to a deleted consumer are dropped.
49. **Replay is evaluated at the composition root** as one expression, on the application's operator instruction. How that instruction arrives belongs to the application. The acceptance test evaluates it directly.

### Composition root

50. **The composition root binds, once:**
    - configuration and the provider client;
    - the clock, minting, and provider interpreters, and the application's read and effect interpreters;
    - for each reaction kind, its specification, its subscription through the `EnsureSubscription` interpreter, and its callback, registered with the client's push binding on the fixed deliver subject with manual acknowledgement.

    The callback's input is the delivery route. Its body is the delivery's terminal expression.

    The callback is registered once at the composition root. The deliver subject is fixed, so registration holds whether or not the consumer exists.

    The startup expression evaluates each kind's `EnsureSubscription` and constructs its terminal fact, `StartupSubscriptions`, the collection of each kind's ensure outcome in specification order. The ensure outcome is `SubscriptionEnsured(subscription)` or `EnsureUnavailable(subscription, reason)`, coupling the subscription because the startup fact reads it. That fact is the value of the startup expression, which is what the process's entry evaluates to. An unavailable ensure authorizes nothing further, and that kind receives no deliveries; what the deployment does with the fact is its liveness, which is out of scope.
51. **A source publishes through one terminal expression** at its composition root, nesting by data dependency:
    - the clock interpreter and the minting interpreter;
    - the source's event, and `Origination(event, expectation)`, with `ExpectAny` or with `ExpectSequence` from a `ReadLatest` nested ahead of it;
    - the originate interpreter and its `AppendAnswer`;
    - the settle interpreter, whose `AppendSettlement` outcome is the publication's result.
52. **Rules and contexts** are domain facts a reaction reads through its fields. They are never scheduler state. Evaluating them is not an execution concern of this work.

### Idempotence and ownership

53. Idempotence has one home per layer:
    - the bus owns idempotent appends and the settling of contests;
    - `ontok-ex` owns causation for every emitted event;
    - the domain owns pure construction.

### Provider contract

54. **The bus defines each operation as an action with a constructed outcome:**
    - `Origination` and `AppendBatch`;
    - `ReadLatest`, `ReadAddress`, and `ReadStream`;
    - `EnsureSubscription` and `DeleteSubscription`;
    - `Dispose`;
    - `ReadClock`, `MintIdentity`, and `MintEmissionIdentities`.

    A provider implements the append, subscription, and dispose actions as effect interpreters. The read interpreters construct application events, so the application declares them over the provider's foreign models. The bus implements the clock and minting itself.
55. Contracts accept and return constructed events, never SDK objects. There is no generic publish or subscribe surface.
56. **A bus provider offers:**
    - conditional append on an exact address and on a whole stream;
    - atomic batch append;
    - the latest read of one type or of every type in a stream, of one exact address, and the whole history of a stream in log order;
    - durable ordered push subscriptions on a fixed deliver address with a deliver group and explicit disposition.

    A provider without them is not a bus provider. The bus does not simulate what a provider lacks.
57. Provider configuration and policy stay in the provider package. Provider framing is serialized at the crossing that owns it: a provider interpreter's client call, and the application's route and read interpreters, which nest the provider's foreign models.

### NATS realization

58. **Subjects.**
    - An originating event's subject is `event.<stream>.<event_type>.<id>`.
    - A policy's emitted event's subject is `event.<stream>.<event_type>.<work_type>.<trigger>.<position>`.
    - A join's emitted event's subject is `event.<stream>.<event_type>.<work_type>.<first>.<second>.<position>`. Each causation derives its subject tokens, and the interpreter composes the subject from them.
59. **Stream specification:**
    - the stream `EVENTS` per account, holding `event.>`;
    - file storage;
    - limits retention with no limits;
    - `deny_delete` and `deny_purge`;
    - `allow_direct`;
    - `allow_atomic`.
60. **Conditional publish headers:**
    - `ExpectAny` sends `Nats-Expected-Last-Subject-Sequence: 0` on the event's exact subject;
    - `ExpectSequence` adds `Nats-Expected-Last-Subject-Sequence-Subject: event.<stream>.>`, with the sequence.
61. **Atomic batches.** Each event is published with `Nats-Batch-Id`, `Nats-Batch-Sequence` from 1, and, on the last, `Nats-Batch-Commit: 1`. The commit is a request, and its reply is the acknowledgement for the whole batch. `nats-py` has no batch call, so the interpreter sets these headers itself.
62. **Answers.** A publish acknowledgement is `Written`. API error `10071`, wrong last sequence, is `Contested`. Every other documented failure is `Unavailable`.
63. **Reads** are requests to `$JS.API.DIRECT.GET.EVENTS` in the body form, `{"last_by_subj": "<subject>"}`:
    - `OfType` reads `event.<stream>.<event_type>.>`;
    - `EveryType` reads `event.<stream>.>`;
    - `ReadAddress` reads the address's exact subject.
    - `ReadStream` pages through a batched direct get, `{"seq": <next>, "next_by_subj": "event.<stream>.>", "batch": <n>}`, from sequence 1. A batched get answers with one reply per message and then `204 EOB` on the request's reply subject, and the client's `request` returns one reply, so the interpreter subscribes an inbox, publishes each page's request with that inbox as its reply, and constructs from the replies it receives until the `EOB`. The first page requests one message. Each later page requests the `Nats-Num-Pending` of the previous `EOB` and starts after its `Nats-Last-Sequence`, and the history ends at an `EOB` with no pending messages.
    - A reply's header text constructs `LogSequence` through `model_validate_json`.

    A 404 status is `Absent`.
64. **Consumer settings:**
    - a durable push consumer named with the reaction kind's `work_type`;
    - `filter_subjects` of `event.*.<event_type>.>` for each consumed event type;
    - the deliver subject `_INBOX.ontok.<work_type>`;
    - the deliver group `<work_type>`;
    - explicit acknowledgement;
    - `max_ack_pending` of 1;
    - an acknowledgement wait of 30 seconds;
    - unlimited deliveries;
    - deliver-all;
    - no flow control.

    `EnsureSubscription` creates it through the JetStream consumer API. The composition root binds the callback with the client's `subscribe_bind` and manual acknowledgement, which subscribes with the deliver group as its queue.
65. **Dispositions** are publishes to the delivery token:
    - Complete publishes `+ACK`;
    - Retry publishes `-NAK`;
    - Reject publishes `+TERM`.
66. **A program identity has exactly these permissions,** and no stream administration:
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
- **Batched history reads.** `JSApiMsgGetRequest` carries `batch` with `next_by_subj`, which may be a wildcard (`jetstream_api.go` lines 673 to 695). Each batched reply carries `Nats-Num-Pending` and `Nats-Last-Sequence`, and a batch ends with `204 EOB`, which also carries `Nats-Num-Pending` (`stream.go` lines 5916 to 5918). A batch stops early at `max_bytes`, which defaults to the server's maximum pending size.
- **One reply per request.** `nats-py`'s `request` returns the first reply to its inbox, as its documentation states, so a multi-reply batched get is read through a subscription on an inbox that the request names as its reply.
- **Terminate advisory.** A terminate publishes on `$JS.EVENT.ADVISORY.CONSUMER.MSG_TERMINATED.<stream>.<consumer>` for operators.

## Constructs

Every declaration is one of the skill's thirteen forms, selected by the construct-selection table. The rule column names what admits it.

### `ontok-core`

| Declaration | Construct | Rule |
|---|---|---|
| every `BaseModel` primitive and finished value | owned `BaseModel` with `frozen=True`, `extra="forbid"`, `strict=True`, `validate_default=True`, `revalidate_instances="never"` | pydantic.md mandatory configuration |
| every `RootModel` scalar and collection | semantic `RootModel` with `frozen=True`, `strict=True`, `validate_default=True`, `revalidate_instances="never"` | pydantic.md mandatory configuration |
| `Connection(source, target)`, `Relation(Connection)` | concept models whose endpoints are `Node`, with no type parameter | construction.md: every field is a whitelisted construct; concept-model.md: a refinement inherits every field unchanged |

### `ontok-bus`

| Declaration | Construct | Rule | File |
|---|---|---|---|
| `StreamKey`, `EventTypeName`, `WorkTypeName`, `LogSequence`, `Ordinal` (0 to 999), `DeliveryToken`, `FailureReason` | semantic scalars | one atomic meaning over a primitive | `type.py` |
| `Disposition` | `StrEnum` scalar | a uniform closed vocabulary | `type.py` |
| `Causation(work_type, trigger, position)`, `JoinCausation(work_type, first, second, position)` | value objects holding the causing events' `NodeId`s; each derives its subject `tokens`; their union is an emitted event's causation | value object references an identified concept by its identity scalar; a join is caused by two events | `value.py` |
| `OriginAddress`, `EmissionAddress`, and `Address` with `AddressConstructor` | value objects and an ordered union | decision 9 proves the sole refusal | `value.py` |
| `ExpectAny`, `ExpectSequence`, and `Expectation` | value objects and a union built in code | alternatives with different facts | `value.py` |
| `OfType`, `EveryType`, and the read scope | value objects and a union built in code | alternatives with different facts | `value.py` |
| `Absent(stream)`, `Unavailable(reason)`, `Disposed` | value objects | exhausted by field equality | `value.py` |
| `Unconstructible(token)` | value object; derives no streams | exhausted by field equality | `value.py` |
| `Minted(id)`, `EmissionMinted(id, emitted)` | value objects | exhausted by field equality | `value.py` |
| `EmittedIdentities` | collection of exactly 1,000 `NodeId`s | position selects an id | `value.py` |
| `Retained(event, sequence)` | concept model; `event` is Core `Event` | a durable fact | `log.py` |
| `Origination(event, expectation)` | action; derives `address` and `reads` | one intended external effect | `publication.py` |
| `AppendBatch(expectation, events, authorized)` | action; `events` from 0 to 1,000; derives `lead` and `reads` | one intended external effect; a completed value may be an effect input | `publication.py` |
| `Lead`, `NoLead` | ordered union built from the batch; each derives `reads` | decision 13 proves the sole refusal | `publication.py` |
| `Written(append)`, `Contested(append)` | concept models; the answer is `Written \| Contested \| Unavailable`; `Contested` derives its append's `reads` | outcomes coupling the action a later construction reads | `publication.py` |
| `AppendAnswer(answer)`, `ContestedAppend`, `UncontestedAppend` | concept model and ordered union; derives `reads` | decision 15 proves the sole refusal | `publication.py` |
| `AppendSettlement(answer, readings)` | concept model returned by the settle interpreter; derives `outcome` | an outcome coupling its action | `publication.py` |
| `Appended(written)`, `AlreadyPresent(contested, existing)`, `Conflict(contested, absent)`, `AppendUnavailable` | concept models holding their proofs through `AliasPath`; the outcome is the ordered union in decision 15 | each attempt's refusals mean the next | `publication.py` |
| `ReadLatest(stream, scope)`, `ReadAddress(address)`, `ReadStream(stream)` | actions | one intended external effect | `read.py` |
| the read outcome `Retained \| Absent \| Unavailable`, and the history outcome `History \| Absent \| Unavailable` | unions | alternatives with different facts | `read.py` |
| `History` | collection of `Retained`, at least one, in log order; derives `latest` | order carries meaning; a fold's input | `read.py` |
| `Readings` with `AllRead \| SomeUnavailable` | collection and ordered union | the declared order of the reads carries meaning; decision 20 proves the sole refusal | `read.py` |
| `Subscription(work_type, event_types)` | value object; `event_types` has at least one member | exhausted by field equality; invalid combinations have no representation | `subscription.py` |
| `EnsureSubscription`, `DeleteSubscription` | actions | one intended external effect | `subscription.py` |
| `SubscriptionEnsured`, `EnsureUnavailable`, `SubscriptionDeleted` | concept models coupling their subscription; the ensure outcome is `SubscriptionEnsured \| EnsureUnavailable`; the delete outcome is `SubscriptionDeleted \| Unavailable` | outcomes a later construction reads | `subscription.py` |
| `StartupSubscriptions` | collection of ensure outcomes in specification order | the startup expression's terminal fact | `subscription.py` |
| `Delivery(token, event, sequence)` | concept model; `event` is Core `Event`; derives `address` and `streams` | a durable fact | `delivery.py` |
| `Conclusion(settlement)` with `DurableAppended \| DurablePresent \| NotDurable` | concept model and ordered union; derives `disposition` | decision 37 proves each refusal | `delivery.py` |
| the arrival `Delivery \| Unconstructible` with `ArrivalConstructor` | ordered union | decision 26 proves the sole refusal | `delivery.py` |
| `Dispose(token, disposition)` | action; the outcome is `Disposed \| Unavailable` | one intended external effect | `delivery.py` |
| `ReadClock`, `MintIdentity`, `MintEmissionIdentities` | actions carrying nothing | one intended external effect | `identity.py` |
| `Uuid` | source-owned scalar over the standard library's `UUID`, serialized at the interpreter | a source-owned scalar meaning | `identity.py` |
| `ClockInterpreter` | effect interpreter; its capability is the standard library's `datetime` class | one action, one imported capability | `interpreter.py` |
| `MintInterpreter`, `MintEmissionIdentitiesInterpreter` | effect interpreters; each one's capability is the standard library's `uuid.uuid7` | one interpreter per action meaning, one imported capability | `interpreter.py` |

### `ontok-nats`

| Declaration | Construct | Rule | File |
|---|---|---|---|
| `NatsSettings` | config, prefix `ONTOK_NATS_`: `url` as the semantic scalar `NatsUrl`, and `user` and `password` as `SecretStr`; the package declares `pydantic-settings>=2,<3` | deployment input; non-secret fields are semantic scalars | `config.py` |
| `StreamSpecification` | value object | exhausted by field equality | `stream.py` |
| the publish acknowledgement, the batch acknowledgement, the wrong-last-sequence error, the other API errors, the JetStream message metadata, the direct-get reply and its `EOB` | foreign models; header text lifts as source-owned text and constructs `LogSequence` through `model_validate_json` | another system's differing representation | `model.py` |
| `MessageBody` | source-owned scalar over the message's bytes | a source-owned scalar meaning; the arrival refuses it | `model.py` |
| `OriginateInterpreter`, `AppendBatchInterpreter`, `EnsureSubscriptionInterpreter`, `DeleteSubscriptionInterpreter`, `DisposeInterpreter` | effect interpreters, one per action meaning; each composes its subject at the client call and catches only its documented errors | one action, one imported capability | `interpreter.py` |

### `ontok-ex`

| Declaration | Construct | Rule | File |
|---|---|---|---|
| `PolicySpecification`, `JoinSpecification`, `ProjectionSpecification` | concept models holding the kind's `Action`; each derives `event_types` and `subscription` | a durable fact holding a concept | `specification.py` |
| `PolicyInquiry`, `JoinInquiry`, `ProjectionInquiry` | transformations; each derives `reads` | constructed inputs determine one output | `attempt.py` |
| `Attempt(inquiry, at, minted, readings)` | concept model; derives `id`, `action`, and `work_type` | a durable fact whose derivations name the reaction's inherited fields | `attempt.py` |
| `Deferred`, `Rejected` | concept models; each derives `batch` and `disposition` | variants with different facts | `response.py` |
| `Reaction(Work)` | concept model adding `work_type` and `at` | a refinement that only adds facts | `reaction.py` |
| `Policy(Reaction)` | concept model adding `emitted` | every policy is a reaction; only policies emit | `reaction.py` |
| `Projection(Reaction)` | concept model | every projection is a reaction; it emits nothing | `reaction.py` |

### The application

Each application declares, because each holds its own types:
- its event-type `StrEnum`, its events, its event union, and that union's `TypeAdapter`;
- its delivery route, `DeliveryRoute`, nesting the provider's metadata foreign model and `MessageBody`;
- its `ReadLatestInterpreter`, `ReadStreamInterpreter`, and `SettleAppendInterpreter`, over direct-get reply foreign models that hold its event union;
- its reaction kinds, their variants, and their `Action`, `Role`, and `Goal` refinements;
- each kind's response union with its `TypeAdapter`;
- its effect actions, their outcome unions, and their interpreters;
- for a kind with effects, `PerformEffects`, `Performed`, `EffectsHeld`, and `EffectsUnavailable`;
- its projections' reset actions and its replay facts;
- its composition root.

## Order

1. **`ontok-core`.** The mandatory configuration on every primitive and finished value, the type parameters removed from `Connection` and `Relation`, and `spec/ontok-core.xml` updated with them.
2. **`ontok-bus`,** with every declaration in its construct table.
3. **`ontok-nats`.**
   - The realization in decisions 58 to 66.
   - The stream specification as a value.
   - The bundled server, license, and manifest moved in, unused.
   - A test fixture that starts `nats:2.14.6-alpine@sha256:ad7a43eb7e3337c3c38ce5d784d1461791f95f730f252d2b25eee699752a0ca3` through testcontainers, with accounts, a scoped program identity, and the `EVENTS` stream.
   - A test ontology declaring the application's route and read interpreters.
   - The conformance suite against that server, covering:
     - routing by event type;
     - idempotent appends under each expectation, including a retry after another event has landed in the stream;
     - a conflict under `ExpectSequence`;
     - an atomic batch landing whole or not at all;
     - a contested batch settling as already present;
     - the latest read of one type, of every type, and of an exact address, and `Absent`;
     - a history read across several pages, and `Absent`;
     - push ordering across several filter subjects;
     - one delivery per event across two instances in the deliver group;
     - durability across a restart;
     - the three dispositions;
     - a callback bound to the fixed deliver subject surviving consumer deletion and recreation;
     - refusal of stream administration to a program identity.
4. **`ontok-ex`.**
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
5. **Acceptance.** A test-owned ontology, refining these packages, proves the five functions. Its projection writes to a SQLite file through an effect interpreter whose one capability is the standard library's SQLite connection. Replay identity compares the table before and after. The test ontology imports EX; EX imports none of it.
6. **Specification.** `spec/ontok-bus.xml` and `spec/ontok-ex.xml` from the built model, `spec/README.md` updated, and this plan updated to what was built.

## Final gates

- The workspace and every package require Python 3.14; ruff targets `py314` and basedpyright `3.14`.
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
- Snapshots. A policy folds its stream's whole history on every delivery.

## Interchange standards

CloudEvents, AsyncAPI, and W3C Trace Context are projections and interoperability assets. They do not define this programming model and are not copied into these packages.

## Open for Core

- **Embedding versus reference.** Core `Work` embeds a whole `Action`, and Core `Connection` embeds its endpoints. Reactions are not published, so the identical embedded action exists only in memory. The question stands on its own merits: whether a primitive embeds a node or references it by identity. It is decided from the evidence this work produces, not within it.

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
- Do not stage a callback local; nest the terminal expression.
- Do not hash to derive identity.
- Do not read class metadata.
- Do not declare a type parameter on any construct.
- Do not redeclare an inherited field.
- Do not name an application type in a library package.
- Do not place an empty variant anywhere but last in a union that is not discriminated and is constructed from raw input.
- Do not flatten logs, queues, streams, subjects, and consumers into one string field.
- Do not turn provider configuration into bus semantics.
