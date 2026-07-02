"""Contextix configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Settings:
    output_directory: str = ".context"
    parse_markdown: bool = True
    parse_text: bool = True
    parse_repo: bool = True
    parse_pdf: bool = False


def load_settings(root: Path) -> Settings:
    path = root / "contextix.yaml"
    if not path.exists():
        return Settings()

    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    parser = data.get("parser", {})
    output = data.get("output", {})

    return Settings(
        output_directory=output.get("directory", ".context"),
        parse_markdown=parser.get("markdown", True),
        parse_text=parser.get("text", True),
        parse_repo=parser.get("repo", True),
        parse_pdf=parser.get("pdf", False),
    )
