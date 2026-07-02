"""User-facing service functions."""

from __future__ import annotations

from pathlib import Path

from contextix.config import load_settings
from contextix.pipeline import PipelineEngine, PipelineResult


DEFAULT_CONFIG = """project:
  name: Auto

parser:
  markdown: true
  text: true
  repo: true
  pdf: false

output:
  directory: .context
"""


def initialize_project(root: Path) -> Path:
    config_path = root / "contextix.yaml"
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    output_dir = root / ".context"
    output_dir.mkdir(parents=True, exist_ok=True)
    return config_path


def generate_memory(root: Path) -> PipelineResult:
    settings = load_settings(root)
    return PipelineEngine(root, settings).run()
