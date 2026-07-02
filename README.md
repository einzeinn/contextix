# Contextix

> Preserve Project Understanding.

Contextix is an AI-first Project Memory Engine that compresses, structures, and preserves software understanding for both developers and AI systems.

Instead of repeatedly explaining your project to every AI conversation, Contextix generates portable project memory.

---

## The Problem

Modern AI development suffers from one recurring problem: **Large contexts.**

- Repeated explanations
- Lost architectural decisions
- AI hallucinations after context resets
- Project understanding slowly disappears

Contextix solves this by generating structured, AI-optimized Project Memory.

---

## Features

- Repository Analysis
- PDF & Markdown Parsing
- Context Compression (60-85% token reduction)
- Context IR (Intermediate Representation)
- Context Exchange Specification (CES)
- AI-ready Project Memory
- Cross-LLM Handoff
- Development Snapshots
- Structured Outputs

---

## Quick Start

```bash
# Initialize Contextix
contextix init

# Generate project memory
contextix
```

Output:

```
.context/
├── context.yaml      # Primary structured project memory
├── snapshot.json     # Current project state
├── metadata.json     # Generation metadata
├── summary.md        # Human-readable overview
├── architecture.md   # Architecture explanation
└── handoff.md        # Prompt optimized for AI transition
```

---

## Philosophy

Source Code answers: **"What exists?"**

Contextix answers: **"Why does it exist?"**

Together they preserve software understanding.

---

## How It Works

```
Project Input
      │
      ▼
Parser Layer (Repository, Markdown, PDF)
      │
      ▼
Analyzer Layer (Structure, Dependencies, Architecture)
      │
      ▼
Context IR (Internal Representation)
      │
      ▼
Memory Builder + Optimizer
      │
      ▼
Exporter → .context/
```

Each stage is independent, deterministic, and replaceable.

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | Product requirements and technical design |
| [Architecture](docs/architecture.md) | System architecture and code structure |
| [Specification](docs/specification.md) | CES format and CLI specification |
| [Roadmap](docs/roadmap.md) | Development stages and future features |
| [Contributing](docs/contributing.md) | How to contribute and glossary |
| [Manifesto](MANIFESTO.md) | Project soul and identity |

---

## Roadmap

```
Research & Documentation (Complete)
        │
        ▼
      MVP (In Progress)
        │
        ▼
      Alpha
        │
        ▼
      Beta
        │
        ▼
      v1.0
        │
        ▼
    Ecosystem
```

---

## Long-Term Vision

Contextix aims to become the knowledge layer between software projects and AI systems.

Just as Git standardizes source code versioning and OpenAPI standardizes API contracts, Contextix aims to standardize project understanding.

---

## Contributing

We welcome contributors interested in:

- Developer Tools
- AI Engineering
- Software Architecture
- Research
- Documentation

See [Contributing Guide](docs/contributing.md) for details.

---

## License

MIT License
