"""Basic deterministic memory optimizer."""

from __future__ import annotations

from dataclasses import fields

from contextix.models import ProjectMemory


class BasicOptimizer:
    """Remove duplicate list values while preserving order."""

    def optimize(self, memory: ProjectMemory) -> ProjectMemory:
        for field in fields(memory):
            value = getattr(memory, field.name)
            if isinstance(value, list):
                setattr(memory, field.name, self._dedupe(value))
        return memory

    def _dedupe(self, values: list[str]) -> list[str]:
        seen = set()
        output = []
        for value in values:
            key = value.strip().lower()
            if key and key not in seen:
                seen.add(key)
                output.append(value.strip())
        return output
