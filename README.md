# Contextix

> Preserve project understanding. Ship it with your code.

![Version](https://img.shields.io/badge/version-0.1.0-blue)

Contextix is a **context portability layer** for AI-assisted development. It generates a compact, deterministic, filesystem-based project memory that travels with your code across AI assistants, tools, and conversations.

When you switch from ChatGPT to Claude, or start a new session, Contextix answers the question: *"What would you tell a new teammate on their first day?"*

```
Repository
    │
    ▼
 Contextix
    │
    ▼
 .context/
    │
    ▼
ChatGPT   Claude   Gemini   Cursor   Codex
```

---

## The Problem

Every AI conversation starts from zero. You re-explain the project. The architecture. The constraints. The decisions. The terminology.

Contextix preserves that understanding once, then ships it with your repository.

---

## Without Contextix vs With Contextix

```
Without Contextix                    With Contextix

Developer                            Developer
    │                                    │
    ▼                                    ▼
Explain the project                  Attach bootstrap.md
    │                                    │
    ▼                                    ▼
Explain the architecture             Coding
    │
    ▼
Explain the decisions
    │
    ▼
Explain the constraints
    │
    ▼
Coding
```

---

## Quick Start

```bash
pip install contextix

# Initialize in your project
contextix init

# Generate project memory
contextix generate
```

### Use with AI

After generating `.context/`, attach `bootstrap.md` or `handoff.md` when starting a new AI conversation.

```
ChatGPT / Claude / Gemini
        ↓
Attach bootstrap.md
        ↓
Continue development
```

Output:

```
.context/
├── bootstrap.md      # Session bootstrap (~500 tokens)
├── summary.md        # Full overview
├── architecture.md   # System design
├── handoff.md        # AI reading instructions
├── context.yaml      # Structured project data
├── snapshot.json     # Project state snapshot
└── metadata.json     # Generation metadata
```

---

## Example Output

```yaml
# context.yaml

project:
  name: Contextix
  description: Context portability layer for AI-assisted development

decisions:
  - what: Use filesystem storage for project memory
    why: Keeps the tool zero-dependency and avoids requiring a database
    alternatives:
      - SQLite (rejected: adds binary dependency)
      - Cloud storage (rejected: violates local-first)
    source: docs/adr/0001-storage.md

constraints:
  - Must not require an API key
  - Must work offline
  - Must stay under 50MB

goals:
  - Preserve project understanding across AI sessions
  - Reduce repeated explanations
  - Enable seamless AI handoff
```

---

## Why Not Just Use README?

| README | Contextix |
|--------|-----------|
| Explains | Compresses |
| Written for humans | Optimized for AI |
| Evolves slowly | Regenerated every run |
| One document | Structured knowledge graph |
| Prose | Machine-readable YAML |
| Manual updates | Automatic extraction |

A README tells a story. Contextix builds a knowledge base.

---

## Pipeline

```
Repository
    │
    ▼
  Parser      Read files, classify by type
    │
    ▼
  Analyzer    Extract goals, decisions, constraints, architecture, domain concepts
    │
    ▼
  Linker      Build cross-document reference graph
    │
    ▼
  Validator   Detect missing rationale, broken links, stale roadmap items
    │
    ▼
  Builder     Merge, deduplicate, prioritize, summarize, apply token budget
    │
    ▼
  Exporter    Write .context/ files
    │
    ▼
  .context/
```

Each stage is deterministic. Same input → same output. Every run.

---

## What Contextix Preserves

| Category | Example |
|----------|---------|
| **Decisions** | What was chosen, why, alternatives considered |
| **Constraints** | Hard boundaries: "Must not require an API key" |
| **Goals** | What the project aims to achieve |
| **Architecture** | Conceptual system design, patterns |
| **Domain Concepts** | Project-specific terminology |
| **Roadmap** | Planned future work with timelines |
| **Code Navigation** | Entry points, key directories |
| **Cross-References** | Which documents reference which |

---

## What Contextix Is NOT

- A code search engine
- A repository compressor
- An IDE replacement
- A documentation generator
- An AST indexing system

Contextix preserves **human understanding** — the WHY behind decisions, not the WHAT of code structure. AI assistants can read code. They cannot read minds.

---

## Philosophy

> If an AI assistant can discover it by reading source code, Contextix should not store it. Contextix stores what source code cannot express.

- **Documentation First** — Extract from human-authored documents
- **Deterministic** — Same input → same output, guaranteed
- **Portable** — `.context/` travels with the repository
- **LLM Optional** — Core pipeline is deterministic; LLM enhancement is opt-in
- **Stable** — Small changes produce small context diffs

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System architecture and pipeline design |
| [RFC-001](docs/rfc-001-architecture-v2.md) | Architecture v2 specification |
| [RFC-001 Review](docs/rfc-001-review.md) | Critical architecture review |
| [Roadmap](docs/roadmap.md) | Development stages and future features |
| [Contributing](docs/contributing.md) | How to contribute |
| [Manifesto](MANIFESTO.md) | Project vision and principles |

---

## License

MIT License
