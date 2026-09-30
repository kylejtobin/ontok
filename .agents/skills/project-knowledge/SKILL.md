---
name: project-knowledge
description: The always-active protocol for wiki/, the project's durable shared knowledge. Use at the start of every task to orient, before delegating to give a subagent its context, whenever something durable is learned, changed, or contradicted, and before finishing to reconcile. Also the standard for writing any page.
---

# Project Knowledge

`wiki/` is what this project knows that the code does not say. Each module is its own specification; tests and tool configuration are the evidence about what runs. The wiki is the evidence about how each module is composed and why, what must hold, and what an operator does. A page that restates a source file is deleted.

## The loop

1. **Orient.** Read `wiki/index.md`, then the index of each directory the task touches, then only the pages the task needs.
2. **Observe.** While working, note every durable thing learned, changed, or contradicted: a decision, a procedure, a rule, a constraint a module carries.
3. **Reconcile.** Before finishing, update the page that owns the knowledge, create the smallest page when none owns it, or state that there is no knowledge delta. The wiki change is part of the same commit as the code change.

Before delegating, give the subagent the paths of the pages it needs. Require its report to name its evidence, any contradiction with the wiki, and a knowledge delta of `add`, `update`, `deprecate`, `conflict`, or `none`.

## Directories

| Directory | Question it answers | Page type |
|-----------|---------------------|-----------|
| `architecture/` | how each module is composed, how a fact comes to exist in it, and why | Architecture, one page per module |

A page goes in the directory whose question it answers. A new directory is added when a page answers a question none of these does, with an `index.md` and a row here.

## What is knowledge

Write what changes future building, decisions, operations, or verification. Update before adding. One subject is one page. Never store transcripts, scratch work, source-tree inventories, primitives or fields the code already declares, dependency tables that restate a `pyproject.toml`, speculative taxonomy, or private reasoning. Rationale lives only in an architecture page's decisions, one sentence per choice; everywhere else a decision's result is stated on the page that owns it.

## A page states what is

A page carries no status. Nothing planned, pending, deferred, or partially built appears on any page. A design becomes a page only in the commit that makes every sentence of it true, so a page is either wholly true of the code or it is a lie to be corrected in the next commit. There is no third state.

## Standard

- [writing-rules.md](writing-rules.md): the shape and voice of each page type, frontmatter, indexes, and links. Read before writing a page.
