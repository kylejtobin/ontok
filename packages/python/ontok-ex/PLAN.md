# ONTOK EX — NATS-Backed Event-Driven Work Execution

## Telos

`ontok-ex` makes an organization's modeled `Work` executable through event-driven
architecture.

ONTOK has one type system: Core. EX models its domain by refining Core primitives.
The class is the kind. Fields are relations. Pydantic construction is execution.

An organization uses EX by refining EX's kinds into its own events and work. Its class
graph is the work DAG. Constructed values are occurrences and undertakings in that DAG.
NATS JetStream is the first concrete event system and the bundled runtime.

EX is not a workflow language laid beside ONTOK, a registry of classes, a graph document,
or a handler framework.

## Decisions

1. Development proceeds concrete-to-general:
   1. bundle and run NATS;
   2. discover and model the NATS slice used by execution;
   3. discover and model general EDA from that concrete model;
   4. construct the generic DAG runner from those types.
2. NATS JetStream, not Core NATS alone, supplies durable streams, pull delivery,
   acknowledgements, redelivery, and replay.
3. The initial runner uses one local NATS server with JetStream enabled. Clustering,
   federation, leaf nodes, gateways, and NATS administration are outside the first
   executable graph.
4. The initial delivery contract is at-least-once. Event identity and durable facts make
   repeated delivery idempotent. No exactly-once claim is permitted.
5. Explicit acknowledgement occurs only after the successor fact is constructed and every
   required durable publication is acknowledged by JetStream.
6. JetStream is the first durable event store. Do not add a second database before evidence
   proves a separate meaning that JetStream cannot own.
7. Writable data lives under the configured cross-platform data directory. Nothing writes
   into the installed package.
8. NATS is concrete evidence and a concrete realization. It is not permission to copy the
   entire NATS API into EX.

## Invariants

### One ontology

- Every semantic EX class is a kind of a Core primitive.
- A new EDA name with no Core parent is not modeled.
- Core primitives are not used raw where the EDA thing has narrower meaning.
- Do not create `Event(Event)`.
- Do not add instance `type`, `kind`, `TypeId`, URI discriminator, or registry fields to
  recover meaning already carried by the class.
- Standard EDA vocabulary is preferred. A different name requires a different meaning, not
  discomfort with an existing word.

### Construction is the program

- User-defined work DAGs are class-and-field dependency graphs, not separate graph values.
- Exact event dependencies are exact typed fields on refinements of `Work`.
- Conjunction is a product of required fields.
- A genuine domain alternative is a union.
- Fan-out is multiple constructed work facts depending on the same event fact.
- A join is a work fact whose required fields own all joined facts.
- No scheduler, readiness flag, pending state, enabled set, or next-step field duplicates
  constructibility.
- No mapper, parser pipeline, handler chain, or orchestrator performs work that belongs to
  construction.

### The live edge

- Time, NATS clients, the NATS server process, delivery, publication, and acknowledgement
  meet in one consistency model.
- Frozen models contain no live client or process.
- NATS SDK objects are foreign evidence at the boundary, never the domain model.
- A NATS binding performs transport calls and serialization only.
- Failed construction means no domain fact was built. It is not a workflow status.

## Current concrete substrate

The repository contains:

- `src/ontok/ex/bin/linux-amd64/nats-server`
- NATS Server `v2.14.6`
- the upstream NATS license
- a manifest recording source archive and checksums
- an 18 MB statically linked Linux AMD64 executable

This artifact is the development substrate and evidence source. It is not yet a
cross-platform release strategy.

The current wheel is not releasable while it contains a Linux executable under a
`py3-none-any` tag.

## Phase 1 — Prove the bundled NATS substrate

### Runtime proof

Run the bundled server with:

- JetStream enabled;
- its store under `ExecutionConfig.data_directory`;
- a test-owned port;
- no write beneath `site-packages`;
- deterministic shutdown.

Prove:

- the exact bundled version starts;
- JetStream reports ready;
- restart reads the same store;
- package-resource lookup finds the executable without assuming the repository layout;
- unsupported OS/architecture produces a constructed, explicit refusal rather than an
  attempted process launch.

### Packaging proof

Prove the wheel contains:

- the executable for its declared platform;
- `NATS-LICENSE`;
- `NATS-MANIFEST.json`;
- executable permissions where the wheel format preserves them.

Do not publish a universal wheel containing one platform's executable.

## Phase 2 — Render real NATS evidence

Install the official Python NATS client only when beginning this phase.

Use the bundled server and the official SDK to render whole, unedited evidence for exactly
the runner's reachable surface:

