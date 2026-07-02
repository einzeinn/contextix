"""Filesystem operations for generated memory artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class FileSystemStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def ensure_directory(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def write_text(self, name: str, content: str) -> Path:
        self.ensure_directory()
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def write_json(self, name: str, data: dict[str, Any]) -> Path:
        return self.write_text(name, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def write_yaml(self, name: str, data: dict[str, Any]) -> Path:
        return self.write_text(name, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
