# System Architecture

Version: 2.0 (RFC-001)

---

## Pipeline

```
Repository
    │
    ▼
┌─────────┐
│ Parser  │  Walk repo, read files, classify by type, apply .contextignore
└────┬────┘
     │  ParsedDocument[]
     ▼
┌──────────────┐
│  Analyzer    │  Extract goals, decisions, constraints, architecture,
│              │  domain concepts, roadmap, project state
└──────┬───────┘
       │  ContextIR
       ▼
┌──────────┐
│  Linker  │  Build cross-document reference graph from markdown links
└────┬─────┘  and natural-language references
     │  ContextIR (with references)
     ▼
┌─────────────┐
│  Validator  │  Detect: missing rationale, broken links, stale roadmap,
└──────┬──────┘  duplicate goals. Warnings only — never blocks pipeline.
       │  ContextIR (with validation_issues)
       ▼
┌──────────┐
│  Builder │  Merge, deduplicate, prioritize, summarize, apply token budget
└────┬─────┘
     │  ProjectMemory
     ▼
┌──────────────┐
│  Exporter    │  Write .context/ files
└──────┬───────┘
       │
       ▼
   .context/
```

---

## Knowledge Model

| Category | Type | Source | Example |
|----------|------|--------|---------|
| Identity | Fact | README, pyproject.toml | Project name, description, version |
| Vision | Intent | MANIFESTO, README | Long-term purpose |
| Goals | Intent | PRD, README | "Preserve project understanding across AI sessions" |
| Decisions | Intent + Rationale | ADR | `{what, why, alternatives, source}` |
| Constraints | Boundary | ADR, README | "Must not require an API key" |
| Architecture | Structure | docs/architecture.md | Conceptual design, named patterns |
| Domain Concepts | Vocabulary | All docs | `{term, definition, source}` |
| Roadmap | Direction | ROADMAP.md | Planned milestones with timelines |
| Project State | Status | pyproject.toml, CHANGELOG | Version, recent changes |
| Non-Goals | Boundary | README, docs/ | Explicit exclusions |

---

## Structured Types

### Decision

```yaml
- what: "Use filesystem storage for project memory"
  why: "Keeps the tool zero-dependency and avoids requiring a database server"
  alternatives:
    - "SQLite (rejected: adds binary dependency)"
    - "Cloud storage (rejected: violates local-first principle)"
  source: "docs/adr/0001-storage.md"
```

### DomainConcept

```yaml
- term: "Memory"
  definition: "A snapshot of project understanding at a point in time"
  source: "MANIFESTO.md"
```

### ProjectState

```yaml
version: "0.1.0"
recent_changes: []
known_issues: []
```

---

## Output Files

```
.context/
├── bootstrap.md      # Session bootstrap (~500 tokens): purpose, key decisions, constraints, navigation
├── summary.md        # Full overview: all categories
├── architecture.md   # Full architecture text
├── handoff.md        # AI reading instructions with validation issues
├── context.yaml      # Structured data (all fields)
├── snapshot.json     # Project state snapshot
└── metadata.json     # Generation metadata (version, hash, checksum)
```

---

## Design Principles

- **Deterministic** — Same input → same output. Every run.
- **Documentation First** — Extract from human-authored documents, not source code.
- **Portable** — `.context/` travels with the repository.
- **LLM Optional** — Core pipeline is deterministic; LLM enhancement is opt-in.
- **Stable** — Small changes produce small context diffs.
- **Warnings, Not Errors** — Validation never blocks the pipeline.

---

## Dependencies

- **mistune** — Markdown AST parser (pure Python, no C compilation)
- **PyYAML** — YAML serialization
- **loguru** — Structured logging
- **pytest** — Testing

All dependencies are pure Python. No C compilation required.
