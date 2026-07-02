"""Goal detection — finds project objectives, purpose, and intended outcomes."""

from __future__ import annotations

import re

from contextix.models import ParsedDocument

from .shared import (
    deduplicate_preserve_order,
    extract_bullets,
    extract_section,
    extract_sentences,
)


class GoalDetector:
    """Detect goals from project documentation using semantic pattern matching.

    Three strategies:
    1. Heading-based: extract bullets from sections named "Goals", "Objectives", "Purpose", etc.
    2. Sentence patterns: "The goal is to...", "aims to...", "designed to..."
    3. Imperative intent: sentences with "should", "must", "will" that describe outcomes
    """

    HEADING_PATTERNS = [
        r"^goals?$",
        r"^product goals?$",
        r"^objectives?$",
        r"^purpose$",
        r"^mission$",
        r"^why.*exist",
        r"^what.*solve",
    ]

    SENTENCE_PATTERNS = [
        re.compile(r"goal\s+is\s+to\s+", re.IGNORECASE),
        re.compile(r"aims?\s+to\s+", re.IGNORECASE),
        re.compile(r"purpose\s+is\s+to\s+", re.IGNORECASE),
        re.compile(r"designed\s+to\s+", re.IGNORECASE),
        re.compile(r"exists\s+to\s+", re.IGNORECASE),
        re.compile(r"objective\s+is\s+to\s+", re.IGNORECASE),
        re.compile(r"mission\s+is\s+to\s+", re.IGNORECASE),
        re.compile(r"trying\s+to\s+", re.IGNORECASE),
        re.compile(r"wants?\s+to\s+", re.IGNORECASE),
        re.compile(r"should\s+(?:be\s+)?able\s+to\s+", re.IGNORECASE),
    ]

    INTENT_INDICATORS = [
        re.compile(r"^(?:we|the\s+project|this\s+project|contextix)\s+(?:should|must|will|shall)\s+", re.IGNORECASE),
        re.compile(r"^(?:the\s+)?(?:primary|main|key|core)\s+(?:goal|objective|aim|purpose)\s+(?:is|:)\s+", re.IGNORECASE),
    ]

    def detect(self, documents: list[ParsedDocument]) -> list[str]:
        goals: list[str] = []

        for doc in documents:
            if doc.file_type != "markdown":
                continue
            goals.extend(self._heading_based(doc))
            goals.extend(self._sentence_patterns(doc))
            goals.extend(self._intent_lines(doc))

        return deduplicate_preserve_order(goals)

    def _heading_based(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for pattern in self.HEADING_PATTERNS:
            section = extract_section(doc.content, pattern)
            if section:
                bullets = extract_bullets(section)
                if bullets:
                    results.extend(bullets)
                else:
                    for sentence in extract_sentences(section):
                        if len(sentence) > 15:
                            results.append(sentence)
        return results

    def _sentence_patterns(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for sentence in extract_sentences(doc.content):
            for pat in self.SENTENCE_PATTERNS:
                if pat.search(sentence):
                    results.append(sentence)
                    break
        return results

    def _intent_lines(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for line in doc.content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for pat in self.INTENT_INDICATORS:
                if pat.search(stripped):
                    results.append(stripped)
                    break
        return results