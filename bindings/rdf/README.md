# Pydantic-to-RDF ontology compiler: inspection build

## Goal
Translate the supplied organizational modeling package to an OWL/RDFS TBox and
SHACL instance-shape declarations while retaining the compositional distinctions
of the source Pydantic v2 type system.

## Inputs
`core_to_rdf.py` directly inspects the original Python classes' resolved
`__pydantic_core_schema__` and Python subclass lineage. It deliberately does
not use JSON Schema as the authoritative source because some constraints do
not survive that projection precisely (for example, strict Decimal input).

## Artifacts
- `ontology.ttl`: OWL classes, subclass hierarchy, scoped properties, property
  restrictions, named variants and their logical unions where representable.
- `shapes.ttl`: SHACL shapes for properties, required/min/max cardinality,
  constrained literals, root-model payloads, correlated discriminated unions,
  and fixed/variable tuple members encoded as RDF collections.
- `typing.ttl`: RDF metadata recording generic type arguments, source Python
  class identities, normalization, configuration, and strict scalar declarations.
- `coverage.json`: type and statement counts.

## RDF encoding agreement
An instance of a Pydantic BaseModel/RootModel becomes an RDF resource with an
`rdf:type` of its concrete generated class URI. Its fields become triples using
that declaration's model-field predicate. `RootModel` has one `root` predicate.
Tuples become RDF collections ordered with `rdf:first`/`rdf:rest`, ending at
`rdf:nil`. Scalar types must be projected into the canonical RDF datatypes
specified by the SHACL shapes, such as `xsd:decimal`, `xsd:integer`,
`xsd:dateTime`, and `xsd:dayTimeDuration`.

The code defines a *schema conversion*, not a serializer from actual Pydantic
instances into RDF. A proper converter must implement that serializer before
end-to-end validity parity can be established.

## What is actually verified
- The script completes without ignoring an unrecognized Pydantic CoreSchema
  node in the supplied package.
- All 19 named concepts appear as OWL classes with SHACL target shapes.
- The asserted Process/Activity, Economic/Value, RefundPurpose/Purpose lineage
  paths exist.
- SHACL alternatives are emitted as `sh:xone` for tagged unions.
- All generated Turtle parses, and generated SPARQL selects parse.

## Not yet proven / not ready to assert full semantic equivalence
- pySHACL (or equivalent SHACL Core + SHACL-SPARQL engine) was unavailable in
  this runtime, so SHACL instance validation has not been run.
- No canonical Pydantic-instance to RDF encoder exists yet, so positive and
  negative instances have not been checked for validation parity.
- XML Schema temporal/Decimal lexical and datatype comparison behavior requires
  target-validator compatibility testing, as do Pydantic's whitespace
  normalization and default materialization.
- For full semantics, a domain-specific mapping must specify identity of RDF
  instance resources, bnodes, and any external references; Pydantic model
  definitions alone do not establish those identities.
- `frozen` object-mutation semantics and Pydantic-specific coercion modes do
  not have equivalent OWL class axioms; where relevant they should be retained
  as source-language metadata and distinguished from RDF validation semantics.

**Do not describe these files as a proven lossless export.** Run differential
property-based tests: for each concrete model, serialize valid and invalid
cases, compare Pydantic validation with SHACL validation, and repair any
mismatch in the converter's mapping rather than weakening the ontology.

## Run

```bash
PYTHONPATH=path/to/original/package/src python core_to_rdf.py --output rdf-schema
PYTHONPATH=path/to/original/package/src python verify_export.py
```

Dependencies: `pydantic>=2.13`, `rdflib>=7`. For the future equivalence tests,
use a SHACL validator that supports SHACL-SPARQL, plus the corresponding Pydantic
and RDF instance encoding libraries.
