"""Repository and text document parser."""

from __future__ import annotations

import os
from fnmatch import fnmatch
from pathlib import Path

from contextix.models import ParsedDocument


TEXT_SUFFIXES = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".py": "python",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".html": "html",
    ".css": "css",
}

SKIP_DIRS = {
    ".git",
    ".context",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}

LOCKFILE_NAMES = {
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}


class RepositoryParser:
    """Parse supported repository files into normalized documents."""

    def __init__(
        self,
        root: Path,
        enabled_file_types: set[str] | None = None,
        max_file_bytes: int = 250_000,
    ) -> None:
        self.root = root.resolve()
        self.enabled_file_types = enabled_file_types
        self.max_file_bytes = max_file_bytes
        self.ignore_patterns = self._load_contextignore()

    def parse(self) -> list[ParsedDocument]:
        documents: list[ParsedDocument] = []

        for path in self._iter_candidate_files():
            file_type = TEXT_SUFFIXES.get(path.suffix.lower())
            if file_type is None:
                continue

            if self.enabled_file_types is not None and file_type not in self.enabled_file_types:
                continue

            if path.stat().st_size > self.max_file_bytes:
                continue

            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            relative = path.relative_to(self.root).as_posix()
            documents.append(
                ParsedDocument(
                    source=relative,
                    content=content,
                    file_type=file_type,
                    language=self._language_for(file_type),
                    metadata={"bytes": path.stat().st_size},
                )
            )

        return documents

    def _iter_candidate_files(self):
        """Walk the tree, pruning skipped directories as we go.

        The previous implementation used `root.rglob("*")` and filtered
        SKIP_DIRS / .contextignore *after* the fact — which meant every
        file inside .git, node_modules, venv, etc. was still enumerated
        and stat'd before being discarded. On a real project those
        directories can hold tens of thousands of files, so the old
        approach could take minutes with zero output before generate
        even started doing real work. `os.walk` lets us prune `dirnames`
        in place, so we never descend into an ignored directory at all.
        """
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirpath_path = Path(dirpath)

            pruned = []
            for d in dirnames:
                if d in SKIP_DIRS:
                    continue
                rel = (dirpath_path / d).relative_to(self.root).as_posix()
                if self._matches_contextignore(rel):
                    continue
                pruned.append(d)
            dirnames[:] = pruned

            for filename in sorted(filenames):
                if filename in LOCKFILE_NAMES:
                    continue
                path = dirpath_path / filename
                relative = path.relative_to(self.root).as_posix()
                if self._matches_contextignore(relative):
                    continue
                yield path

    def _language_for(self, file_type: str) -> str | None:
        if file_type in {"markdown", "text", "toml", "yaml", "json"}:
            return None
        return file_type

    def _load_contextignore(self) -> list[str]:
        ignore_file = self.root / ".contextignore"
        if not ignore_file.exists():
            return []

        patterns = []
        for line in ignore_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped)
        return patterns

    def _matches_contextignore(self, relative: str) -> bool:
        for pattern in self.ignore_patterns:
            normalized = pattern.replace("\\", "/").strip("/")
            if fnmatch(relative, normalized) or fnmatch(relative, f"{normalized}/*"):
                return True
        return False