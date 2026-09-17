# ontok-bus plan

## Status

Planning only.

- Future branch: `module/ontok-bus`
- Distribution: `ontok-bus`
- Namespace: `ontok.bus`
- This directory intentionally contains only this plan. Render the package skeleton
  after the work is split onto its branch.

## Telos

`ontok-bus` is the provider-independent event transport domain for ONTOK systems.
It makes the ideas required to publish, deliver, route, acknowledge, and recover
constructed facts explicit without making any event platform the semantic
authority.

ONTOK systems are fundamentally event driven. The bus is therefore a first-class
reusable module rather than an implementation detail embedded in `ontok-ex` or in
each domain package.

`Event` remains one of ONTOK Core's twelve primitives: a durable memorial of an
occurrence. A transport publication, message, delivery, acknowledgement, offset,
or retry is not automatically an `Event`. Discovery must preserve the distinction
between what occurred, the fact being transported, and a provider's account of
transporting it.

## Governing insight

One provider is sufficient evidence from which to discover a generic domain.
Generic does not mean the intersection of several provider schemas and does not
mean a lowest-common-denominator API.

NATS is the first evidence because its real system exposes the ideas clearly. The
work is to identify the things evidenced by NATS, separate those things from NATS's
account of them, and name the provider-independent ideas according to their nature.
Later providers test, refine, or extend that model; they do not justify it by schema
matching.

## Dependency topology

```text
ontok-bus  -> ontok-core
ontok-ex   -> ontok-core + ontok-bus
ontok-nats -> ontok-bus + official NATS client

composition root -> ontok-ex + selected provider package(s)
```

- Core remains bus-free and retains exactly twelve primitives.
- EX depends on the provider-independent bus domain, never NATS or another concrete
  provider.
- Provider packages depend inward on `ontok-bus` and implement its declared
  contracts.
- Provider packages remain separate distributions. `ontok-bus` does not bundle a
  provider matrix or hide providers behind optional extras.
- The composition root selects and binds one or more providers.

## Source of semantic authority

- ONTOK classes and successfully constructed Pydantic values remain authoritative.
- The bus carries constructed facts; it does not redefine their kinds, fields, or
  identities.
- Bus facts express actual transport-domain distinctions discovered from evidence.
- Provider replies and wire objects are source accounts, modeled as foreign shapes
  in the provider package.
- No broker, stream, log, queue, or SDK becomes an ontology registry.

## Discovery gate

No bus construct is approved by this plan. Before writing any type, execute the
repository's `domain-discovery` skill in full and persist its written outputs.

### Evidence

Render whole, unedited evidence from a real NATS server through the official Python
client. Include successful and failed publication, durable consumption, delivery,
acknowledgement, negative acknowledgement, redelivery, timeout, reconnect, and
consumer recovery. Read the official protocol and JetStream documentation where
the SDK objects do not expose the governing fact.

The evidence must have been produced for operating NATS, not authored as a proposed
ONTOK model.

### Things

Answer, without construct vocabulary:

1. What things in the world the evidence is of and how they compose.
2. Which things already exist in Core and which are new to the bus domain.
3. What each thing is in nature and what must be true of every one.
4. The best domain name for each thing.
5. Which parts are NATS's account of a thing rather than the thing itself.
6. How the event-driven ONTOK world changes when these things are recognized.
7. The exact create/change/unchanged discovery schema.

### Constructs

Only after the things schema passes, select the smallest TCA construct for every
approved thing, place it in the dependency graph, audit all four breaks, and persist
the exact constructs/holders/removed schema. Build exactly that set.

## Questions discovery must settle

These are questions, not a preapproved type list:

- What is published: an ONTOK fact, a reference to one, or a transport
  representation of one?
- What makes one publication the same publication across retries?
- What is a delivery, and how is it distinct from the published fact?
- What does acknowledgement establish, and whose knowledge does it represent?
- How are rejection, retry, redelivery, expiry, and terminal failure distinguished?
- Which ordering promises exist, and what scope owns each promise?
- What is durable: the fact, its publication, a provider's retained representation,
  or a consumer's progress?
- What does a consumer represent independently of any process currently running?
- Which routing distinctions are meaning and which are provider addressing?
- What idempotence belongs to the producing domain, consuming domain, or bus?
- Which capabilities can be required, offered, or unavailable without pretending
  all providers have identical semantics?
- What context, authority, causation, and trace information must survive transport?

## Provider-neutrality

Provider-neutrality means stable ideas with explicit capability distinctions.

- Do not flatten logs, queues, streams, topics, subjects, subscriptions, consumer
  groups, and cloud event routers into one string field.
- Do not promise "exactly once" without naming the exact scope and proof supplied
  by a provider.
- Do not turn provider configuration into bus semantics.
- Do not force every provider to simulate a capability it does not possess.
- Represent a genuine choice as a union or refinement, not flags and optional
  fields.
- Keep provider policy vocabularies in provider modules unless discovery proves a
  provider-independent idea.

## Pydantic execution substrate

- Every semantic bus fact is a strict, frozen Pydantic construction.
- Every meaning has exactly one structural home.
- The outer construction consumes an arrived representation whole.
- Nested annotations construct every reachable constituent.
- Construction selects delivery, acknowledgement, failure, and capability variants
  where discovery establishes those axes.
