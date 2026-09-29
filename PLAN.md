# ONTOK event system plan

## Scope

This branch builds ONTOK's event system as three packages:

| Package | Owns | Depends on |
|---|---|---|
| `ontok-bus` | provider-independent meaning: address, publication, subscription, delivery, disposition, latest read, the provider contract | `ontok-core` |
| `ontok-nats` | the NATS JetStream realization of the bus contract | `ontok-bus`, the official NATS client |
| `ontok-ex` | executing `Work`: subscriptions derived from work kinds, deterministic identity, the delivery run | `ontok-core`, `ontok-bus` |

A composition root selects the provider. `ontok-ex` never names NATS. Core does not change.

The architecture is event sourcing: an append-only log of immutable facts, durable at-least-once subscriptions, idempotent handling, prior state read from the log, and read models rebuilt by replay.

## Acceptance

The first consuming organization's program, using only `ontok-core`, `ontok-bus`, `ontok-nats`, and `ontok-ex`, proves five functions against a real NATS server:

1. **Publish.** A fact it publishes lands on the log.
2. **Handle.** A work kind it defines receives the facts of the kind it consumes.
3. **Emit.** Facts that work emits reach the next work kind.
4. **Read latest.** It reads the latest fact for a key.
5. **Replay.** A read model rebuilt from the start of the log is identical.

## Decisions

**What is published.** The fact itself. The log is the only durable store of facts; a second store would give one meaning two homes. The message is the provider's representation of the fact. Large originals live outside the log, and the fact carries their digest.

**Fact identity.** A fact's identity is deterministic from its causes, so a retry after a crash produces the same fact rather than a duplicate.
- A fact emitted by work has a UUIDv7 id whose timestamp is its cause's and whose remaining bits are a hash of the work kind, the cause's id, and the output's position. It is a valid v7, time-ordered by cause, and identical on every retry.
- An originating fact mints its id once at its source; a fact about an original derives its id from the original's digest.

**Address.** A fact's address is its kind, its key, and its own id. The kind is the class. The key is what the fact is about, declared by every publishable kind as a derivation; a fact that is about itself uses its own id. The provider maps an address to its own syntax. Accounts isolate organizations, so addresses carry no organization prefix.

**Publication.** Every fact is published at its own address expecting nothing there. The outcome is one of three:
- **Written.**
- **Already present:** the fact at that address has the same id. This is success; the fact is on the log.
- **Conflict:** an expectation failed for another reason.

A successor also expects the latest fact under its key to be its prior. Optimistic concurrency is enforced by the log, with no lock and no deduplication window.

**Latest read.** The last fact under a kind and key, or none.

**Subscription.** A work kind's standing interest in the kind it consumes, with its progress. It exists independently of any running process, is named from the work kind, and is created by the program, because subscriptions are program meaning. Storage is infrastructure and is declared outside the program. A subscription starts at the next fact or at the beginning of the log.

**Delivery.** The provider handing one fact to one subscription, possibly more than once. The work receives the fact. EX holds the delivery and disposes of it.

**Disposition.** Exactly three:
- **Complete:** every consequence of the fact is durable. It records the subscription's progress and is never a domain fact.
- **Retry:** try again later.
- **Reject:** the delivery is terminal. The provider's own account of the termination is the record; the bus reads it rather than inventing a second one.

**Ordering.** A subscription handles its facts one at a time in log order. The promise is scoped to the subscription, and the cost is throughput.

**Durability.** The fact, retained in the log, and each subscription's progress are durable. A publication is an act whose result is the retained fact. A log sequence orders facts; it does not identify them.

**Idempotence.** The bus owns publication idempotence. EX owns deterministic identity for work and everything it emits. The domain owns pure construction. Each has one home.

**Causation.** An emitted fact references the work that produced it; the work references the fact it consumed. Causation is a relation between events and is never inferred from temporal order.

**Work.** An executable unit is a refinement of Core `Work` whose required field is the fact it consumes. Its subscription derives from that field's type, so there is no registration table and no subject-to-class dispatch. The composition root binds the work kinds a process runs. The work fact is published as provenance.

**State.** Each delivery reads what it needs from the log through read interpreters nested in its construction. The log is the state. There is no mutable consistency model and no current-state holder.

**Capability.** A bus provider offers conditional append on an address, the latest read under a key, and durable ordered subscriptions with explicit disposition. A provider without them is not a bus provider; the bus does not simulate what a provider lacks.

## Evidence gate

Before any source is written, confirm on a real NATS server with accounts and a scoped, non-administrative identity, through the official Python client:

1. A publish expecting nothing at an exact subject succeeds once and is refused after.
2. A publish expecting a last sequence across a wildcard subject enforces succession.
3. Direct get returns the last message across a wildcard subject.
4. The scoped identity creates its own durable consumers on the fact stream, receives termination advisories, and is refused stream administration.

Record the rendered evidence here. If 2 or 3 is unavailable, the address is kind and key; succession uses the exact-subject expectation; a retry is recognized by comparing ids; kinds that accumulate facts under one key use per-fact addresses.

## Order

1. **Evidence.** The gate above.
2. **`ontok-bus`.** Address, publication and its outcomes, subscription and its start, delivery and its dispositions, the latest read, the publishable-kind key requirement, and the provider contract. No provider names.
3. **`ontok-nats`.** Subjects from addresses, conditional publish headers, direct get, durable pull consumers with explicit acknowledgement, the three dispositions, termination advisories, consumer creation, and server monitoring reads. Its tests against a real server are the provider conformance suite: routing, idempotent publication, succession conflict, latest read, ordering, durability across restart, dispositions, and replay from the beginning.
4. **`ontok-ex`.** Work refinements with consumed-fact fields, subscriptions derived from them, deterministic identity, and the delivery run: construct the work, publish the work fact, publish what it emits, then complete. Replay is the same run from a subscription that starts at the beginning.
5. **Acceptance.** The five functions above.
6. **Specification.** `spec/ontok-bus.xml` and `spec/ontok-ex.xml` from the built model, with this plan updated to what was built.

## Out of scope

Retry with delay and rejection handling beyond the three dispositions, multiple providers, the bundled server and cross-platform wheels now in `ontok-ex`, clustering, key-value and object stores, and tracing. The bundled server belongs to `ontok-nats` when distribution is taken up.

## Open for Core

Core `Work` embeds a whole `Action` with its role and goal, and every work fact of one kind embeds the identical one. This is the same question as `Connection` embedding its endpoints: whether a primitive embeds a node or references it by identity. It is decided with the evidence this work produces, not before.
