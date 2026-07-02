"""Decision detection — finds architecture decisions, trade-offs, and rationale."""

from __future__ import annotations

import re

from contextix.models import ParsedDocument

from .shared import (
    deduplicate_preserve_order,
    extract_bullets,
    extract_section,
    extract_sentences,
)


class DecisionDetector:
    """Detect decisions from ADR documents and inline decision statements.

    Strategies:
    1. ADR documents: extract "Decision" section from docs/adr/*.md
    2. Inline patterns: "We chose X because Y", "Decided to X", "Opted for X"
    3. Trade-off statements: "Trade-off", "X vs Y", "X over Y"
    4. Decision headings: "Architecture Decisions", "Decisions", "Key Decisions"
    """

    DECISION_HEADINGS = [
        r"^decisions?$",
        r"^architecture decisions?$",
        r"^key decisions?$",
        r"^design decisions?$",
        r"^technical decisions?$",
    ]

    INLINE_PATTERNS = [
        re.compile(r"(?:we|I|team)\s+(?:chose|chosen|picked|selected|went\s+with)\s+", re.IGNORECASE),
        re.compile(r"(?:we|I|team)\s+decided\s+to\s+", re.IGNORECASE),
        re.compile(r"(?:we|I|team)\s+opted\s+(?:for|to)\s+", re.IGNORECASE),
        re.compile(r"decision\s*(?::|was|is)\s+to\s+", re.IGNORECASE),
        re.compile(r"(?:rationale|reasoning)\s*(?::|was|is)\s+", re.IGNORECASE),
        re.compile(r"(?:instead|rather)\s+than\s+", re.IGNORECASE),
        re.compile(r"in\s+favor\s+of\s+", re.IGNORECASE),
        re.compile(r"trade-?off\s*(?::|between|is)\s+", re.IGNORECASE),
        re.compile(r"\b(vs\.?|versus)\b.*\b(?:because|since|as)\b", re.IGNORECASE),
        re.compile(r"(?:prefer|preferred|chose)\s+\S+\s+over\s+", re.IGNORECASE),
    ]

    def detect(self, documents: list[ParsedDocument]) -> list[str]:
        decisions: list[str] = []

        for doc in documents:
            if doc.source.lower().startswith("docs/adr/"):
                decisions.extend(self._adr_decision(doc))
                continue

            if doc.file_type == "markdown":
                decisions.extend(self._heading_decisions(doc))
                decisions.extend(self._inline_decisions(doc))

        return deduplicate_preserve_order(decisions)

    def _adr_decision(self, doc: ParsedDocument) -> list[str]:
        section = extract_section(doc.content, "Decision")
        bullets = extract_bullets(section)
        if bullets:
            return bullets

        paragraph = self._first_paragraph(section)
        return [paragraph] if paragraph else []

    def _heading_decisions(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for pattern in self.DECISION_HEADINGS:
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

    def _inline_decisions(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for sentence in extract_sentences(doc.content):
            for pat in self.INLINE_PATTERNS:
                if pat.search(sentence):
                    results.append(sentence)
                    break
        return results

    def _first_paragraph(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        paragraph: list[str] = []
        for line in lines:
            if not line:
                if paragraph:
                    break
                continue
            paragraph.append(line)
        return " ".join(paragraph)