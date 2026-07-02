"""Context validator — detects quality issues without blocking the pipeline.

Validation is advisory only. Issues are warnings that inform the AI assistant
or developer about potential problems in the project documentation.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from contextix.models import ContextIR, Decision, ParsedDocument


class ContextValidator:
    """Detect quality issues in extracted project context.

    Checks:
    - Missing rationale in ADR decisions
    - Broken document references
    - Duplicate or conflicting goals
    - Stale roadmap items (past target dates)
    """

    def validate(
        self, documents: list[ParsedDocument], context: ContextIR
    ) -> ContextIR:
        issues: list[str] = []

        issues.extend(self._missing_rationale(context.decisions))
        issues.extend(self._broken_references(context.references, documents))
        issues.extend(self._duplicate_goals(context.goals))
        issues.extend(self._stale_roadmap(context.roadmap))

        context.validation_issues = issues
        return context

    # ------------------------------------------------------------------
    # Missing rationale
    # ------------------------------------------------------------------

    def _missing_rationale(self, decisions: list[Decision]) -> list[str]:
        issues: list[str] = []
        for d in decisions:
            if not d.why and d.source.startswith("docs/adr/"):
                issues.append(
                    f"ADR decision has no rationale: '{d.what[:80]}' "
                    f"in {d.source}"
                )
        return issues

    # ------------------------------------------------------------------
    # Broken references
    # ------------------------------------------------------------------

    def _broken_references(
        self,
        references: list,
        documents: list[ParsedDocument],
    ) -> list[str]:
        issues: list[str] = []
        doc_paths = {doc.source.lower() for doc in documents}

        for ref in references:
            if ref.target.lower() not in doc_paths:
                issues.append(
                    f"Broken reference: {ref.source} links to "
                    f"'{ref.target}' (file not found)"
                )
        return issues

    # ------------------------------------------------------------------
    # Duplicate / conflicting goals
    # ------------------------------------------------------------------

    def _duplicate_goals(self, goals: list[str]) -> list[str]:
        issues: list[str] = []
        normalized: dict[str, str] = {}

        for goal in goals:
            key = re.sub(r"\s+", " ", goal).strip().lower()
            if key in normalized:
                existing = normalized[key]
                # Only flag when the wording differs significantly
                if goal.strip() != existing.strip():
                    issues.append(
                        f"Similar goals may conflict: "
                        f"'{existing[:80]}' vs '{goal[:80]}'"
                    )
            else:
                normalized[key] = goal
        return issues

    # ------------------------------------------------------------------
    # Stale roadmap items
    # ------------------------------------------------------------------

    _TIMELINE_DATE = re.compile(
        r"\b(?:by|in|before)\s+"
        r"(?:Q([1-4])\s*(?:'?(\d{4})|'?(\d{2}))|"
        r"(January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+(\d{4})|"
        r"(\d{4}))",
        re.IGNORECASE,
    )

    def _stale_roadmap(self, roadmap: list[str]) -> list[str]:
        issues: list[str] = []
        now = datetime.now(timezone.utc)

        for item in roadmap:
            match = self._TIMELINE_DATE.search(item)
            if not match:
                continue

            # Try to extract a year from the match
            year = self._extract_year(match)
            if year and year < now.year:
                issues.append(
                    f"Stale roadmap item (target year {year} has passed): "
                    f"'{item[:100]}'"
                )
            elif year and year == now.year:
                # Check quarter
                quarter = self._extract_quarter(match)
                current_quarter = (now.month - 1) // 3 + 1
                if quarter and quarter < current_quarter:
                    issues.append(
                        f"Stale roadmap item (target Q{quarter} {year} "
                        f"has passed): '{item[:100]}'"
                    )

        return issues

    def _extract_year(self, match: re.Match) -> int | None:
        groups = match.groups()
        # Q1 2026 → year = 2026 (4-digit, tried first)
        if groups[1]:
            return int(groups[1])
        # Q1 '26 → year = 2026 (2-digit fallback)
        if groups[2]:
            return 2000 + int(groups[2])
        # January 2025 → year = 2025
        if groups[4]:
            return int(groups[4])
        # 2025 → year = 2025
        if groups[5]:
            return int(groups[5])
        return None

    def _extract_quarter(self, match: re.Match) -> int | None:
        groups = match.groups()
        if groups[0]:
            return int(groups[0])
        # Month names
        if groups[3]:
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December",
            ]
            try:
                month = month_names.index(groups[3]) + 1
            except ValueError:
                return None
            return (month - 1) // 3 + 1
        return None