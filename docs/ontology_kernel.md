# Ontology Kernel (ONTOK)

## Purpose

The Ontology Kernel (ONTOK) is a proposed minimal ontology architecture for machine knowledge systems.

Its purpose is not to model any particular domain. It defines the smallest stable conceptual foundation from which arbitrary domains can be represented, extended, retrieved, revised, and reasoned over.

The motivation comes from a convergence of fields that have historically developed in parallel. Philosophy asked how reality should be categorized. Ontology engineering asked how meaning should be represented consistently across systems. Knowledge graphs asked how structured facts should be connected. Recent AI research asks how a machine can accumulate knowledge that remains useful across time instead of repeatedly reconstructing it from documents.

ONTOK begins from the observation that these are no longer independent questions. Persistent machine knowledge requires a stable conceptual architecture that can support:

* ingestion
* consolidation
* retrieval
* revision
* explanation
* reasoning

## The Problem

Most current AI systems are assembled from separate representations:

* documents preserve source material
* embeddings provide semantic similarity
* knowledge graphs represent explicit relationships
* prompts provide temporary working context
* application code imposes rules and workflow behavior

Each representation solves a different problem, but none defines what the system fundamentally knows. Identity, temporal validity, contradiction, provenance, and context are often reconstructed separately inside each component. The result is that the same knowledge exists in incompatible forms.

Recent work on temporal knowledge graphs, semantic memory, episodic memory, and graph-augmented retrieval increasingly converges on the idea that durable machine knowledge cannot remain purely document-centric or embedding-centric. Systems such as AriGraph, Graphiti, and related research distinguish between observations, structured knowledge, and higher-level semantic memory because these play different roles during retrieval and reasoning.

The important conclusion is not that every system should become a knowledge graph. The conclusion is that retrieval depends on coherent conceptual structure. A graph is only one possible implementation of that structure.

## The Research Question

The central question is not how knowledge should be stored, and it is not which ontology language should be used.

OWL, RDF, RDFS, SHACL, and similar technologies are languages for expressing ontologies. They are not themselves ontologies.

Likewise, schema.org, FOAF, FIBO, BFO, DOLCE, and SUMO are different conceptual systems built using those languages. They make different assumptions about how reality should be decomposed.

The more fundamental question is:

> What is the minimal conceptual architecture from which machine knowledge should be constructed?

Instead of choosing a vocabulary, ONTOK identifies the smallest set of conceptual primitives required for arbitrary knowledge systems.

## Why a Kernel?

The term *kernel* is intentional. Like an operating system kernel, ONTOK represents the smallest trusted conceptual core from which larger systems are built. It should remain small, stable, and difficult to change.

Everything else, including domain ontologies, should specialize the kernel rather than modify it. A healthcare ontology should introduce concepts such as Patient and Diagnosis. A financial ontology should introduce concepts such as Position and Instrument. Neither should redefine the conceptual machinery by which identity, events, evidence, context, or temporal validity are represented.

The kernel exists to keep those foundations consistent across domains.

## Design Criterion

Traditional ontology work often evaluates conceptual correctness. ONTOK is evaluated by operational capability.

Every primitive must improve one or more fundamental knowledge operations:

* acquisition
* organization
* retrieval
* revision
* reasoning
* explanation
* consolidation

The test is not whether a category is intellectually satisfying. The test is whether removing it would make the machine materially worse at constructing or using knowledge.

## Proposed Kernel

The current kernel consists of ten primitives:

```text
Entity
Event
State
Role
Relation
Claim
Evidence
Context
Concept
Rule
```

These are intentionally abstract. They are not intended to describe the world directly. They define the conceptual machinery from which descriptions of the world can be built.

"Person" is not part of the kernel. It is a specialization of Entity.

"Employment" may be represented as an Event, a State, a Role, a Relation, or a combination of these depending on domain semantics. The kernel does not dictate domain modeling decisions. It provides the primitives from which those decisions can be expressed consistently.

## Primitive Responsibilities

**Entity** represents persistent identity. It anchors the system’s ability to decide whether two references concern the same thing across documents, conversations, systems, or time.

**Event** represents occurrence and change. It gives the system a way to organize episodes, transitions, actions, observations, and historical sequence.

**State** represents a condition that is true over some interval or within some scope. It allows the system to distinguish current truth from historical truth.

**Role** represents contextual participation. An Entity can play different roles in different contexts without becoming a different Entity.

**Relation** represents typed connection. It enables graph traversal, dependency discovery, semantic navigation, and structured retrieval.

**Claim** represents assertion status. The system should not treat every extracted statement as settled truth. Claims can be supported, contradicted, revised, merged, deprecated, or promoted.

**Evidence** represents support. Evidence may be a source span, document, message, transcript, API result, observation, or tool output. It keeps knowledge traceable.

**Context** represents scope. Context prevents local truths from being treated as universal truths.

**Concept** represents reusable classification. Domain ontologies extend the kernel by specializing Concepts.

**Rule** represents constraints, derivations, identity policies, contradiction policies, and retrieval policies. Rules govern how knowledge behaves.

## Knowledge Construction

A strong observation from recent memory and retrieval research is that durable knowledge is layered. Raw observations are not yet knowledge. They become candidate assertions. Assertions accumulate supporting or conflicting evidence. Stable patterns eventually consolidate into reusable semantic knowledge while remaining traceable to their origin.

The conceptual progression is:

```text
Evidence
  -> Claims
  -> Entities, Events, States, Relations
  -> Domain Concepts
  -> Derived Knowledge
```

This progression is more important than any particular storage technology because it separates observation from belief and belief from stable knowledge. That separation allows systems to revise conclusions without losing history.

## Declared Structure and Learned Structure

ONTOK does not assume that a machine's conceptual structure must be entirely hand-authored. A learned world model can have stable internal organization even when no human-readable declaration language exists.

The important distinction is not symbolic versus learned. The important distinction is implicit versus explicit structure.

ONTOK concerns the structure itself. Some systems may learn parts of it. Others may declare it. Practical systems will likely combine both approaches, allowing learning to propose new concepts while preserving an explicit foundation for interoperability, explanation, governance, and long-term consistency.

## Relationship to Retrieval

ONTOK is not a retrieval algorithm. Retrieval is the operation that exposes weaknesses in conceptual organization most quickly.

To retrieve correctly, a system must distinguish:

* persistent identity from temporary state
* observations from asserted knowledge
* historical truth from current truth
* local context from global validity
* evidence from inference
* relationships from coincidence

A system that cannot make these distinctions cannot retrieve reliably, regardless of the sophistication of its embedding model or search algorithm. For this reason, retrieval becomes the practical test of the ontology rather than its definition.

## Relationship to Storage

ONTOK avoids coupling itself to any storage technology. However, it aligns naturally with declarative fact systems because knowledge construction is fundamentally recursive.

The relevant operations include:

* evidence supporting claims
* claims revising other claims
* events changing states
* rules deriving new conclusions
* identity resolution depending on existing relationships
* retrieval combining graph structure, semantic similarity, temporal scope, and contextual constraints

These are recursive operations over knowledge rather than isolated database queries. A declarative substrate is therefore a natural implementation, but the ontology remains independent of any specific engine.

## Working Thesis

The Ontology Kernel identifies the smallest conceptual foundation required for machines to build coherent, durable knowledge across arbitrary domains.

It does not propose a complete ontology of reality. It proposes a stable foundation from which richer ontologies can emerge while preserving consistency in the operations that matter most:

* acquiring knowledge
* organizing knowledge
* retrieving knowledge
* revising knowledge
* explaining knowledge
* reasoning over knowledge
