"""Build ProjectMemory from Context IR.

Phase 3: merge similar entries, apply token budget, and produce compact memory.
"""

from __future__ import annotations

from contextix.models import ContextIR, Decision, DomainConcept, ProjectMemory


# ---------------------------------------------------------------------------
# Document priority: higher weight = more authoritative.
# When conflicting information exists, the higher-weighted document wins.
# ---------------------------------------------------------------------------
DOCUMENT_WEIGHTS: dict[str, int] = {
    "MANIFESTO.md": 100,
    "docs/adr/": 95,          # prefix match for all ADRs
    "README.md": 90,
    "docs/architecture.md": 90,
    "docs/rfc-": 90,           # prefix match for RFC docs
    "docs/specification.md": 85,
    "docs/PRD.md": 85,
    "docs/roadmap.md": 70,
    "docs/contributing.md": 50,
    "research/": 20,
    "": 30,                     # default for unknown documents
}


def _document_weight(source: str) -> int:
    """Return the priority weight for a document source."""
    for prefix, weight in sorted(DOCUMENT_WEIGHTS.items(), key=lambda x: -len(x[0])):
        if prefix and source.lower().startswith(prefix.lower()):
            return weight
    return DOCUMENT_WEIGHTS.get("", 30)


# ---------------------------------------------------------------------------
# Token budget: max items per category before the exporter trims further.
# ---------------------------------------------------------------------------
CATEGORY_BUDGET: dict[str, int] = {
    "goals": 10,
    "features": 8,
    "decisions": 15,
    "constraints": 10,
    "roadmap": 8,
    "coding_standards": 5,
    "domain_concepts": 10,
    "non_goals": 8,
}


class MemoryBuilder:
    """Convert internal analysis into persistent project memory.

    Operations (in order):
    1. Merge — combine near-duplicate entries
    2. Budget — cap each category to a maximum item count
    3. Build — produce the final ProjectMemory
    """

    def build(self, context: ContextIR) -> ProjectMemory:
        memory = ProjectMemory(**context.__dict__)

        memory.goals = self._merge_strings(memory.goals)
        memory.features = self._merge_strings(memory.features)
        memory.constraints = self._merge_strings(memory.constraints)
        memory.roadmap = self._merge_strings(memory.roadmap)
        memory.coding_standards = self._merge_strings(memory.coding_standards)
        memory.non_goals = self._merge_strings(memory.non_goals)
        memory.decisions = self._merge_decisions(memory.decisions)
        memory.domain_concepts = self._merge_concepts(memory.domain_concepts)

        memory = self._apply_budget(memory)

        return memory

    # ------------------------------------------------------------------
    # Merge — near-duplicate detection
    # ------------------------------------------------------------------

    def _merge_strings(self, items: list[str]) -> list[str]:
        """Merge string items that are near-duplicates.

        Two items are near-duplicates when one is a subset of the other
        (token overlap > 70%). The longer, more specific item is kept.
        """
        if len(items) <= 1:
            return items

        merged: list[str] = []
        for item in items:
            replaced = False
            for i, existing in enumerate(merged):
                if self._is_subset(item, existing):
                    # Item is less specific — skip it
                    replaced = True
                    break
                if self._is_subset(existing, item):
                    # Existing is less specific — replace with item
                    merged[i] = item
                    replaced = True
                    break
            if not replaced:
                merged.append(item)
        return merged

    def _is_subset(self, shorter: str, longer: str) -> bool:
        """Return True if `shorter` is a near-subset of `longer`."""
        words_a = set(shorter.lower().split())
        words_b = set(longer.lower().split())
        if not words_a or not words_b:
            return False
        overlap = len(words_a & words_b)
        ratio = overlap / len(words_a)
        return ratio >= 0.7

    def _merge_decisions(self, decisions: list[Decision]) -> list[Decision]:
        """Merge decisions with identical `what` (case-insensitive).

        When two decisions conflict, keep the one from the higher-priority document.
        """
        seen: dict[str, Decision] = {}
        for d in decisions:
            key = d.what.strip().lower()
            if key not in seen:
                seen[key] = d
            else:
                existing = seen[key]
                existing_w = _document_weight(existing.source)
                new_w = _document_weight(d.source)
                if new_w > existing_w:
                    seen[key] = d
                elif d.why and not existing.why:
                    seen[key] = d
                elif d.alternatives and not existing.alternatives:
                    seen[key] = d
        # Sort by document priority (highest first)
        result = list(seen.values())
        result.sort(key=lambda d: _document_weight(d.source), reverse=True)
        return result

    def _merge_concepts(self, concepts: list[DomainConcept]) -> list[DomainConcept]:
        """Merge concepts with identical term (case-insensitive).

        When two definitions conflict, keep the one from the higher-priority document.
        """
        seen: dict[str, DomainConcept] = {}
        for c in concepts:
            key = c.term.strip().lower()
            if key not in seen:
                seen[key] = c
            else:
                existing = seen[key]
                existing_w = _document_weight(existing.source)
                new_w = _document_weight(c.source)
                if new_w > existing_w:
                    seen[key] = c
                elif len(c.definition) > len(existing.definition):
                    seen[key] = c
        # Sort by document priority (highest first)
        result = list(seen.values())
        result.sort(key=lambda c: _document_weight(c.source), reverse=True)
        return result

    # ------------------------------------------------------------------
    # Token budget — cap items per category
    # ------------------------------------------------------------------

    def _apply_budget(self, memory: ProjectMemory) -> ProjectMemory:
        for field_name, limit in CATEGORY_BUDGET.items():
            value = getattr(memory, field_name, None)
            if isinstance(value, list) and len(value) > limit:
                setattr(memory, field_name, value[:limit])
        return memory
