# RFC-001: Contextix Architecture v3

Author: Lead Architect

Status: Draft

Date: 2026-07-03

---

# 1. Vision

## Why Contextix Exists

Modern software development increasingly depends on AI assistants.

Developers move between ChatGPT, Claude, Gemini, Cursor, Codex, local LLMs, and entirely new conversations every day.

Every transition has the same cost:

The developer must explain the project again.

Not because the AI cannot read source code.

But because the AI has lost the project's accumulated understanding.

The expensive part of software development is not source code.

It is shared understanding.

Source code tells an AI **what exists**.

Documentation explains **why it exists**.

Neither preserves the understanding that gradually emerges as a project evolves.

Contextix exists to preserve that understanding.

Instead of repeatedly reconstructing project knowledge from documentation, Contextix captures it once, maintains it over time, and makes it portable across AI assistants and conversations.

---

# 2. Product Vision

> Contextix preserves project understanding so any AI assistant can continue working with minimal re-explanation.

The objective is not repository compression.

The objective is not documentation generation.

The objective is continuity.

A project should feel like one continuous conversation, even when the developer changes AI assistants, starts a new session, or returns months later.

---

# 3. The Core Problem

Software evolves continuously.

Human understanding evolves slowly.

Today's AI workflows force developers to repeatedly rebuild the same understanding every time context is lost.

This creates unnecessary token usage, inconsistent reasoning, duplicated explanations, and degraded collaboration.

Contextix treats project understanding as a persistent asset rather than temporary prompt text.

---

# 4. What Contextix Is

Contextix is a context preservation engine.

It continuously transforms project documentation into a stable, portable representation of project understanding.

This representation is optimized for AI assistants rather than humans.

It captures knowledge that is expensive for humans to repeatedly explain but inexpensive for AI systems to consume.

---

# 5. What Contextix Is Not

Contextix is not:

- a code search engine
- a repository compressor
- an IDE replacement
- a documentation generator
- an AST indexing system
- a dependency graph visualizer

Those problems are already solved by existing tools.

Contextix focuses exclusively on preserving project understanding.

---

# 6. The Intelligence Boundary

AI assistants are already extremely good at discovering machine-readable facts.

Examples include:

- function definitions
- imports
- class hierarchies
- dependency graphs
- syntax trees
- API signatures

These can always be regenerated.

They are not Contextix's responsibility.

Instead, Contextix preserves information that source code cannot reliably express:

- project vision
- goals
- decisions
- rationale
- constraints
- domain terminology
- architectural intent
- future direction
- current project state

This boundary keeps Contextix focused while avoiding duplication with IDEs, LSPs, and AI assistants.

---

# 7. Guiding Principles

## Documentation First

Documentation is the primary source of project understanding.

Source code validates implementation.

Documentation explains intent.

---

## Stable Evolution

Project understanding should evolve slower than source code.

Small code changes should not completely rewrite project context.

Context should preserve identity while incorporating new knowledge.

---

## Portable Context

Generated context should work equally well with ChatGPT, Claude, Gemini, Cursor, Codex, or any future AI assistant.

No provider-specific assumptions should exist.

---

## Minimal Token Growth

Every additional token must justify its existence.

Generated context should grow significantly slower than the repository itself.

Repository size and context size are intentionally decoupled.

---

## Deterministic Output

Running Contextix twice against an unchanged repository should produce identical output.

Small repository changes should produce proportionally small context changes.

---

## Human Knowledge First

If an AI assistant can recover information directly from source code, Contextix should not store it.

Contextix exists to preserve human knowledge, not machine-readable structure.

---

# 8. Core Product Goals

Contextix should enable developers to:

• continue projects across different AI assistants

• preserve project understanding over time

• minimize repeated explanations

• maintain stable context across repository evolution

• reduce context token growth

• detect documentation inconsistencies

• provide trustworthy project memory

Every architectural decision should contribute to one or more of these goals.

Otherwise, it does not belong in the core product.

---

# 9. Knowledge Model

Project understanding is composed of knowledge that changes at different speeds.

Some knowledge rarely changes.

Some evolves every sprint.

Some is regenerated every execution.

Contextix separates these categories so each can evolve independently.

