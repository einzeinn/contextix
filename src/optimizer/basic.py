"""Basic deterministic memory optimizer."""

from __future__ import annotations

from dataclasses import fields

from contextix.models import Decision, DomainConcept, ProjectMemory


class BasicOptimizer:
    """Remove duplicate list values while preserving order."""

    def optimize(self, memory: ProjectMemory) -> ProjectMemory:
        for field in fields(memory):
            value = getattr(memory, field.name)
            if isinstance(value, list) and value:
                # Peek at the first element to decide dedup strategy.
                first = value[0]
                if isinstance(first, Decision):
                    setattr(memory, field.name, self._dedupe_decisions(value))
                elif isinstance(first, DomainConcept):
                    setattr(memory, field.name, self._dedupe_concepts(value))
                elif isinstance(first, str):
                    setattr(memory, field.name, self._dedupe_strings(value))
        return memory

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for v in values:
            key = v.strip().lower()
            if key and key not in seen:
                seen.add(key)
                output.append(v.strip())
        return output

    def _dedupe_decisions(self, values: list[Decision]) -> list[Decision]:
        seen: set[str] = set()
        output: list[Decision] = []
        for d in values:
            key = d.what.strip().lower()
            if key and key not in seen:
                seen.add(key)
                output.append(d)
        return output

    def _dedupe_concepts(self, values: list[DomainConcept]) -> list[DomainConcept]:
        seen: set[str] = set()
        output: list[DomainConcept] = []
        for c in values:
            key = c.term.strip().lower()
            if key and key not in seen:
                seen.add(key)
                output.append(c)
        return output
