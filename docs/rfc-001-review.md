# RFC-001 Review: The Portability Gap

**Reviewer:** Lead Architect
**Date:** 2026-07-02
**Status:** Critical Review

---

## 0. The Real Problem

RFC-001 was written under the assumption that Contextix's job is to "extract
understanding from documentation." That's wrong.

The real problem Contextix solves:

> When a developer switches AI assistants (ChatGPT, Claude, Codex, Cursor, Gemini)
> or starts a new conversation, they should not need to re-explain the entire project.

This reframes everything. The product is not an extraction pipeline. The product is
a **context portability layer**. The output is not documentation. The output is the
answer to: "What would you tell a new teammate on their first day?"

Every architectural decision must now pass a single test:

> **Does this reduce the amount of context a developer needs to re-explain when
> switching AI sessions?**

If the answer is no, the feature does not belong in the core.

---

## 1. Does RFC-001 Truly Solve the Real Problem?

**No.** RFC-001 designs an excellent extraction pipeline. It solves the "how to parse
markdown and extract structured knowledge" problem thoroughly. But extraction is
necessary, not sufficient.

What RFC-001 does NOT solve:

### 1.1 No Session Bootstrap

A developer switches from Claude to Codex. The new AI session reads `.context/`.
What does it read first? `context.yaml`? `handoff.md`? `summary.md`? All three?

The AI has a limited context window. It needs to understand the project in the first
500 tokens. RFC-001 has no concept of a "bootstrap" — the minimum viable context for
a new session. The AI gets everything, and everything is treated as equally important.

### 1.2 No Context Evolution

A developer runs Contextix on Monday. The project has 3 ADRs and 5 goals. On Friday,
they add a new ADR and complete a goal. They run Contextix again.

What does the AI see? A completely regenerated `context.yaml`. It has no way to know
what changed. It must re-read the entire file and compare mentally with what it knew
before — except it has no memory of "before" because this is a new session.

RFC-001 has no concept of context diff, change tracking, or evolution metadata.

### 1.3 No Stability Guarantees

A developer runs Contextix twice on the same project state. The output should be
identical. RFC-001 doesn't guarantee this. The pipeline regenerates everything from
scratch. Document ordering, deduplication order, section ordering — all are
implementation details that could drift between runs.

Without stability guarantees, the AI cannot trust that "unchanged context" means
"unchanged project." The developer cannot trust that running Contextix again won't
produce a different context for the same project.

### 1.4 No Token Budget Management

RFC-001 mentions that the Builder "manages token budget" but doesn't design it. How
many tokens should the output target? 500? 2000? 10000? What happens when the project
has 50 ADRs? Does the context grow linearly? Does it cap?

Without a token budget, Contextix has the same problem as reading all the documentation
directly: the AI gets overwhelmed.

### 1.5 No Context Tiers

Not all knowledge is equally important for a new session. A decision about the storage
backend is critical. A roadmap item for Q4 2027 is not. A domain concept definition is
important. A non-goal is contextual.

RFC-001 treats all knowledge categories as flat lists. There's no tiering, no
prioritization for the AI's consumption order.

---

## 2. Which Parts Directly Contribute to Portable Project Context?

### Strong Contributions

| Component | Why It Helps |
|-----------|-------------|
| **Filesystem-first output** | `.context/` is a directory. It can be committed, copied, shared. The unit of portability is clear. |
| **Structured decisions with rationale** | The WHY survives session switches. "We chose Redis because X" is portable. "We chose Redis" is not. |
| **Domain concepts** | Terminology defined once. The AI doesn't misinterpret "Entity" across 5 different documents. |
| **Source attribution** | Every claim links to its source. A developer can verify correctness. The AI can trace claims to origin documents. |
| **Code navigation hints** | 5 lines telling the AI where to start. Beats reading the entire directory tree. |

### Weak or No Contribution

| Component | Why It Doesn't Help |
|-----------|-------------------|
| **Linker stage** | Cross-document references build a graph, but the AI can follow links itself. The graph is developer-facing, not AI-facing. |
| **Validator stage** | Contradiction detection is useful for the developer, not for the AI. The AI doesn't need to know that README and ADR disagree — it needs to know what the project IS. |
| **Plugin interface** | Not product-facing. Premature design without a single plugin to validate it. |
| **11 knowledge categories** | Several categories (Project State, References, Issues) are meta-information. They don't help the AI understand the project. They're implementation artifacts. |

---

## 3. Which Parts Only Improve Implementation Quality?

These are good engineering but don't move the product needle:

