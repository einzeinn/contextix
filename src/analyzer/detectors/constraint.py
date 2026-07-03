"""Constraint detection — finds non-functional requirements, limits, and boundaries."""

from __future__ import annotations

import re

from contextix.models import ParsedDocument

from .shared import (
    deduplicate_preserve_order,
    extract_bullets,
    extract_section,
    extract_sentences,
    is_noise,
    strip_table_rows,
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

    def _heading_constraints(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for pattern in self.CONSTRAINT_HEADINGS:
            section = extract_section(doc.content, pattern)
            if section:
                section = strip_table_rows(section)
                bullets = extract_bullets(section)
                if bullets:
                    for b in bullets:
                        if not is_noise(b):
                            results.append(b)
                else:
                    for sentence in extract_sentences(section):
                        if len(sentence) > 15 and not is_noise(sentence):
                            results.append(sentence)
        return results

    def _pattern_constraints(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for sentence in extract_sentences(doc.content):
            if is_noise(sentence):
                continue
            for pat in self.HARD_CONSTRAINT_PATTERNS:
                if pat.search(sentence):
                    results.append(sentence)
                    break
        return results