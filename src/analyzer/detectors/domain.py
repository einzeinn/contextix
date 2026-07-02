"""Domain concept detection — finds project-specific terminology definitions."""

from __future__ import annotations

import re

from contextix.models import DomainConcept, ParsedDocument

from .shared import extract_section, extract_sentences


class DomainConceptDetector:
    """Detect project-specific terminology from documentation.

    Strategies:
    1. Glossary sections: headings like "Glossary", "Terminology", "Definitions"
    2. Inline definitions: "X is a Y that...", "We define X as...", "**X**: definition"
    3. Bold-term patterns: "**Term** — definition" or "**Term**: definition"
    """

    GLOSSARY_HEADINGS = [
        r"^glossary$",
        r"^terminology$",
        r"^definitions?$",
        r"^terms?$",
        r"^concepts?$",
        r"^vocabulary$",
        r"^domain concepts?$",
        r"^key concepts?$",
    ]

    INLINE_DEFINITION_PATTERNS = [
        re.compile(
            r"(.{3,80}?)\s+(?:is|are)\s+(?:a|an|the)\s+(.{10,200}?)[.!]\s",
            re.IGNORECASE,
        ),
        re.compile(
            r"we\s+(?:define|call|refer\s+to)\s+(.{3,60}?)\s+as\s+(.{10,200}?)[.!]",
            re.IGNORECASE,
        ),
        re.compile(
            r"""(?:^|\n)\*\*(.{3,60}?)\*\*\s*[:\u2014-]\s*(.{10,200}?)(?:\.|$)""",
            re.IGNORECASE,
        ),
    ]

    def detect(self, documents: list[ParsedDocument]) -> list[DomainConcept]:
        concepts: list[DomainConcept] = []

        for doc in documents:
            if doc.file_type != "markdown":
                continue
            concepts.extend(self._glossary_concepts(doc))
            concepts.extend(self._inline_definitions(doc))

        return self._deduplicate_concepts(concepts)

    def _glossary_concepts(self, doc: ParsedDocument) -> list[DomainConcept]:
        results: list[DomainConcept] = []
        for pattern in self.GLOSSARY_HEADINGS:
            section = extract_section(doc.content, pattern)
            if not section:
                continue
            # Parse glossary entries: each line is typically "**Term**: definition"
            for line in section.splitlines():
                match = re.match(
                    r"""(?:\*\*|__)?(.{2,60}?)(?:\*\*|__)?\s*[:\u2014-]\s*(.{10,300}?)$""",
                    line.strip(),
                )
                if match:
                    results.append(
                        DomainConcept(
                            term=match.group(1).strip(),
                            definition=match.group(2).strip().rstrip("."),
                            source=doc.source,
                        )
                    )
        return results

    def _inline_definitions(self, doc: ParsedDocument) -> list[DomainConcept]:
        results: list[DomainConcept] = []
        for sentence in extract_sentences(doc.content):
            for pat in self.INLINE_DEFINITION_PATTERNS:
                match = pat.search(sentence)
                if match:
                    term = match.group(1).strip().strip("*_")
                    definition = match.group(2).strip().rstrip(".")
                    if 2 <= len(term) <= 60 and len(definition) >= 10:
                        results.append(
                            DomainConcept(
                                term=term,
                                definition=definition,
                                source=doc.source,
                            )
                        )
                    break
        return results

    def _deduplicate_concepts(
        self, concepts: list[DomainConcept]
    ) -> list[DomainConcept]:
        seen: set[str] = set()
        result: list[DomainConcept] = []
        for c in concepts:
            key = c.term.strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(c)
        return result