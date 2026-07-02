# Product Requirements & Technical Design

Version: 1.0 Draft

---

# Product Overview

Contextix is a CLI-based developer infrastructure tool that builds an AI-readable memory layer for software projects.

Instead of forcing AI to repeatedly reconstruct project understanding from raw repositories, Contextix extracts, structures, compresses, and preserves project understanding into portable memory artifacts.

---

# Problem Statement

Modern AI-assisted development suffers from recurring problems:

## Context Window Limitations

Large projects exceed LLM context windows. Developers repeatedly remove information or split conversations.

## Cross-LLM Handoff

Switching AI models requires rebuilding context manually, resulting in repeated explanations, inconsistent outputs, and architecture drift.

## Missing Understanding

Repositories describe implementation but rarely describe project goals, architectural reasoning, constraints, or priorities. AI must infer these repeatedly.

## Context Fragmentation

Knowledge is scattered across README, documentation, source code, issues, meeting notes, and PDFs.

---

# Product Goals

- Preserve project understanding
- Reduce repeated explanations
- Enable seamless AI handoff
- Reduce unnecessary token usage (target: 60-85% reduction)
- Generate deterministic project memory
- Build an open project memory standard (CES)

---

# Target Users

**Primary:** AI Engineers, Software Engineers, Indie Hackers, Solo Developers, Startup Teams

**Secondary:** Open Source Maintainers, Technical Writers, Research Engineers

---

# MVP Scope

CLI only. No IDE integrations, cloud services, or web dashboard.

---

# Functional Requirements

## Repository Parsing

- Analyze repository structure
- Detect programming languages
- Identify important files
- Collect repository metadata

## Document Parsing

**MVP:** Markdown, Plain Text, PDF

**Future:** DOCX, Notion Export, HTML, Confluence

## Project Understanding

The engine identifies: project goal, vision, architecture, tech stack, constraints, decisions, development state, next tasks, known issues.

## Context Compression

- Remove redundant information
- Preserve intent, architecture, constraints
- Target: 60-85% token reduction

## Output Generation

Generate `.context/` directory containing:

```
.context/
├── context.yaml      # Primary structured project memory
├── summary.md        # Human-readable overview
├── architecture.md   # Architecture explanation
├── handoff.md        # Prompt optimized for AI transition
├── snapshot.json     # Current project state
└── metadata.json     # Generation metadata
```

---

# Technical Design

## Design Philosophy

Contextix behaves like a compiler. Instead of compiling source code into machine code, it compiles project information into AI-readable project memory.

Every processing stage is independent, deterministic, and replaceable.

## Pipeline Architecture

```
Project Input
      │
      ▼
Parser Layer
      │
      ▼
Analyzer Layer
      │
      ▼
Context IR
      │
      ▼
Memory Builder
      │
      ▼
Memory Optimizer
      │
      ▼
Exporter
      │
      ▼
.context/
```

### Stage 1: Parser Layer

Converts raw project artifacts into normalized documents.

**Output:** `ParsedDocument[]` containing source, content, metadata, language, file_type.

Performs no reasoning. Only extraction.

### Stage 2: Analyzer Layer

Understands project information through: language detection, repository structure analysis, dependency analysis, architecture detection, semantic chunking, project classification.

**Output:** `AnalysisResult`

### Stage 3: Context IR (Core)

The heart of Contextix. All downstream modules operate on Context IR.

```
Project
├── Architecture
├── Goals
├── Constraints
├── Tasks
├── Tech Stack
├── Known Issues
├── Decisions
├── Features
└── History
```

Provider-independent. Never depends on YAML, Markdown, JSON, or LLM provider.

### Stage 4: Memory Builder

Converts Context IR into structured project memory through hierarchy construction, relationship mapping, state reconstruction, decision extraction.

**Output:** `ProjectMemory`

### Stage 5: Memory Optimizer

Improves memory quality through redundancy removal, semantic deduplication, hierarchy optimization, context compression.

**Important:** Optimizer must preserve understanding. Compression is secondary.

### Stage 6: Export Layer

Generates output artifacts: context.yaml, summary.md, architecture.md, handoff.md, snapshot.json, metadata.json.

---

# CLI Experience

```bash
$ contextix

Analyzing project...
Building project memory...
Compressing context...
Generating outputs...
Done.

Generated:
.context/
```

## Commands

- `contextix` - Generate project memory
- `contextix update` - Incrementally update project memory
- `contextix snapshot` - Generate development snapshot
- `contextix export [format]` - Export memory (markdown, yaml, json)
- `contextix validate` - Validate CES compliance
- `contextix doctor` - Analyze memory quality
- `contextix diff` - Compare snapshots
- `contextix clean` - Remove generated artifacts

---

# Non-Functional Requirements

- **Fast:** Generate memory within reasonable time
- **Deterministic:** Repeated runs produce similar outputs
- **Modular:** Each stage independently replaceable
- **Provider Agnostic:** Support multiple LLM providers
- **Local First:** Core features work offline
- **Extensible:** Easy to add parsers and exporters

---

# Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12+ |
| CLI | Typer |
| Configuration | YAML |
| Schema Validation | Pydantic |
| Repository Parsing | GitPython, Pathlib, Tree-sitter |
| Document Parsing | PyMuPDF, Markdown-it, Unstructured |
| LLM Abstraction | LiteLLM |
| Embedding | sentence-transformers, BGE-M3 |
| Vector Storage (Future) | FAISS, SQLite-VSS |
| Database (Future) | SQLite, PostgreSQL |
| Logging | Loguru |
| Testing | pytest |
| Packaging | uv |
| Formatting | Ruff, Black |

---

# Performance Goals

- **Small Projects (<100 files):** <5 seconds
- **Medium Projects (<2,000 files):** <20 seconds
- **Large Projects (>10,000 files):** Incremental mode recommended

---

# Success Metrics

MVP is successful if developers can:

1. Generate project memory using one command
2. Switch AI models without rebuilding context
3. Reduce prompt size significantly
4. Preserve project understanding
5. Reuse memory across multiple sessions

---

# Out of Scope (MVP)

Web Dashboard, VS Code Extension, Cursor Extension, Cloud Sync, Fine-Tuned Models, Autonomous Coding Agent, Multi-Agent Collaboration, Database Server, Project Management Features.

---

# Risks

- Incorrect project understanding
- Over-compression
- Hallucinated memory
- Poor parser performance
- Large repository scalability

---

# Incremental Memory (Future)

```
Previous Memory * Repository Changes
      │
      ▼
Analyzer
      │
      ▼
Updated Context IR
      │
      ▼
Updated Memory
      │
      ▼
Export
```

Avoids rebuilding everything. Significantly reduces execution time.

---

# Error Handling

Pipeline stages fail independently:

```
PDF Parser Failed
      │
      ▼
Skip PDF
      │
      ▼
Continue Repository Parsing
      │
      ▼
Generate Partial Memory
      │
      ▼
Warn User
```

System degrades gracefully.
