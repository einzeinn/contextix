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

DEFAULT_CONTEXTIGNORE = """# ============================================================================
# Version Control
# ============================================================================
.git

# ============================================================================
# Contextix
# ============================================================================
.context
.contextix
contextix.yaml.local

# ============================================================================
# AI Agent Runtime
# ============================================================================
.qwen
.claude
.cursor
.copilot
.aider
.roo
.augment
.windsurf

# ============================================================================
# Python
# ============================================================================
.venv
venv
env
ENV

__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.tox
.coverage
htmlcov
*.pyc

# ============================================================================
# JavaScript / Node
# ============================================================================
node_modules
.npm
.pnpm-store
.yarn
.next
.nuxt
dist
build

# ============================================================================
# IDE
# ============================================================================
.vscode
.idea

# ============================================================================
# Operating System
# ============================================================================
.DS_Store
Thumbs.db

# ============================================================================
# Logs
# ============================================================================
*.log

# ============================================================================
# Temporary
# ============================================================================
tmp
temp
.cache
"""


def initialize_project(root: Path) -> Path:
    config_path = root / "contextix.yaml"
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")

    ignore_path = root / ".contextignore"
    if not ignore_path.exists():
        ignore_path.write_text(DEFAULT_CONTEXTIGNORE, encoding="utf-8")

    output_dir = root / ".context"
    output_dir.mkdir(parents=True, exist_ok=True)
    return config_path


def generate_memory(root: Path) -> PipelineResult:
    settings = load_settings(root)
    return PipelineEngine(root, settings).run()