| Category | Purpose | Typical Source | Change Frequency |
|----------|----------|---------------|-----------------|
| Identity | Project identity | README, pyproject | Very Low |
| Vision | Long-term purpose | MANIFESTO, README | Very Low |
| Goals | Active objectives | PRD, README | Medium |
| Decisions | Architectural decisions with rationale | ADRs | Low |
| Constraints | Hard boundaries | ADR, README | Low |
| Architecture | Conceptual system design | Architecture docs | Low |
| Domain Concepts | Shared vocabulary | Documentation | Low |
| Roadmap | Planned direction | ROADMAP | Medium |
| Project State | Current snapshot | CHANGELOG, Git | High |
| Code Navigation | Entry points & orientation | Auto-generated | Medium |
| Non Goals | Explicit exclusions | Documentation | Very Low |

Each category has different regeneration rules.

Stable knowledge should remain stable.

Rapidly changing knowledge should update independently.

This separation minimizes unnecessary context churn.

---

# 10. Knowledge Lifecycle

Every piece of knowledge moves through four stages.

```
Repository

↓

Extract

↓

Normalize

↓

Preserve

↓

Evolve
```

Unlike traditional documentation generators, Contextix does not recreate knowledge every run.

It preserves existing knowledge whenever possible.

Only changed knowledge is regenerated.

---

# 11. Project Memory

Contextix treats generated context as persistent project memory.

Project memory has three properties.

## Identity

Knowledge keeps a stable identity across generations.

Example

Decision

```
DEC-003
```

should remain

```
DEC-003
```

even if its wording changes.

Identity is more important than wording.

---

## Stability

If nothing meaningful changes,

Context should remain identical.

Two executions against the same repository should produce identical output.

---

## Evolution

Knowledge should evolve incrementally.

Adding one ADR should not rewrite the entire project memory.

Understanding grows.

It should not restart.

---

# 12. Pipeline

```
Repository

↓

Parser

↓

Analyzer

↓

Linker

↓

Validator

↓

Builder

↓

Evolution Engine

↓

Exporter
```

Each stage has a single responsibility.

---

# Stage 1 — Parser

Responsibility

Read project files.

Classify documents.

Apply ignore rules.

Produce ParsedDocument objects.

Supported initially

- Markdown
- Text
- YAML
- JSON
- TOML
- reStructuredText

Future support

- PDF (plugin)
- DOCX (plugin)
- Notion export (plugin)

The Parser never performs semantic analysis.

It only prepares structured documents.

---

# Stage 2 — Analyzer

Responsibility

Extract structured knowledge from documentation.

The Analyzer converts documents into normalized knowledge objects.

Examples

Goal

Decision

Constraint

Architecture

Roadmap

Domain Concept

Every extracted object includes

- content
- source
- confidence
- extraction method

The Analyzer operates on Markdown ASTs instead of regex whenever possible.

This dramatically reduces extraction errors.

---

# Stage 3 — Linker

Responsibility

Build relationships between extracted knowledge.

Examples

README references ADR.

ADR references MANIFESTO.

ROADMAP depends on Decision.

Architecture references Domain Concept.

The Linker creates a lightweight knowledge graph.

The graph is used only for navigation and validation.

It is intentionally not a full knowledge graph database.

---

# Stage 4 — Validator

Responsibility

Detect quality issues.

Examples

Missing rationale.

Broken links.

Conflicting goals.

Duplicate decisions.

Stale roadmap items.

Validation never blocks generation.

Issues become metadata for AI assistants.

Warnings are preferable to silent failures.

---

# Stage 5 — Builder

Responsibility

Assemble project memory.

The Builder performs

- merge
- deduplication
- prioritization
- summarization
- source attribution
- token budgeting

Every entry competes for inclusion.

Knowledge that provides little value relative to its token cost is discarded.

The Builder produces a coherent representation of project understanding.

Not a repository inventory.

---

# Stage 6 — Evolution Engine

This is the defining stage of Contextix.

The Evolution Engine compares newly generated knowledge against previous project memory.

Instead of rebuilding everything,

it identifies what actually changed.

Responsibilities

• preserve stable identities

• reuse unchanged knowledge

• classify modifications

• generate incremental updates

• minimize token growth

• preserve context continuity

Without this stage,

Contextix becomes another repository summarizer.

With it,

Contextix becomes a persistent memory system.

---

# Stage 7 — Exporter

Responsibility

Generate portable outputs.

Default outputs

```
.context/

context.yaml

metadata.json

summary.md

architecture.md

handoff.md
```

Future exporters

- MCP Memory
- JSON API
- Markdown Bundle
- LLM Prompt Package
- IDE Companion
- Agent Memory Package

The Exporter never changes knowledge.

It only changes representation.