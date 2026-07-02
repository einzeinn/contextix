"""Core data structures shared across the Contextix pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


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
    decisions: list[str] = field(default_factory=list)
    roadmap: list[str] = field(default_factory=list)
    coding_standards: list[str] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    current: list[str] = field(default_factory=list)
    next: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class ContextIR(AnalysisResult):
    """Internal representation passed between stages."""


@dataclass
class ProjectMemory(AnalysisResult):
    """CES-oriented memory ready for optimization and export."""


@dataclass
class Snapshot:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed: list[str] = field(default_factory=list)
    current: list[str] = field(default_factory=list)
    next: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class Metadata:
    ces_version: str = "0.1.0"
    generator: str = "contextix 0.1.0"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project_hash: str = ""
    checksum: str = ""