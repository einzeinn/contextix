"""Export ProjectMemory into CES v0.1 filesystem artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path

from contextix.models import Metadata, ProjectMemory, Snapshot
from contextix.storage import FileSystemStorage


class FileSystemExporter:
    def __init__(self, output_dir: Path) -> None:
        self.storage = FileSystemStorage(output_dir)

    def export(self, memory: ProjectMemory, project_hash: str) -> list[Path]:
        context_data = self._context_data(memory)
        snapshot = Snapshot(
            completed=memory.completed,
            current=memory.current,
            next=memory.next,
            issues=memory.issues,
        )
        metadata = Metadata(project_hash=project_hash)
        metadata.checksum = self._checksum(context_data)

        written = [
            self.storage.write_yaml("context.yaml", context_data),
            self.storage.write_json("snapshot.json", asdict(snapshot)),
            self.storage.write_json("metadata.json", asdict(metadata)),
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
            "architecture": memory.architecture,
            "constraints": memory.constraints,
            "non_goals": memory.non_goals,
            "features": memory.features,
            "decisions": memory.decisions,
            "coding_standards": memory.coding_standards,
            "documentation": memory.documentation,
        }

    def _summary(self, memory: ProjectMemory) -> str:
        return "\n".join(
            [
                f"# {memory.project.name}",
                "",
                memory.project.description,
                "",
                "## Goals",
                self._list(memory.goals),
                "",
                "## Tech Stack",
                self._list(memory.tech_stack),
                "",
                "## Current State",
                self._list(memory.current),
                "",
            ]
        )

    def _architecture(self, memory: ProjectMemory) -> str:
        return f"# Architecture\n\n{memory.architecture}\n"

    def _handoff(self, memory: ProjectMemory) -> str:
        return "\n".join(
            [
                "# AI Handoff",
                "",
                f"You are working on {memory.project.name}.",
                "",
                "Use `.context/context.yaml` as the primary project memory.",
                "",
                "## Project Purpose",
                memory.project.description,
                "",
                "## Constraints",
                self._list(memory.constraints),
                "",
                "## Non-Goals",
                self._list(memory.non_goals),
                "",
                "## Next Work",
                self._list(memory.next),
                "",
            ]
        )

    def _list(self, values: list[str]) -> str:
        if not values:
            return "- Not detected yet."
        return "\n".join(f"- {value}" for value in values)

    def _checksum(self, data: dict) -> str:
        return hashlib.sha256(repr(data).encode("utf-8")).hexdigest()