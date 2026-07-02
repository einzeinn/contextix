"""Filesystem operations for generated memory artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def _str_presenter(dumper: yaml.Dumper, data: str):
    # Multi-line strings (e.g. architecture diagrams) get dumped with
    # literal block style ("|") instead of an escaped single line,
    # so generated context.yaml stays human-readable.
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, _str_presenter, Dumper=yaml.SafeDumper)


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