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

    Three strategies with confidence scoring:
    1. Heading-based (0.9): bullets from "Goals", "Objectives", "Purpose" sections
    2. Sentence patterns (0.6): "The goal is to...", "aims to..."
    3. Intent lines (0.4): "should", "must" lines — low confidence, easily noisy

    Only goals with confidence >= 0.6 are kept. Low-confidence items
    (ADR titles, metadata, document headers) are filtered out.
    """

    HEADING_PATTERNS = [
        r"^goals?$",
        r"^product goals?$",
        r"^objectives?$",
        r"^purpose$",
        r"^mission$",
        r"^core product goals?$",
    ]

    SENTENCE_PATTERNS = [
        re.compile(r"goal\s+is\s+to\s+", re.IGNORECASE),
        re.compile(r"aims?\s+to\s+", re.IGNORECASE),
        re.compile(r"purpose\s+is\s+to\s+", re.IGNORECASE),
        re.compile(r"designed\s+to\s+", re.IGNORECASE),
        re.compile(r"exists\s+to\s+", re.IGNORECASE),
        re.compile(r"objective\s+is\s+to\s+", re.IGNORECASE),
        re.compile(r"mission\s+is\s+to\s+", re.IGNORECASE),
        re.compile(r"should\s+(?:be\s+)?able\s+to\s+", re.IGNORECASE),
    ]

    # Patterns that indicate a line is NOT a real goal
    NOISE_PATTERNS = [
        re.compile(r"^ADR\s+\d{3,4}[:\s]", re.IGNORECASE),  # ADR titles
        re.compile(r"^\|\s", re.IGNORECASE),  # Table rows
        re.compile(r"^#{1,6}\s", re.IGNORECASE),  # Headings
        re.compile(r"^Version:", re.IGNORECASE),  # Metadata
        re.compile(r"^Status:", re.IGNORECASE),  # Metadata
        re.compile(r"^Date:", re.IGNORECASE),  # Metadata
        re.compile(r"^Author:", re.IGNORECASE),  # Metadata
        re.compile(r"^```", re.IGNORECASE),  # Code blocks
        re.compile(r"^\[!", re.IGNORECASE),  # Badges
        re.compile(r"^\d+\.\s", re.IGNORECASE),  # Numbered list (usually steps, not goals)
    ]

    def detect(self, documents: list[ParsedDocument]) -> list[str]:
        scored: list[tuple[float, str]] = []

        for doc in documents:
            if doc.file_type != "markdown":
                continue
            # Heading-based goals = high confidence
            for goal in self._heading_based(doc):
                scored.append((0.9, goal))
            # Sentence patterns = medium confidence
            for goal in self._sentence_patterns(doc):
                scored.append((0.6, goal))
            # Intent lines = low confidence, only if they pass noise filter
            for goal in self._intent_lines(doc):
                if not self._is_noise(goal):
                    scored.append((0.4, goal))

        # Keep only goals with confidence >= 0.6
        goals = [text for conf, text in scored if conf >= 0.6]
        return deduplicate_preserve_order(goals)

    def _is_noise(self, text: str) -> bool:
        for pat in self.NOISE_PATTERNS:
            if pat.match(text.strip()):
                return True
        return False

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
                        if len(sentence) > 15 and not self._is_noise(sentence):
                            results.append(sentence)
        return results

    def _sentence_patterns(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for sentence in extract_sentences(doc.content):
            if self._is_noise(sentence):
                continue
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
            if self._is_noise(stripped):
                continue
            # Only keep lines that look like statements, not questions or fragments
            if len(stripped) < 20:
                continue
            results.append(stripped)
        return results