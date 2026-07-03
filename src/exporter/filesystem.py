"""Export ProjectMemory into CES v0.1 filesystem artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path

from contextix.models import Decision, DomainConcept, Metadata, ProjectMemory, Snapshot
from contextix.storage import FileSystemStorage


def _truncate_at_word(text: str, max_chars: int) -> str:
    """Truncate text at the last word boundary before max_chars.

    If the text is shorter than max_chars, return it unchanged.
    If truncated, append '...' at a word boundary.
    """
    if len(text) <= max_chars:
        return text
    # Find the last space within the limit
    cut = text.rfind(" ", 0, max_chars)
    if cut == -1:
        cut = max_chars
    return text[:cut].rstrip() + "..."


class FileSystemExporter:
    def __init__(self, output_dir: Path) -> None:
        self.storage = FileSystemStorage(output_dir)

    def export(self, memory: ProjectMemory, project_hash: str) -> list[Path]:
        context_data = self._context_data(memory)
        snapshot = Snapshot(project_state=memory.project_state)
        metadata = Metadata(project_hash=project_hash)
        metadata.checksum = self._checksum(context_data)

        written = [
            self.storage.write_yaml("context.yaml", context_data),
            self.storage.write_json("snapshot.json", asdict(snapshot)),
            self.storage.write_json("metadata.json", asdict(metadata)),
            self.storage.write_text("bootstrap.md", self._bootstrap(memory)),
            self.storage.write_text("summary.md", self._summary(memory)),
            self.storage.write_text("architecture.md", self._architecture(memory)),
            self.storage.write_text("handoff.md", self._handoff(memory)),
        ]
        return written

    def _context_data(self, memory: ProjectMemory) -> dict:
        return {
            "project": asdict(memory.project),
            "vision": memory.vision,
            "goals": memory.goals,
            "tech_stack": memory.tech_stack,
            "architecture": self._architecture_summary(memory),
            "architecture_patterns": memory.architecture_patterns,
            "constraints": memory.constraints,
            "non_goals": memory.non_goals,
            "features": memory.features,
            "decisions": [asdict(d) for d in memory.decisions],
            "domain_concepts": [asdict(c) for c in memory.domain_concepts],
            "roadmap": memory.roadmap,
            "coding_standards": memory.coding_standards,
            "documentation": memory.documentation,
            "project_state": asdict(memory.project_state),
            "references": [asdict(r) for r in memory.references],
            "validation_issues": memory.validation_issues,
        }

    def _bootstrap(self, memory: ProjectMemory) -> str:
        """The first 500 tokens an AI reads — purpose, key decisions, constraints.

        This is the session bootstrap. It answers "what is this project?"
        in the minimum tokens needed for the AI to start working.
        """
        lines: list[str] = [
            f"# {memory.project.name}",
            "",
            memory.project.description,
            "",
            "## Purpose",
            _truncate_at_word(memory.vision, 300) if memory.vision else memory.project.description,
            "",
        ]

        # Key decisions (top 3 with rationale)
        key_decisions = [d for d in memory.decisions if d.why][:3]
        if not key_decisions:
            key_decisions = memory.decisions[:3]
        if key_decisions:
            lines.append("## Key Decisions")
            for d in key_decisions:
                lines.append(f"- {_truncate_at_word(d.what, 120)}")
                if d.why:
                    lines.append(f"  _{_truncate_at_word(d.why, 150)}_")
            lines.append("")

        # Top constraints (guardrails)
        if memory.constraints:
            lines.append("## Constraints")
            for c in memory.constraints[:5]:
                lines.append(f"- {_truncate_at_word(c, 120)}")
            lines.append("")

        # Navigation
        lines.append("## Where to Start")
        lines.append(f"- Read `{memory.documentation[0]}`" if memory.documentation else "- Read the README")
        if memory.project_state.version:
            lines.append(f"- Version: {memory.project_state.version}")
        lines.append("- Full context: `.context/context.yaml`")
        lines.append("- Architecture: `.context/architecture.md`")

        return "\n".join(lines)

    def _summary(self, memory: ProjectMemory) -> str:
        return "\n".join(
            [
                f"# {memory.project.name} — Overview",
                "",
                memory.project.description,
                "",
                "## Goals",
                self._list(memory.goals),
                "",
                "## Tech Stack",
                self._list(memory.tech_stack),
                "",
                "## Architecture Patterns",
                self._list(memory.architecture_patterns),
                "",
                "## Decisions",
                self._decisions_list(memory.decisions),
                "",
                "## Domain Concepts",
                self._concepts_list(memory.domain_concepts),
                "",
                "## Roadmap",
                self._list(memory.roadmap),
                "",
                "## Project State",
                f"Version: {memory.project_state.version}",
                self._list(memory.project_state.recent_changes),
                "",
            ]
        )

    def _architecture(self, memory: ProjectMemory) -> str:
        return f"# Architecture\n\n{memory.architecture}\n"

    def _architecture_summary(self, memory: ProjectMemory) -> str:
        """Return a concise architecture summary for context.yaml.

        The full architecture text lives in architecture.md — context.yaml
        gets only the first meaningful paragraph, skipping tables and labels.
        """
        text = memory.architecture.strip()
        if not text or text == "Architecture summary was not detected.":
            return text

        for line in text.splitlines():
            stripped = line.strip()
            # Skip headings, labels, table rows, empty lines
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if stripped.startswith("**"):
                continue
            if stripped.startswith("|") and stripped.endswith("|"):
                continue
            if len(stripped) > 40:
                return stripped

        return text.split("\n")[0] if text else ""

    def _handoff(self, memory: ProjectMemory) -> str:
        return "\n".join(
            [
                "# AI Handoff",
                "",
                f"You are working on **{memory.project.name}**.",
                f"Version: {memory.project_state.version}",
                "",
                "## How to Use This Context",
                "",
                "1. Read `bootstrap.md` first — it's the 500-token summary.",
                "2. Use `context.yaml` for structured project data.",
                "3. Read `architecture.md` for system design.",
                "4. Check `summary.md` for the full overview.",
                "",
                "## Project Purpose",
                memory.project.description,
                "",
                "## Key Decisions",
                self._decisions_list(memory.decisions[:5]),
                "",
                "## Constraints",
                self._list(memory.constraints[:5]),
                "",
                "## Non-Goals",
                self._list(memory.non_goals),
                "",
                "## Roadmap",
                self._list(memory.roadmap[:5]),
                "",
                "## Validation Issues",
                self._list(memory.validation_issues) if memory.validation_issues else "_No issues detected._",
                "",
            ]
        )

    def _list(self, values: list[str]) -> str:
        if not values:
            return "- Not detected yet."
        return "\n".join(f"- {value}" for value in values)

    def _decisions_list(self, decisions: list[Decision]) -> str:
        if not decisions:
            return "- Not detected yet."
        lines: list[str] = []
        for d in decisions:
            lines.append(f"- {d.what}")
            if d.why:
                lines.append(f"  Why: {d.why}")
            if d.source:
                lines.append(f"  Source: {d.source}")
        return "\n".join(lines)

    def _concepts_list(self, concepts: list[DomainConcept]) -> str:
        if not concepts:
            return "- Not detected yet."
        lines: list[str] = []
        for c in concepts:
            lines.append(f"- **{c.term}**: {c.definition}")
        return "\n".join(lines)

    def _checksum(self, data: dict) -> str:
        return hashlib.sha256(repr(data).encode("utf-8")).hexdigest()