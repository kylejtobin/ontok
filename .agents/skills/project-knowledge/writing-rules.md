---
type: Reference
description: The shape and voice of each page type, frontmatter, indexes, and links. Read before writing a page.
---

# Writing rules

No hedging, narration, or performance in any page. A sentence that explains, justifies, reassures, or marks something as provisional is deleted. A page states current state only: no history, no future tense, no deferral, no status.

## Frontmatter

```yaml
---
type: Architecture
title: ontok-core
description: One sentence saying what the page is, written for a reader deciding whether to open it.
generated:
  by: claude-code/claude-fable-5-1
  at: 2026-09-30T00:00:00Z
sources:
  - id: spec
    resource: ../../spec/ontok-core.xml
    title: Core specification
---
```

`type` is one of Architecture, Procedure, Policy. `title` is the page's H1. `generated` says who produced the page and when. `sources` cites what the page describes or was drawn from. `verified` is added only after an actual check of the thing described, with who and when.

## Indexes and links

Every directory has an `index.md`: a title, one sentence stating the question the directory answers, and one line per page or subdirectory, `- [name](./name.md): <the page's description>`. Module pages list in dependency order, Core first. Procedures list in operational order; policy sections in reading order.

Links are relative markdown links that resolve. Link to a page rather than restating it. A link to a specification or source file is allowed when the page's subject is how to use it. Filenames are lowercase and hyphenated, naming the thing; a module's page is named for its distribution.

## Architecture

One page per module, `wiki/architecture/<distribution>.md`: constraints, the context diagram as Mermaid C4 text, the building blocks, the startup order, the construction view, decisions, quality scenarios, glossary. The building blocks are Mermaid C4 container text where the module has running parts and a Mermaid class diagram of its constructs where the module is a type system. The startup order appears only for a module with running parts. The construction view states how a fact comes to exist in the module: what refines what, what constructs from what, and what is refused. Each decision is one bold-led paragraph of at most 80 words stating the choice as present fact, the one reason it is what it is, and what it rules out.

A structural change, meaning a primitive, construct, field, module dependency, running part, transport, or crosscutting rule added, removed, or rewired, is stated first as its design, the declarations by construct and each new thing's place in the specification and in the startup order where one exists, and then lands as an edit to the section it changes, the specification, and the code in one commit. Git is the history; no superseded text remains on the page. A new term joins the glossary in the same commit that introduces it.

## Procedure

Write for an operator executing at 3am. Title, preconditions, numbered imperative steps, nothing else.

- One command per step, in a fenced block, copy-pasteable
- State what success looks like and what to check on failure
- No prose between steps, no context paragraphs, no options
- Destructive steps say so in the preconditions line
- A step that is an edit rather than a command says exactly which file and which field

## Policy

Write a normative standard. Definitions once, on the policy's definitions page; clauses numbered from 1 on each page and cited as `<page>.<n>`. Use "must", "must not", "may", and "is"; never "should", "ideally", "consider", or "by default".

- One rule per clause, no compound clauses
- A term used in a clause is defined on the policy's definitions page
- No examples of bad practice, no rationale, no hedging
- A mapping is a table; the clauses that follow refer to it
