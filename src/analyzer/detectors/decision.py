"""Decision detection — finds architecture decisions, trade-offs, and rationale."""

from __future__ import annotations

import re

from contextix.models import Decision, ParsedDocument

from .shared import (
    extract_bullets,
    extract_section,
    extract_sentences,
)


class DecisionDetector:
    """Detect decisions from ADR documents and inline decision statements.

    Strategies:
    1. ADR documents: pair "Decision" + "Rationale" sections
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
        re.compile(r"(?:instead|rather)\s+than\s+", re.IGNORECASE),
        re.compile(r"in\s+favor\s+of\s+", re.IGNORECASE),
        re.compile(r"trade-?off\s*(?::|between|is)\s+", re.IGNORECASE),
        re.compile(r"\b(vs\.?|versus)\b.*\b(?:because|since|as)\b", re.IGNORECASE),
        re.compile(r"(?:prefer|preferred|chose)\s+\S+\s+over\s+", re.IGNORECASE),
    ]

    RATIONALE_HEADINGS = [
        r"^rationale$",
        r"^context$",
        r"^reasoning$",
        r"^motivation$",
        r"^why$",
        r"^background$",
    ]

    def detect(self, documents: list[ParsedDocument]) -> list[Decision]:
        decisions: list[Decision] = []

        for doc in documents:
            if doc.source.lower().startswith("docs/adr/"):
                decisions.extend(self._adr_decision(doc))
                continue

            if doc.file_type == "markdown":
                decisions.extend(self._heading_decisions(doc))
                decisions.extend(self._inline_decisions(doc))

        return self._deduplicate_decisions(decisions)

    def _adr_decision(self, doc: ParsedDocument) -> list[Decision]:
        what_section = extract_section(doc.content, "Decision")
        if not what_section:
            return []

        # Try to find the rationale section
        why = ""
        for heading in self.RATIONALE_HEADINGS:
            rationale = extract_section(doc.content, heading)
            if rationale:
                why = self._first_paragraph(rationale)
                break

        # Extract bullet items or first paragraph as individual decisions
        bullets = extract_bullets(what_section)
        if bullets:
            return [
                Decision(what=bullet, why=why, source=doc.source)
                for bullet in bullets
            ]

        paragraph = self._first_paragraph(what_section)
        if paragraph:
            return [Decision(what=paragraph, why=why, source=doc.source)]

        return []

    def _heading_decisions(self, doc: ParsedDocument) -> list[Decision]:
        results: list[Decision] = []
        for pattern in self.DECISION_HEADINGS:
            section = extract_section(doc.content, pattern)
            if not section:
                continue
            bullets = extract_bullets(section)
            if bullets:
                for bullet in bullets:
                    results.append(Decision(what=bullet, source=doc.source))
            else:
                for sentence in extract_sentences(section):
                    if len(sentence) > 15:
                        results.append(Decision(what=sentence, source=doc.source))
        return results

    def _inline_decisions(self, doc: ParsedDocument) -> list[Decision]:
        results: list[Decision] = []
        for sentence in extract_sentences(doc.content):
            for pat in self.INLINE_PATTERNS:
                if pat.search(sentence):
                    results.append(Decision(what=sentence, source=doc.source))
                    break
        return results

    def _deduplicate_decisions(self, decisions: list[Decision]) -> list[Decision]:
        seen: set[str] = set()
        result: list[Decision] = []
        for d in decisions:
            key = re.sub(r"\s+", " ", d.what).strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(d)
        return result

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