1. **The specific markdown parser choice** (mistune) — Important for correctness, but the user doesn't care which parser is used. They care that the output is correct.

2. **The Context IR schema** with 9 structured types — Clean design, but the AI doesn't consume Python dataclasses. It consumes YAML. The IR is an implementation detail.

3. **The plugin system design** — No plugins exist yet. Designing the interface before the first plugin is premature generalization.

4. **The Linker and Validator as separate stages** — They could be part of the Analyzer. Separate stages add pipeline complexity without proportional product value.

5. **ADR recommendations** — Useful for the development team, not for the product.

---

## 4. Which Sections Are Over-Engineered?

### 4.1 The Pipeline Has Too Many Stages

```
Parser → Analyzer → Linker → Validator → Builder → Exporter
```

Six stages. For a tool whose core value proposition is "preserve project understanding."

The Linker resolves cross-document references. The AI can follow `[text](path)` links
itself. This is a developer tooling feature, not a context portability feature.

The Validator detects contradictions. This is useful for the developer maintaining
documentation, not for the AI starting a new session. The AI needs to know what the
project IS, not what disagreements exist in the docs.

**Recommendation:** Merge Linker into Analyzer (it's an analysis concern). Remove
Validator from the core pipeline (make it a CLI subcommand: `contextix validate`).

### 4.2 The Context IR Has Too Many Types

```
Goal, Decision, Architecture, DomainConcept, RoadmapItem,
CodeNavigation, ProjectState, DocumentReference, ValidationIssue
```

Nine structured types. Each one adds a class, a constructor, serialization logic,
and documentation. For a project that should be simple enough for one person to
maintain, this is heavy.

**Recommendation:** Keep only the types that the AI consumer actually needs:
- `Decision` (structured, because rationale pairing is the core value)
- `DomainConcept` (structured, because term+definition is a natural pair)
- Everything else: flat lists with source attribution inline

### 4.3 The Plugin Interface Is Premature

Three hooks, a protocol class, pip extras, configuration schema — all designed before
a single plugin exists to validate the interface.

**Recommendation:** Remove the plugin system from RFC-001. Ship the core pipeline
first. When the first plugin is needed (AST, LLM, Git), design the interface against
a real use case, not speculation.

---

## 5. Which Sections Are Under-Designed?

### 5.1 Context Evolution (MISSING ENTIRELY)

This is the biggest gap. RFC-001 designs a one-shot extraction pipeline. It has no
concept of:

- **Context identity:** How does Contextix know this is the "same" project as last time?
- **Context diff:** What changed between runs?
- **Change classification:** Is this a new decision, a modified goal, or a typo fix?
- **Staleness:** Did a roadmap item pass its target date? Does a reference point to a deleted file?
- **Incremental rebuild:** Can we re-analyze only changed documents, not the entire project?

Without context evolution, the developer's experience is:

1. Run Contextix on Monday → AI reads context
2. Project changes during the week
3. Run Contextix on Friday → AI must re-read the ENTIRE context to find what changed

This is barely better than not having Contextix at all.

### 5.2 Session Bootstrap (MISSING ENTIRELY)

The most important output of Contextix is the first 500 tokens the AI reads. RFC-001
has no design for this. The `handoff.md` and `summary.md` files exist but are
afterthoughts — they're generated from the same data as `context.yaml`, just formatted
differently.

What should the bootstrap contain?

```
# Project: Contextix
# Purpose: Preserve project understanding across AI sessions
# Key Decisions:
#   - Filesystem storage (keeps tool zero-dependency)
#   - Markdown-first documentation (human-readable, git-friendly)
# Constraints: Must not require API key. Must work offline.
# Where to start: src/pipeline/engine.py, docs/adr/
```

50-100 tokens. The AI reads this and knows enough to ask intelligent questions or
start working. Everything else is reference material.

### 5.3 Stability Contract (MISSING ENTIRELY)

RFC-001 doesn't state what guarantees Contextix makes about output stability. Without
this, the AI cannot trust the context.

Required guarantees:

1. **Same input → same output.** Running Contextix twice on identical project state produces identical output.
2. **Document ordering is deterministic.** Alphabetical by path. No random iteration order.
3. **Deduplication is deterministic.** Same algorithm, same order, every time.
4. **Section ordering is deterministic.** Defined by the schema, not by discovery order.

### 5.4 Context Tiers (MISSING ENTIRELY)

Not all knowledge is equally important. RFC-001 has no concept of tiers.

| Tier | Size | Content | When to Read |
|------|------|---------|-------------|
| **Critical** | ~500 tokens | Purpose, key decisions, constraints, entry points | Every new session, immediately |
| **Important** | ~2000 tokens | All decisions, architecture, domain concepts, roadmap | When the AI needs deeper context |
| **Reference** | Unlimited | Full architecture text, document index, validation issues | When the AI is working on a specific area |

### 5.5 Human-in-the-Loop (MISSING ENTIRELY)

The context is machine-generated. It will contain mistakes. How does a developer
correct them?

Options:
- **Override file:** `.context/overrides.yaml` — hand-written corrections merged into the generated output
- **Annotation markers:** `<!-- contextix: goal="Preserve understanding" -->` in source documents
- **Review workflow:** `contextix review` — shows what was extracted, developer accepts/rejects each item

RFC-001 has none of these. The developer's only option is to edit the generated
`.context/` files, which will be overwritten on the next run.

---

## 6. Missing Architectural Capabilities

### 6.1 Context Diff

```
$ contextix diff
  + New decision: "Use mistune for markdown parsing" (docs/adr/0002-parser.md)
  ~ Modified goal: "Preserve project understanding" → "Preserve understanding across AI sessions"
  - Removed roadmap item: "Add PDF parser" (completed)
  ! Stale reference: docs/adr/0001-storage.md references "docs/old-arch.md" (file not found)
```

The diff IS the context update. It's what the AI reads to know what changed since its
last session. It's more important than the full context for returning sessions.

### 6.2 Context Decay Model

Different knowledge decays at different rates:

| Knowledge Type | Decay Rate | Action When Stale |
|---------------|-----------|-------------------|
| Vision | Years | — |
| Architecture decisions | Months | Flag for review |
| Goals | Months | Flag for review |
| Roadmap items | Weeks | Flag as overdue |
| Project state | Days | Regenerate every run |
| Code navigation | Medium | Regenerate on structural changes |

The context should encode decay information so the AI knows which claims are fresh
and which might be outdated.

### 6.3 Incremental Rebuild

Regenerating the entire context from scratch on every run is wasteful and destabilizing.
A document that hasn't changed should produce the same extracted knowledge as last time.

Required:
- Document fingerprinting (hash of content)
- Cache of extracted knowledge per document
- Only re-analyze documents whose fingerprint changed
- Merge cached results with new results

This is the only way to achieve output stability for unchanged documents.

### 6.4 Context Identity

How does Contextix know this is the "same" project? If a developer clones the repo
to a new machine and runs Contextix, should the output be identical?

Required:
- Project identity derived from content, not path
- Hash of all analyzed documents
- Version marker in the output

---

## 7. Revised Product Vision

### Before (RFC-001)

> Contextix preserves WHY decisions were made, WHAT constraints exist, WHERE the
> project is going, HOW the system is structured conceptually.

### After

> **Contextix is a context portability layer for AI-assisted development.**
>
> It generates a compact, stable, filesystem-based project memory that travels with
> the code. When a developer starts a new AI conversation — regardless of which
> assistant or tool they use — Contextix answers the question:
>
> *"What would you tell a new teammate on their first day?"*
>
> The memory captures purpose, key decisions, constraints, domain language, and
> navigation hints. It evolves visibly as the project changes. It is deterministic,
> verifiable, and fits in 500 tokens.

---

## 8. Revised Guiding Principles

| # | Principle | What It Means |
|---|-----------|---------------|
| 1 | **Portable First** | The `.context/` directory is the unit of portability. It lives in the repo. It can be committed, copied, or shared. |
| 2 | **Stable Across Runs** | Same project state → same output. Determinism is a contract, not a preference. The AI trusts that unchanged context means unchanged project. |
| 3 | **Bootstrap in 500 Tokens** | A new AI session understands the project's purpose, key decisions, constraints, and entry points in the first 500 tokens. Everything else is reference material. |
| 4 | **Human-Verifiable** | Every machine-extracted claim includes its source. A developer can trace any statement to the document it came from in under 30 seconds. |
| 5 | **Evolves Visibly** | When the project changes, the context change is visible and understandable. The diff IS the context update. The AI reads the diff, not the full context. |
| 6 | **Documentation First** | Extract from human-authored documents. Code is the AI assistant's job. Contextix stores what code cannot express. |
| 7 | **Simplicity Over Completeness** | Missing a domain concept is better than including a wrong one. Prefer under-extraction over over-extraction. 500 correct tokens beat 5000 noisy tokens. |
| 8 | **LLM Optional** | The core pipeline is deterministic. LLM enhancement is opt-in, not required. The bootstrap context works without an LLM ever touching it. |

---

## 9. Revised Core Product Goals

| # | Goal | Success Metric |
|---|------|---------------|
| 1 | **Session Bootstrap** | A new AI session reads 500 tokens and correctly states the project's purpose, 2-3 key decisions, and where to find the code. |
| 2 | **Decision Memory** | Structured decisions with rationale. The AI can answer "why was X chosen?" without reading the source ADR. |
| 3 | **Domain Language** | Project-specific terminology defined once. The AI uses terms correctly across the entire conversation. |
| 4 | **Navigation Map** | The AI knows where to start reading code. Entry points, key directories, naming conventions. 5-10 lines. |
| 5 | **Context Evolution** | The AI reads the diff from the previous run. It knows what's new, what changed, and what was removed — without re-reading the entire context. |
| 6 | **Source Traceability** | Every claim in the context links to its source document. A developer can verify any claim in 30 seconds. |

### What Was Removed

- **Architecture extraction** as a separate goal — merged into Navigation Map. The AI doesn't need a prose architecture description. It needs to know where the architecture is documented.
- **Roadmap extraction** as a separate goal — merged into Context Evolution. Roadmap items are relevant when they change, not as a static list.
- **Constraint extraction** as a separate goal — merged into Session Bootstrap. Constraints are guardrails that belong in the first 500 tokens.
- **Plugin system** as a product goal — removed entirely. It's an implementation detail, not a product capability.

---

## 10. RFC-002 Outline: Stable Context Evolution

### RFC-002: Stable Context Evolution

**Purpose:** Define how Contextix's output evolves across runs — the contracts,
guarantees, and mechanisms that make project context trustworthy across AI sessions.

**Sections:**

#### 1. Context Identity
How does Contextix know this is the "same" project? Project hash derived from document
content, not filesystem path. Identity survives repo cloning, renaming, and relocation.

#### 2. Deterministic Output Contract
What guarantees does Contextix make about output stability? Same input → same output.
Document ordering, section ordering, deduplication strategy — all specified and tested.
No randomness. No dependency on filesystem iteration order.

#### 3. Context Diff
What changed between runs? The diff is a first-class output. It shows new, modified,
and removed knowledge. The AI reads the diff for returning sessions, the full context
for new sessions.

#### 4. Change Classification
Not all changes are equal. A new ADR is a "significant change." A typo fix is a
"minor change." A roadmap item being completed is a "state transition." The AI
should know the magnitude of each change.

#### 5. Staleness Detection
When does context become stale? Roadmap items past their target date. References to
deleted files. Decisions that contradict newer documents. Staleness is a warning,
not an error. The AI is informed, not blocked.

#### 6. Context Tiers
Critical (~500 tokens), Important (~2000 tokens), Reference (unlimited). The Builder
assigns tiers based on knowledge type. The AI reads tiers in order. The export format
supports tiered consumption.

#### 7. Incremental Rebuild
Document fingerprinting. Cache of extracted knowledge per document. Only re-analyze
changed documents. Merge cached results with new results. This is the mechanism that
makes output stability possible.

#### 8. Context Decay Model
Different knowledge types decay at different rates. Vision decays in years. Architecture
decisions in months. Roadmap items in weeks. The context encodes decay information so
the AI knows which claims are fresh.

#### 9. Evolution Metadata
Each context generation includes: when it was generated, what project version it
represents, which documents were analyzed, document fingerprints, and a diff from
the previous generation.

#### 10. Human-in-the-Loop
The context is machine-generated but human-curated. Override files for corrections.
Annotation markers in source documents. A review workflow for accepting/rejecting
extracted claims. The developer owns the context; Contextix suggests it.

---

## Summary

RFC-001 is a good extraction pipeline. It solves the "how to parse markdown and extract
structured knowledge" problem. But it does not solve the "preserve context across AI
sessions" problem.

The gap is not in extraction quality. It's in the absence of:

1. **Context Evolution** — the diff, not the full context, is the update
2. **Session Bootstrap** — 500 tokens that answer "what is this project?"
3. **Stability Contract** — same input → same output, guaranteed
4. **Context Tiers** — critical vs. important vs. reference
5. **Human-in-the-Loop** — the developer corrects mistakes

RFC-002 should address these gaps before any implementation of RFC-001 begins. The
extraction pipeline is the engine. Context evolution is the steering wheel. Without
both, the car doesn't go where you want.