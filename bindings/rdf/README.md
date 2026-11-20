# RDF export: unfinished experimental work

This directory is not a supported Ontok binding. Nothing here is an authoritative or verified RDF representation of Ontok, and no generated graph is kept in the repository.

Ontok defines the semantics (see `rfc/ontok.md`). An RDF binding would represent those semantics for graph use. It does not get to define them.

## What is here

- `core_to_rdf.py`: an experimental compiler that walks the Pydantic core schema of the Python binding and emits OWL/RDFS, SHACL, and metadata graphs.
- `verify_export.py`: structural smoke checks over the compiler's output. They confirm that named classes and shapes exist and that the Turtle and SPARQL parse. They are not conformance evidence and say nothing about whether the graph means what Ontok means.

## Known defects

- Identifiers are derived from Python class paths. That is not a stable, language-independent identity for an Ontok concept.
- The namespaces are `example.org` placeholders.
- The compiler reflects whichever Python classes exist. It does not map the established Ontok concepts and their structural semantics.
- There is no encoder from constructed instances to RDF.
- No SHACL engine has been run against the shapes.

## Required before this is a supported binding

- Stable Ontok identities for the foundational concepts and relationships.
- Preservation of inheritance, composition, cardinality, and correlated alternatives.
- An explicit RDF instance representation.
- Differential tests demonstrating that valid and invalid constructions behave consistently under Pydantic and SHACL.

A graph that parses is not evidence that the graph means the same thing. Generated artifacts stay out of the repository until these requirements are demonstrated.

## Running the experiment

```bash
PYTHONPATH=bindings/python/src python bindings/rdf/core_to_rdf.py --output <directory>
PYTHONPATH=bindings/python/src python bindings/rdf/verify_export.py <directory>
```

Dependencies: `pydantic>=2.13`, `rdflib>=7`.