- Construction failure propagates; it is never converted into a partial message,
  default acknowledgement, status flag, or retry decision.
- No loose `dict`, generic metadata bag, untyped header map, or `bytes` payload API
  carries domain meaning.
- Serialization occurs exactly once at a provider binding.
- The one live consistency boundary holds provider clients and current proven bus
  state; frozen bus facts hold no client or handle.

## Interchange standards

CloudEvents, AsyncAPI, W3C Trace Context, and relevant CNCF or protocol standards
are evidence and interoperability assets. They may supply vocabulary, wire
projection, or contract descriptions where useful. They do not automatically
define ONTOK's programming model and must not be copied wholesale into Core or the
bus domain.

## Provider contract

`ontok-bus` owns the contracts its consumers require. Provider packages realize
those contracts through dependency inversion.

- Contracts accept and return constructed bus facts, never provider SDK objects.
- Provider-specific arrivals are lifted before crossing the contract.
- Provider selection and client construction remain at the composition root.
- The bus contract does not expose a generic `publish(topic, bytes)` or
  `subscribe(callback)` convenience surface.
- The contract is capability-honest: unsupported behavior is structurally absent or
  represented by an explicit constructed alternative, never discovered by runtime
  convention.

The exact contract surface is withheld until discovery establishes the bus things
and their construction graph.

## Relationship to ontok-ex

`ontok-ex` owns execution semantics. It consumes and emits bus facts but does not
own transport semantics.

- Execution requests, activations, completions, and execution idempotence belong to
  EX only if discovery establishes them as execution-domain things.
- Publication, delivery, acknowledgement, and provider progress belong to the bus
  domain only if bus discovery establishes them.
- EX must not name NATS subjects, streams, durable consumers, SDK replies, server
  processes, or JetStream policies.
- Removing or replacing NATS must not change the EX model.

The later split removes NATS assets and plans from `ontok-ex`, adds an
`ontok-bus` dependency, and binds EX to bus contracts through its single live
boundary. That work occurs only after the bus discovery schema is complete.

## Conformance strategy

The bus module owns a reusable provider conformance contract. Each provider package
runs it against real infrastructure in addition to its provider-specific tests.

Tests prove difficult system behavior, not Pydantic guarantees or line coverage:

- a constructed fact survives publication and delivery without semantic loss;
- duplicate publication and redelivery do not silently duplicate domain effects;
- acknowledgement occurs only after the fact required by the contract exists;
- producer failure cannot appear as successful publication;
- consumer restart preserves the promised durable progress;
- ordering holds exactly within its declared scope and nowhere broader;
- malformed, partial, or contradictory provider arrivals cannot construct bus
  facts;
- cancellation, reconnect, timeout, backpressure, and shutdown do not lose or
  falsely acknowledge work;
- two concurrent producers and consumers converge according to the declared
  guarantees;
- one provider's unsupported capability cannot masquerade as a successful common
  operation.

Expected and observed states are constructed as strict Pydantic facts. A passing
test means an invariant was constructed from real behavior or an illegal system
state could not be produced.

## Forbidden substitutions

- Do not add bus behavior to Core or introduce a thirteenth primitive.
- Do not put NATS, Kafka, AMQP, Pulsar, or cloud-provider names in bus semantics.
- Do not derive the domain by intersecting provider schemas.
- Do not create a generic message envelope before discovery proves what it means.
- Do not model transport messages as Core `Event` merely because they move through
  time.
- Do not use `type`, `kind`, registry identifiers, or generic metadata to recover
  meaning already carried by Python classes.
- Do not build a provider switch, plugin registry, factory, service locator, or
  optional-extra provider bundle.
- Do not hide delivery guarantees behind booleans, nullable fields, or prose.
- Do not test Pydantic behavior that Pydantic itself guarantees.
- Do not author implementation before the evidence/things/constructs gate passes.

## Build sequence

1. Split this directory onto `module/ontok-bus` without carrying unrelated
   worktree changes.
2. Render the standard Python package skeleton and add an implementation-independent
   `ontok-bus` specification.
3. Capture whole real NATS evidence for the bus questions.
4. Complete and persist domain discovery: evidence, things, constructs.
5. Implement exactly the approved strict Pydantic construction graph.
6. Define the smallest consumer-owned provider contracts implied by that graph.
7. Add semantic tests using constructed expected and observed facts.
8. Add the reusable adversarial provider conformance suite.
9. Add a minimal provider-free README example using a test realization at the
   composition boundary, not a fake semantic model.
10. Run pytest, Ruff, formatting, basedpyright, import-linter, specification checks,
    and wheel/sdist isolation checks.
11. Audit every construct for escaped, duplicated, vacuous, and fused meaning.

## Definition of done

- Bus ideas are named from real evidence and are independent of provider schemas.
- Core remains unchanged and retains exactly twelve primitives.
- EX can depend on the bus without importing any provider.
- NATS and future providers can realize the contracts without entering the bus
  domain.
- Provider differences remain explicit and capability-honest.
- Every ingress constructs whole through Pydantic; no parser, mapper, JSON detour,
  or loose message dictionary exists.
- The reusable conformance suite proves reliability under failure, concurrency,
  restart, redelivery, and malformed provider behavior.
- Removing every provider package loses no bus-domain meaning.
