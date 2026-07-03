"""Constraint detection — finds non-functional requirements, limits, and boundaries."""

from __future__ import annotations

import re

from contextix.models import ParsedDocument

from .shared import (
    deduplicate_preserve_order,
    extract_bullets,
    extract_section,
    extract_sentences,
    find_sections_by_headings,
)


class ConstraintDetector:
    """Detect constraints, non-functional requirements, and hard boundaries.

    Strategies:
    1. Heading-based: "Non-Functional Requirements", "Constraints", "Limitations"
    2. Modal patterns: "must not", "cannot", "shall not", "must", "shall"
    3. Boundary patterns: "limited to", "restricted to", "bounded by"
    4. Quantified constraints: "must handle X requests/sec", "must support Y users"
    5. Compliance: "must comply with", "must be SOC2", "GDPR", etc.
    """

    CONSTRAINT_HEADINGS = [
        r"^constraints?$",
        r"^non-functional requirements?$",
        r"^limitations?$",
        r"^restrictions?$",
        r"^boundaries?$",
        r"^hard limits?$",
        r"^compliance$",
        r"^security requirements?$",
    ]

    HARD_CONSTRAINT_PATTERNS = [
        re.compile(r"\b(must\s+not|cannot|shall\s+not|may\s+not|never)\b", re.IGNORECASE),
        re.compile(r"\b(restricted\s+to|limited\s+to|bounded\s+by|capped\s+at)\b", re.IGNORECASE),
        re.compile(r"\b(non-?negotiable|hard\s+constraint|hard\s+limit)\b", re.IGNORECASE),
        re.compile(r"\b(comply\s+with|compliant\s+with|must\s+be\s+SOC|must\s+be\s+GDPR|must\s+be\s+HIPAA)\b", re.IGNORECASE),
        re.compile(r"\b(must\s+(?:support|handle|process|maintain|ensure|guarantee|keep))\b", re.IGNORECASE),
        re.compile(r"\b(shall\s+(?:support|handle|process|maintain|ensure|guarantee|keep))\b", re.IGNORECASE),
        re.compile(r"\b(no\s+more\s+than|at\s+most|up\s+to|maximum\s+of|minimum\s+of)\b", re.IGNORECASE),
        re.compile(r"\b(should\s+(?:never|always))\b", re.IGNORECASE),
    ]

    def detect(self, documents: list[ParsedDocument]) -> list[str]:
        constraints: list[str] = []

        for doc in documents:
            if doc.file_type != "markdown":
                continue
            constraints.extend(self._heading_constraints(doc))
            constraints.extend(self._pattern_constraints(doc))

        return deduplicate_preserve_order(constraints)

    def _is_noise(self, text: str) -> bool:
        """Filter out lines that look like package names, dependency lists, or table syntax."""
        stripped = text.strip()
        # Package names: lowercase, no spaces, common patterns
        if re.match(r"^[a-z][a-z0-9_.-]+$", stripped):
            return True
        # Single words that look like identifiers
        if len(stripped.split()) == 1 and len(stripped) < 20:
            return True
        # Table syntax leaks
        if "|---" in stripped or "| :" in stripped:
            return True
        if stripped.count("|") > 3:
            return True
        return False

    def _heading_constraints(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for pattern in self.CONSTRAINT_HEADINGS:
            section = extract_section(doc.content, pattern)
            if section:
                section = self._strip_table_rows(section)
                bullets = extract_bullets(section)
                if bullets:
                    for b in bullets:
                        if not self._is_noise(b):
                            results.append(b)
                else:
                    for sentence in extract_sentences(section):
                        if len(sentence) > 15 and not self._is_noise(sentence):
                            results.append(sentence)
        return results

    @staticmethod
    def _strip_table_rows(content: str) -> str:
        """Remove markdown table rows."""
        lines = content.splitlines()
        kept = [line for line in lines if not (
            line.strip().startswith("|") and line.strip().endswith("|")
        )]
        return "\n".join(kept)

    def _pattern_constraints(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for sentence in extract_sentences(doc.content):
            if self._is_noise(sentence):
                continue
            for pat in self.HARD_CONSTRAINT_PATTERNS:
                if pat.search(sentence):
                    results.append(sentence)
                    break
        return results