1. server connection information;
2. creation of one file-backed stream over one subject family;
3. creation of one durable pull consumer with explicit acknowledgement;
4. publication and its publish acknowledgement;
5. fetched message attributes:
   - subject;
   - reply subject;
   - headers;
   - bytes;
   - JetStream metadata;
6. metadata for stream sequence, consumer sequence, delivery count, timestamp, and pending
   count;
7. acknowledgement;
8. negative acknowledgement followed by redelivery;
9. server restart followed by durable replay;
10. two durable consumers receiving the same published fact.

Read the corresponding SDK models as written. The evidence is the SDK's account of NATS,
not automatically ONTOK's account of the world.

Do not inspect or model NATS KV, object store, services, request/reply, monitoring,
clustering, federation, gateways, leaf nodes, accounts, or authorization during this phase.

## Phase 3 — Discover the NATS execution domain

Run `/domain-discovery` over the Phase 2 evidence, one question per turn.

For every candidate thing:

1. decide what it is in nature;
2. decide which Core primitive it refines, or decide that it is transport representation
   and therefore a foreign model;
3. state what must be true of every one;
4. choose the established NATS or EDA name unless another meaning requires another name;
5. state how it composes with the other things;
6. distinguish the NATS source's representation from the thing represented.

No NATS source code is written until discovery produces the complete 2.7 schema and the
complete 3.6 construct schema.

The discovery must explicitly settle:

- whether stream, subject, consumer, message, delivery, publication, publish
  acknowledgement, and acknowledgement are things, relations, occurrences, undertakings,
  roles, or transport accounts;
- which meanings belong to NATS specifically and which already reveal general EDA;
- the identity of a publication versus the identity of a delivery;
- what repeated delivery is the same occurrence of;
- what JetStream sequence numbers order and what they do not prove;
- which facts survive server restart;
- which NATS fields are wire identity and which are aliases into ONTOK identity.

## Phase 4 — Implement only the discovered NATS slice

Build exactly the Phase 3 construct schema.

- NATS semantic kinds refine Core primitives.
- NATS SDK and wire shapes are foreign models.
- Aliases lift NATS shapes whole.
- No hand-built dictionaries copy fields.
- No generic metadata bag enters the domain.
- No class registry or subject-to-class dispatch table enters the domain.
- Configuration is frozen `BaseSettings`.
- Every behavioral claim about SDK or Pydantic construction receives a substrate test.

Run NATS model tests, Ruff, formatting, basedpyright, import-linter, and package tests before
starting general EDA discovery.

## Phase 5 — Discover the general EDA ontology

Use the completed NATS model as the first concrete world. Use established, implementation-
independent EDA evidence to separate what is general from what is NATS-specific.

The general ontology must account for the meanings required by the runner, including:

- an occurrence in the world versus its event-system representation;
- event source;
- production and consumption responsibilities;
- channel or stream membership;
- publication;
- delivery;
- subscription;
- acknowledgement and redelivery;
- event identity, correlation, causation, and ordering without collapsing them;
- the undertaking that consumes events;
- the events produced by that undertaking.

These are discovery subjects, not preapproved class names. Each resulting class must refine
a Core primitive and add the fields that make it that EDA kind. Concepts that exist only in
NATS remain NATS refinements. Transport representations remain foreign models.

No general EDA source is written until discovery produces the complete 2.7 schema and the
complete 3.6 construct schema.

The completed schema must answer, without placeholders:

- which EX events can enter executable work;
- how a work kind declares exact consumed event kinds;
- how produced event kinds own or otherwise relate to the work that produced them;
- how one event fact can participate in multiple work facts;
- how multiple event facts constitute one work fact;
- how alternatives are represented;
- how one execution is correlated without treating temporal order as causation;
- how domain `Rule` and `Context` constrain `Action` without becoming scheduler state;
- where event-system semantics end and NATS transport semantics begin.

## Phase 6 — Implement the general EDA ontology

Build exactly the Phase 5 construct schema by refining Core.

Requirements:

- domain experts recognize every name;
- every field is a declared type and one semantic relation;
- all semantic values are frozen;
- event data is exact fields on refinements, never `data: dict`;
- class identity carries event meaning;
- Core `Event` remains the universal occurrence and is not renamed or shadowed;
- Core `Work` remains the persistent undertaking and is not collapsed into an event;
- NATS meanings have one structural home after the general types exist;
- import direction is acyclic and ownership is one-way.

Run EDA ontology tests and all static gates before constructing the runner.

## Phase 7 — Discover the generic runner

The runner executes user refinements; it does not ask users to redescribe them in a second
graph.

