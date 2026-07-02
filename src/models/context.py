"""Core data structures shared across the Contextix pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Structured knowledge types
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    """An architectural decision with rationale.

    The `why` field is the core value — it preserves the reasoning that
    would otherwise be lost when the author leaves the project.
    """
    what: str
    why: str = ""
    alternatives: list[str] = field(default_factory=list)
    source: str = ""


@dataclass
class DomainConcept:
    """Project-specific terminology definition.

    Prevents AI assistants from misinterpreting terms like "Entity",
    "Memory", or "Snapshot" across different documents.
    """
    term: str
    definition: str
    source: str = ""


@dataclass
class ProjectState:
    """Current project snapshot — regenerated every run."""
    version: str = ""
    recent_changes: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)


@dataclass
class DocumentReference:
    """A cross-reference between two project documents."""
    source: str       # "docs/adr/0001-storage.md"
    target: str       # "docs/architecture.md"
    context: str = ""  # The sentence that contained the reference


# ---------------------------------------------------------------------------
# Pipeline data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ParsedDocument:
    source: str
    content: str
    file_type: str
    language: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectIdentity:
    name: str
    description: str
    version: str = "0.1.0"


@dataclass
class AnalysisResult:
    project: ProjectIdentity
    vision: str = ""
    goals: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    architecture: str = ""
    architecture_patterns: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    domain_concepts: list[DomainConcept] = field(default_factory=list)
    roadmap: list[str] = field(default_factory=list)
    coding_standards: list[str] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)
    project_state: ProjectState = field(default_factory=ProjectState)
    references: list[DocumentReference] = field(default_factory=list)
    validation_issues: list[str] = field(default_factory=list)


@dataclass
class ContextIR(AnalysisResult):
    """Internal representation passed between stages."""


@dataclass
class ProjectMemory(AnalysisResult):
    """CES-oriented memory ready for optimization and export."""


@dataclass
class Snapshot:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project_state: ProjectState = field(default_factory=ProjectState)


@dataclass
class Metadata:
    ces_version: str = "0.1.0"
    generator: str = "contextix 0.1.0"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project_hash: str = ""
    checksum: str = ""