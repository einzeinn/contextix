"""Contextix pipeline orchestration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from contextix.analyzer import BasicAnalyzer
from contextix.builder import MemoryBuilder
from contextix.config import Settings
from contextix.exporter import FileSystemExporter
from contextix.optimizer import BasicOptimizer
from contextix.parser import RepositoryParser


@dataclass(frozen=True)
class PipelineResult:
    output_directory: Path
    generated_files: list[Path]
    document_count: int


class PipelineEngine:
    def __init__(self, root: Path, settings: Settings) -> None:
        self.root = root.resolve()
        self.settings = settings

    def run(self) -> PipelineResult:
        documents = RepositoryParser(
            self.root,
            enabled_file_types=self._enabled_file_types(),
        ).parse()
        context = BasicAnalyzer().analyze(documents, self.root)
        memory = MemoryBuilder().build(context)
        optimized = BasicOptimizer().optimize(memory)

        output_dir = self.root / self.settings.output_directory
        generated = FileSystemExporter(output_dir).export(
            optimized,
            project_hash=self._project_hash(documents),
        )

        return PipelineResult(
            output_directory=output_dir,
            generated_files=generated,
            document_count=len(documents),
        )

    def _project_hash(self, documents) -> str:
        digest = hashlib.sha256()
        for document in documents:
            digest.update(document.source.encode("utf-8"))
            digest.update(document.content.encode("utf-8"))
        return digest.hexdigest()

    def _enabled_file_types(self) -> set[str]:
        enabled: set[str] = set()

        if self.settings.parse_markdown:
            enabled.add("markdown")
        if self.settings.parse_text:
            enabled.add("text")
        if self.settings.parse_repo:
            enabled.update(
                {
                    "python",
                    "toml",
                    "yaml",
                    "json",
                    "javascript",
                    "typescript",
                    "html",
                    "css",
                }
            )

        return enabled
