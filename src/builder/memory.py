"""Build ProjectMemory from Context IR.

Phase 3: merge similar entries, apply token budget, and produce compact memory.
"""

from __future__ import annotations

from contextix.models import ContextIR, Decision, DomainConcept, ProjectMemory


# ---------------------------------------------------------------------------
# Token budget: max items per category before the exporter trims further.
# These are generous — the real budget is enforced by the exporter.
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
        """Merge decisions with identical `what` (case-insensitive)."""
        seen: dict[str, Decision] = {}
        for d in decisions:
            key = d.what.strip().lower()
            if key not in seen:
                seen[key] = d
            else:
                # Keep the one with rationale if available
                existing = seen[key]
                if d.why and not existing.why:
                    seen[key] = d
                elif d.alternatives and not existing.alternatives:
                    seen[key] = d
        return list(seen.values())

    def _merge_concepts(self, concepts: list[DomainConcept]) -> list[DomainConcept]:
        """Merge concepts with identical term (case-insensitive)."""
        seen: dict[str, DomainConcept] = {}
        for c in concepts:
            key = c.term.strip().lower()
            if key not in seen:
                seen[key] = c
            else:
                # Keep the longer definition
                existing = seen[key]
                if len(c.definition) > len(existing.definition):
                    seen[key] = c
        return list(seen.values())

    # ------------------------------------------------------------------
    # Token budget — cap items per category
    # ------------------------------------------------------------------

    def _apply_budget(self, memory: ProjectMemory) -> ProjectMemory:
        for field_name, limit in CATEGORY_BUDGET.items():
            value = getattr(memory, field_name, None)
            if isinstance(value, list) and len(value) > limit:
                setattr(memory, field_name, value[:limit])
        return memory
