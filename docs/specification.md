# Specification

Version: CES v0.1 / CLI v1.0 Draft

---

# Context Exchange Specification (CES)

## Purpose

CES defines a standardized, machine-readable format for representing software project understanding.

Rather than describing implementation details, CES describes project knowledge.

Designed for interoperability between AI assistants, IDEs, developer tools, and automation systems.

Implementation-independent. Any language, framework, or application may implement this specification.

## Goals

- Preserve understanding
- Minimize ambiguity
- Support deterministic parsing
- Enable cross-LLM handoff
- Remain human-readable

## Design Principles

| Principle | Description |
|-----------|-------------|
| Structured | Every field has a defined meaning. No free-form structure. |
| Deterministic | Same information produces equivalent outputs |
| Extensible | New fields without breaking backward compatibility |
| Portable | Works across OS, AI providers, and programming languages |
| Human Readable | Developers can inspect files without additional tools |
| AI Optimized | Minimizes ambiguity for language models |

---

## Directory Layout

```
.context/
├── context.yaml       # Primary project memory (long-lived knowledge)
├── snapshot.json      # Current development state (changes frequently)
├── metadata.json      # Machine metadata (CES version, checksums)
├── summary.md         # Human-readable overview
├── architecture.md    # Architecture explanation
└── handoff.md         # Prompt optimized for AI transition
```

---

## File Structures

### context.yaml

Primary project memory containing long-lived knowledge.

```yaml
project:
  name: ""
  description: ""
  version: ""

vision: ""

goals: []

tech_stack: []

architecture: ""

constraints: []

features: []

decisions: []

coding_standards: []

documentation: []
```

### snapshot.json

Current development state.

```json
{
  "timestamp": "",
  "completed": [],
  "current": [],
  "next": [],
  "issues": []
}
```

### metadata.json

Machine metadata.

```json
{
  "ces_version": "",
  "generator": "",
  "generated_at": "",
  "project_hash": "",
  "checksum": ""
}
```

---

## Required Fields

A valid CES project MUST include:

- Project Identity (name, description)
- Goals
- Tech Stack
- Constraints
- Architecture Summary
- Current State

## Optional Fields

Business Context, Deployment, Coding Convention, Testing Strategy, Security Notes, Performance Goals.

---

## Versioning

CES follows semantic versioning:

- **Major:** Breaking specification changes
- **Minor:** New optional fields
- **Patch:** Documentation improvements

Future versions remain backward compatible. Unknown fields must be ignored rather than rejected.

---

## Validation

```bash
contextix validate
```

Output:

```
✓ CES Valid
```

or

```
✗ Missing Required Fields
```

Future versions will provide JSON Schema, YAML Schema, and CLI validation.

---

## Workflow

```
Developer
    │
    ▼
contextix
    │
    ▼
CES Files
    │
    ▼
ChatGPT / Claude / Gemini / Cursor / Windsurf
    │
    ▼
Shared Project Understanding
```

---

## Future Extensions

- Project Memory Graph
- Reasoning Timeline
- Architecture Graph
- AI Conversation Summary
- Benchmark Metadata
- Plugin Metadata
- Knowledge Graph

## Future Package Format

```
project.ctx
├── .context/
├── compressed assets
├── version
└── checksums
```

---

# CLI Specification

## Overview

The Contextix CLI is the primary interface between developers and the Contextix Engine.

**Design Goals:** Simple, Predictable, Fast, Scriptable, Unix-friendly.

## Design Philosophy

| Principle | Description |
|-----------|-------------|
| Convention over Configuration | `contextix` works without configuration |
| Human Friendly | Memorable commands, readable outputs, helpful errors |
| Automation Friendly | Usable in Bash, PowerShell, CI/CD, Git Hooks, Scripts |

## Syntax

```bash
contextix [command] [options]
```

---

## Commands

### contextix

Generate project memory.

```bash
$ contextix

Analyzing Repository...
█████████░░░░

Building Context IR...
████████████

Exporting...
████████████

Done.
Generated: .context/
```

### contextix init

Initialize Contextix. Creates `.context/` and `contextix.yaml`.

### contextix update

Incrementally update project memory. Only modified files are analyzed.

### contextix snapshot

Generate a development snapshot.

### contextix export

Export memory to different formats.

```bash
contextix export markdown
contextix export yaml
contextix export json
# Future: contextix export ctx
```

### contextix validate

Validate CES compliance.

### contextix doctor

Analyze project memory quality. Checks: missing fields, stale snapshot, duplicated memory, invalid references.

### contextix diff

Compare two snapshots. Future: Git integration.

### contextix clean

Remove generated artifacts. Keeps source project intact.

### contextix version

Show CLI version.

### contextix help

Display documentation.

---

## Configuration

Priority order:

```
CLI Arguments → contextix.yaml → Default Values
```

### Example Configuration

```yaml
project:
  name: Auto

compression:
  target: balanced

parser:
  pdf: true
  markdown: true
  repo: true

output:
  directory: .context
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unknown Error |
| 2 | Invalid Configuration |
| 3 | CES Validation Failed |
| 4 | Parser Error |
| 5 | Export Error |

---

## Logging

```bash
# Default: Minimal output
contextix

# Verbose
contextix --verbose

# Debug
contextix --debug

# Silent
contextix --quiet
```

---

## Future CLI

```bash
contextix graph        # Visualize Memory Graph
contextix benchmark    # Measure Context Fidelity
contextix plugin       # Plugin Manager
contextix ai           # AI-assisted project analysis
contextix sync         # Cloud synchronization
```

---

## CLI Principles

The CLI should feel similar to: `git`, `docker`, `uv`, `cargo`

Simple commands. Predictable behavior. Clear outputs.

---

# Philosophy

CES is not designed to describe source code.

CES is designed to describe understanding.

Source code answers: **"What exists?"**

CES answers: **"Why does it exist?"**

Together they provide complete project knowledge.
