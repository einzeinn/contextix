# System Architecture

Version: 1.0 Draft

---

# Architecture Goals

The architecture satisfies these principles:

- **Modular** - Each component has one responsibility
- **Deterministic** - Predictable, reproducible outputs
- **Extensible** - Easy to add new capabilities
- **Provider Agnostic** - Support multiple AI/analysis providers
- **Local First** - Works offline, privacy by default
- **Incremental** - Update only what changed
- **AI-Optimized** - Outputs designed for AI consumption

---

# High-Level Architecture

```
                    User
                      │
                      ▼
                Contextix CLI
                      │
                      ▼
                Command Router
                      │
                      ▼
                Pipeline Engine
                      │
 ┌────────────────────┼────────────────────┐
 ▼                    ▼                    ▼
Parser Layer     Analyzer Layer      Storage Layer
        │              │                   │
        └──────┬───────┘                   │
               ▼                           │
          Context IR                       │
               │                           │
        ┌──────┴────────┐                  │
        ▼               ▼                  │
 Memory Builder   Memory Optimizer         │
        │               │                  │
        └──────┬────────┘                  │
               ▼                           │
             Exporter                      │
               │                           │
               ▼                           │
           .context/                       │
```

---

# System Components

## 1. CLI Layer

**Responsibilities:** Receive commands, validate arguments, load configuration, initialize pipeline, display progress.

Contains no business logic.

## 2. Pipeline Engine

**Responsibilities:** Execute stages in order, handle failures, retry recoverable operations, track execution state, emit events for logging.

## 3. Parser Layer

**Purpose:** Normalize all project inputs.

**Supported:** Repository, Markdown, Text, PDF

**Output:** `ParsedDocument[]`

## 4. Analyzer Layer

**Purpose:** Transform parsed documents into structured knowledge.

**Tasks:** Semantic Chunking, Repository Analysis, Dependency Detection, Architecture Detection, Feature Detection, Constraint Detection, Decision Extraction.

**Output:** `AnalysisResult`

## 5. Context IR

The internal language of Contextix. No module communicates using YAML or Markdown directly. All modules communicate through Context IR.

```
Project
├── Metadata
├── Goals
├── Features
├── Tech Stack
├── Architecture
├── Constraints
├── Decisions
├── Current State
├── Tasks
├── Issues
└── Documents
```

## 6. Memory Builder

Transforms Context IR into persistent project memory through hierarchy creation, relationship mapping, state reconstruction, summarization.

**Output:** `ProjectMemory`

## 7. Memory Optimizer

Removes duplicates, compresses context, preserves reasoning and architecture, optimizes token usage.

**Important:** Optimization never sacrifices project understanding.

## 8. Export Layer

Generates standardized outputs in `.context/` directory.

---

# Execution Flow

```
CLI → Load Config → Parse Project → Analyze Project → Build Context IR
     → Build Memory → Optimize Memory → Export → Done
```

Each stage can emit logs and warnings.

---

# Repository Structure

```
Contextix/
├── docs/                    # Project documentation
├── research/                # Research experiments
├── schemas/                 # Machine-readable schemas (CES, Snapshot, Metadata)
├── examples/                # Reference projects for testing
├── src/                     # Production implementation
│   ├── cli/                 # User interaction (no business logic)
│   ├── core/                # Business orchestration
│   ├── pipeline/            # Context processing workflow
│   ├── parser/              # Input processing (Markdown, PDF, Repo)
│   ├── analyzer/            # Extract project understanding
│   ├── optimizer/           # Compress project memory
│   ├── exporter/            # Generate CES outputs
│   ├── storage/             # Filesystem operations
│   ├── validator/           # Validate CES compliance
│   ├── config/              # Configuration handling
│   ├── utils/               # Shared utilities
│   ├── models/              # Data models
│   ├── interfaces/          # Shared contracts, protocols, ABCs
│   ├── providers/           # Provider abstraction layer
│   │   ├── base.py          # Abstract Provider interface
│   │   ├── registry.py      # Provider discovery and registration
│   │   ├── llm/             # LLM providers
│   │   ├── analysis/        # Analysis providers
│   │   ├── export/          # Export providers
│   │   └── sponsor/         # Sponsor providers (plugin-ready)
│   └── plugins/             # Plugin system
│       ├── loader.py        # Dynamic plugin loading
│       └── manifest.py      # Plugin manifest schema
├── tests/                   # Unit, Integration, Regression tests
├── benchmarks/              # Evaluation scripts
├── scripts/                 # Developer utilities
├── assets/                  # Static assets (logos, diagrams)
├── .github/                 # GitHub configuration
├── contextix.yaml           # Project configuration
├── pyproject.toml
├── README.md
├── MANIFESTO.md
└── LICENSE
```

## Dependency Rules

```
CLI → Core → Pipeline → Components → Storage
```

Dependencies flow downward only. No circular dependencies.

---

# Storage Strategy

## MVP

Filesystem only. `.context/` directory. No database required.

## Future

```
SQLite → Project Registry → Cloud Synchronization
```

Filesystem remains the source of truth.

---

# Plugin Architecture

Every major component supports plugins:

| Plugin Type | Purpose |
|-------------|---------|
| Parser Plugin | Add new input format support |
| Analyzer Plugin | Custom analysis capabilities |
| Optimizer Plugin | Advanced compression strategies |
| Export Plugin | New output formats |
| LLM Provider Plugin | Support for different AI providers |
| Sponsor Plugin | Integration with hackathon sponsor tools |