Before runner source exists, construct substrate probes that settle:

1. how one outer constructor receives the organization's executable type graph;
2. how concrete event kinds are selected from arrived foreign messages without an
   instance-level type registry;
3. how exact work dependencies are discovered from owned typed fields without a separate
   DAG declaration;
4. how facts for a join are durably associated;
5. how repeated delivery reconstructs the same facts rather than duplicating work;
6. how a constructed work fact determines the exact event facts it produces;
7. how publication acknowledgement and message acknowledgement compose crash-safely;
8. how replay reconstructs runner state solely from durable facts;
9. how an unconstructible arrival remains transport refusal rather than domain state.

If a probe requires a registry, mapper, workflow status, or procedural DAG walker, stop:
the ontology is incomplete. Return to the earliest discovery answer that omitted the
meaning.

Run `/domain-discovery` for the live runner context after those probes. Produce the complete
2.7 and 3.6 schemas before implementation.

## Phase 8 — Construct the runner

Build exactly the runner construct schema.

The intended topology is:

- frozen EDA and NATS facts at the center;
- one unfrozen consistency model holding live NATS clients and current constructed state;
- one NATS binding;
- one composition root that reads config, locates or starts the bundled server, constructs
  clients, and binds the consistency model.

Runner operations may only:

- capture an arrived foreign reply;
- construct one fact whose constituents construct inside that call;
- re-point current state to that proven fact;
- publish proven event facts;
- acknowledge delivery after durable publication proof.

No operation may sequence domain transformations, inspect generic dictionaries, branch on
class names, or maintain a second dependency graph.

## Phase 9 — Prove event-driven DAG execution

Define a test-owned executable ontology solely by refining EX kinds. It exists to prove the
generic contract, not to become EX's public ontology.

Prove against the real bundled NATS server:

- one event constructs one work fact and its produced event;
- one event constructs two independent work facts;
- two required events construct one joining work fact;
- a genuine alternative constructs the declared union variant;
- an absent required event constructs no work;
- duplicate delivery constructs no duplicate work;
- negative acknowledgement redelivers;
- process restart replays durable facts and continues;
- publication is durable before input acknowledgement;
- event ordering does not manufacture causation;
- the test ontology imports EX, while EX imports none of the test ontology.

## Phase 10 — Cross-platform distribution

Support at minimum:

- Linux AMD64 and ARM64;
- macOS AMD64 and ARM64;
- Windows AMD64 and ARM64.

Do not commit every uncompressed binary to the repository.

Build platform-specific wheels in CI by downloading the pinned upstream archive, verifying
the recorded SHA-256 digest, extracting only `nats-server` plus required license/SBOM
material, and assigning a truthful platform wheel tag.

The source distribution contains manifests and build instructions, not a falsely portable
Linux executable. Each wheel contains exactly one NATS target.

Test each wheel on its target:

- resource discovery;
- executable launch;
- writable JetStream store under the configured data directory;
- clean shutdown;
- Phase 9 smoke execution.

## Phase 11 — Specification and documentation

Only after the executable model passes:

- write `spec/ontok-ex.xml` from the final ontology;
- update `spec/README.md`;
- update the EX README with refinement examples and the NATS-backed runner;
- update package metadata so it no longer claims semantics the model does not provide;
- update the root README's EX description;
- document NATS version, license, checksums, supported platforms, data location, and
  configuration.

The specification names semantic kinds and laws. It does not describe Python procedures or
copy the NATS API.

## Final gates

- all EX tests;
- end-to-end bundled-NATS tests;
- Ruff check and format;
- basedpyright strict;
- import-linter;
- XML parsing;
- wheel and sdist content inspection;
- wheel installation and launch on every supported target;
- no source or wheel writes beneath `site-packages`;
- no uncommitted generated runtime data;
- four-break audit for every construct: escaped, duplicated, vacuous, fused;
- final diff review without committing.

## Forbidden substitutions

- Do not replace modeling with a NATS wrapper.
- Do not replace EDA with “it is events.”
- Do not replace refinement with matching an IT noun to a Core noun.
- Do not exclude broker, stream, subject, producer, consumer, subscription, message,
  delivery, or acknowledgement as “transport” before discovery decides what each is.
- Do not model the whole NATS API.
- Do not invent novel vocabulary merely to avoid standard EDA words.
- Do not build a one-off organizational workflow as EX.
- Do not infer the general ontology first and use NATS only as a later adapter.
- Do not discard the concrete NATS model when generalizing EDA.
- Do not begin implementation while a discovery schema still contains a question,
  placeholder, or unresolved semantic owner.
