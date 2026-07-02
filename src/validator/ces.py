"""Minimal CES v0.1 validator."""

from __future__ import annotations

from pathlib import Path

import yaml


def validate_context(context_file: Path) -> tuple[bool, list[str]]:
    if not context_file.exists():
        return False, [f"Missing file: {context_file}"]

    data = yaml.safe_load(context_file.read_text(encoding="utf-8")) or {}
    errors: list[str] = []

    project = data.get("project") or {}
    if not project.get("name"):
        errors.append("Missing project.name")
    if not project.get("description"):
        errors.append("Missing project.description")

    for key in ["goals", "tech_stack", "constraints", "architecture"]:
        value = data.get(key)
        if value in (None, "", []):
            errors.append(f"Missing {key}")

    return len(errors) == 0, errors