Plugins communicate only through Context IR.

## Provider Registry Pattern

**Implementation:** `src/providers/`

```python
from contextix.providers import ProviderRegistry, Provider, ProviderType, ProviderResult

# Abstract provider interface
class Provider(ABC):
    name: str
    version: str
    provider_type: ProviderType

    def initialize(self, config: dict) -> None: ...
    def execute(self, context: PipelineContext) -> ProviderResult: ...

# Auto-discovery from plugin directories
registry = ProviderRegistry()
registry.discover("src/providers/sponsor/")
```

### Provider Types

| Type | Base Class | Purpose |
|------|------------|----------|
| `llm` | `LLMProvider` | OpenAI, Anthropic, local LLMs |
| `analysis` | `AnalysisProvider` | Code analysis, architecture detection |
| `export` | `ExportProvider` | Output format converters |
| `sponsor` | `SponsorProvider` | Hackathon sponsor integrations |
| `compute` | `ComputeProvider` | GPU/TPU/cloud compute |
| `data` | `DataProvider` | Databases, data lakes |

## Plugin Manifest

**Implementation:** `src/plugins/manifest.py`

Each plugin declares itself via `plugin.yaml`:

```yaml
name: "sponsor-x"
type: "sponsor"       # llm, analysis, export, sponsor, compute, data
version: "1.0.0"
entry: "sponsor_x.py"
description: "Integration with Sponsor X's AI platform"
config:
  api_key:
    required: true
    env: "SPONSOR_X_API_KEY"
  endpoint:
    required: false
    env: "SPONSOR_X_ENDPOINT"
    default: "https://api.sponsor-x.com"
```

### Creating a New Sponsor Plugin

```bash
# Scaffold a new plugin
contextix plugin create my-sponsor --type sponsor
```

Or manually:

1. Create `src/providers/sponsor/my_sponsor/` directory
2. Add `plugin.yaml` (see template above)
3. Add `my_sponsor.py` implementing `BaseSponsorProvider`
4. The registry auto-discovers it on next run

## Pipeline Hooks

**Implementation:** `src/providers/registry.py` - `execute_hooks()`

The pipeline accepts optional provider hooks at each stage:

| Hook | Purpose | Example Use |
|------|---------|-------------|
| `pre_parse` | Before parsing | Inject sponsor data sources |
| `post_analyze` | After analysis | Enrich with sponsor insights |
| `pre_export` | Before export | Format for sponsor requirements |
| `post_export` | After export | Submit to sponsor platform |

```python
# Pipeline executes hooks automatically
registry.execute_hooks("post_analyze", context)
registry.execute_hooks("post_export", export_result)
```

---

# API (Future - Post-MVP)

## Design Principles

- Stateless, RESTful, Predictable, Versioned
- Base endpoint: `/api/v1/`

## Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/analyze` | POST | Analyze project and build Context IR |
| `/memory` | POST | Generate Project Memory |
| `/validate` | POST | Validate CES compliance |
| `/snapshot` | POST | Generate development snapshot |
| `/export` | POST | Export memory (YAML, JSON, Markdown) |
| `/health` | GET | API status |
| `/metadata` | GET | Generator information |

## Response Format

```json
{
  "success": true,
  "data": {},
  "warnings": [],
  "errors": []
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| CTX-001 | Invalid Configuration |
| CTX-002 | Parser Failure |
| CTX-003 | Analyzer Failure |
| CTX-004 | Invalid CES |
| CTX-005 | Export Failure |
| CTX-999 | Unknown Error |

---

# Architecture Decisions

| Decision | Reason |
|----------|--------|
| CLI First | Fast, scriptable, developer-friendly |
| Local First | Privacy and offline support |
| Filesystem Storage | Simplicity and portability |
| Context IR | Decouple pipeline stages |
| Modular Components | Easier maintenance |
| Plugin Architecture | Long-term extensibility |
| Deterministic Output | Reliable AI collaboration |
| Provider Abstraction | Easy sponsor integration |

---

# Design Timeline

| Date | Decision |
|------|----------|
| 2026-06-27 | Project started - from AI context overflow problem |
| 2026-06-27 | Scope evolved: Compressor → Optimization Engine → Memory Engine |
| 2026-06-27 | Filesystem First chosen for simplicity |
| 2026-06-27 | Documentation Before Code approach adopted |
| 2026-06-27 | Context IR introduced for modularity |
| 2026-06-27 | CES created as open specification |
| 2026-06-27 | Core Engine Architecture defined |
| 2026-06-27 | Research separated from product development |
| 2026-06-27 | Philosophy refined: Preserve Understanding (not just compress) |

---

# Future Architecture

## Graph Context IR

Replace tree-based Context IR with knowledge graph for dependency traversal, impact analysis, semantic search.

## Memory Graph

Represent relationships between Features, Constraints, Decisions, Architecture, Tasks.

## AI Memory Registry

Centralized registry for sharing project memory across tools.

## Context Package (.ctx)

Portable archive format containing context.yaml, snapshot.json, metadata.json, attachments, version.

## Incremental Context Engine

Analyze only changed files. Update only affected memory nodes.

## Event-Driven Pipeline

Replace sequential execution with event-driven architecture for parallel processing, plugin ecosystem, higher scalability.

---

# Architecture Principles

**Every module knows only what it needs to know.**

Loose coupling enables evolution.

Strong interfaces enable stability.
