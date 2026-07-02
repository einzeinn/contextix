---
name: semantic-detector-pattern
description: Decompose monolithic document analyzers into specialized semantic detectors with layered strategies
source: auto-skill
extracted_at: '2026-07-02T16:57:45.622Z'
---

# Semantic Detector Pattern

When upgrading a monolithic heuristic analyzer (e.g., one that only matches exact markdown headings) into a system that detects semantic categories from documents, use the **detector decomposition pattern**.

## Structure

```
src/analyzer/
├── __init__.py          # exports all detectors
├── basic.py             # orchestrator that wires detectors together
└── detectors/
    ├── __init__.py       # re-exports + shared utilities
    ├── shared.py         # extract_section, extract_bullets, dedup
    ├── goal.py           # GoalDetector
    ├── decision.py       # DecisionDetector
    ├── constraint.py     # ConstraintDetector
    ├── architecture.py   # ArchitectureDetector
    ├── techstack.py      # TechStackDetector
    └── roadmap.py        # RoadmapDetector
```

## Each detector uses three strategy layers

1. **Heading-based**: match markdown sections by heading name (e.g., `## Goals` → `GoalDetector.HEADING_PATTERNS`)
2. **Sentence patterns**: regex against natural language sentences (e.g., `"goal is to"`, `"chose X over Y"`)
3. **Intent/fallback**: broader patterns as a last resort (e.g., `"should"`, `"must"` lines, timeline terms)

## Shared utilities

- `extract_section(content, heading_regex)` — Returns text under a markdown heading. The `heading` parameter is a regex matched against the heading text (after `#` markers), NOT a full-line regex. This avoids double-anchoring bugs.
- `extract_bullets(text)` — Returns list items from markdown bullet/numbered lists.
- `deduplicate_preserve_order(values)` — Case-insensitive dedup that preserves first occurrence order.

## Orchestrator pattern

The `BasicAnalyzer` instantiates all detectors in `__init__` and delegates:

```python
class BasicAnalyzer:
    def __init__(self):
        self._goal_detector = GoalDetector()
        self._decision_detector = DecisionDetector()
        # ... etc

    def analyze(self, documents, root):
        result = AnalysisResult(
            goals=self._goal_detector.detect(documents),
            decisions=self._decision_detector.detect(documents),
            # ... etc
        )
```

## Leak prevention: file-type filtering + code block stripping

Detectors that scan for prose patterns (component descriptions, relationships) must **not** scan source code files. Otherwise, regex patterns and docstrings in `.py` / `.ts` files leak into the output:

```python
# BROKEN: scans ALL documents including source code
def _detect_components(self, documents):
    for doc in documents:
        for sentence in extract_sentences(doc.content):  # ← includes .py files!
            ...
```

**Fix with two guards:**

```python
def _detect_components(self, documents):
    for doc in documents:
        if doc.file_type != "markdown":   # Guard 1: only prose
            continue
        for sentence in extract_sentences(
            self._strip_code_blocks(doc.content)  # Guard 2: strip ``` blocks
        ):
            ...

@staticmethod
def _strip_code_blocks(content: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", content)
```

Guard 1 prevents `.py` files from being scanned at all. Guard 2 prevents fenced code blocks *inside* markdown files from being mistaken for architecture descriptions.

## Why this works

- Each detector is independently testable
- New semantic categories can be added without touching existing detectors
- Strategy layers provide fallback depth — if heading-based fails, sentence patterns catch it
- Regex-based, no LLM dependency — fast and deterministic
- File-type filtering + code-block stripping prevents source artifacts from leaking into prose analysis