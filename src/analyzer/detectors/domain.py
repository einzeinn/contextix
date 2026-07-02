"""Domain concept detection — finds project-specific terminology definitions."""

from __future__ import annotations

import re

from contextix.models import DomainConcept, ParsedDocument

from .shared import extract_section, extract_sentences


class DomainConceptDetector:
    """Detect project-specific terminology from documentation.

    Strategies:
    1. Glossary sections: "Glossary", "Terminology", "Definitions"
    2. Heading-based: "### Context IR" followed by definition paragraph
    3. Inline definitions: "X is a Y that...", "**X** — definition"
    4. Knowledge model tables: extract term + description from table rows
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
        r"^knowledge model$",
        r"^structured types$",
    ]

    # Terms that are clearly project-specific (multi-word, capitalized, not generic)
    TERM_PATTERN = re.compile(
        r"\b(?:Context\s+IR|Project\s+Memory|Context\s+Exchange\s+Specification|CES|"
        r"Code\s+Navigation|Domain\s+Concept|Project\s+State|"
        r"Session\s+Bootstrap|Evolution\s+Engine|"
        r"Context\s+Portability\s+Layer)\b",
        re.IGNORECASE,
    )

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
            concepts.extend(self._heading_definitions(doc))
            concepts.extend(self._inline_definitions(doc))
            concepts.extend(self._table_concepts(doc))

        return self._deduplicate_concepts(concepts)

    def _glossary_concepts(self, doc: ParsedDocument) -> list[DomainConcept]:
        results: list[DomainConcept] = []
        for pattern in self.GLOSSARY_HEADINGS:
            section = extract_section(doc.content, pattern)
            if not section:
                continue
            for line in section.splitlines():
                match = re.match(
                    r"""(?:\*\*|__)?(.{2,60}?)(?:\*\*|__)?\s*[:\u2014-]\s*(.{10,300}?)$""",
                    line.strip(),
                )
                if match:
                    term = match.group(1).strip().strip("*_")
                    if self._is_valid_term(term):
                        results.append(
                            DomainConcept(
                                term=term,
                                definition=match.group(2).strip().rstrip("."),
                                source=doc.source,
                            )
                        )
        return results

    def _heading_definitions(self, doc: ParsedDocument) -> list[DomainConcept]:
        """Detect terms defined as headings followed by descriptive paragraphs.

        Only matches headings that look like concept names (short, capitalized,
        not sentence-like prose).
        """
        results: list[DomainConcept] = []
        lines = doc.content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            match = re.match(r"^#{2,4}\s+(.{3,60})$", stripped)
            if not match:
                continue
            term = match.group(1).strip()
            if not self._is_valid_term(term):
                continue
            # Skip headings that look like full sentences
            if term[0].islower() and len(term.split()) > 2:
                continue
            # Skip if heading ends with punctuation (sentence-like)
            if term.rstrip().endswith((".", "?", "!")):
                continue
            # Find the next paragraph
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith("#") and not next_line.startswith("|"):
                    if len(next_line) > 20:
                        # Only accept if the paragraph is definition-like
                        # (starts with the term, or with "is", "are", "a", "an", "the")
                        first_word = next_line.split()[0].lower() if next_line.split() else ""
                        if not (
                            next_line.lower().startswith(term.lower())
                            or first_word in {"is", "are", "was", "were", "a", "an", "the"}
                        ):
                            break
                        results.append(
                            DomainConcept(
                                term=term,
                                definition=next_line[:200].rstrip("."),
                                source=doc.source,
                            )
                        )
                    break
        return results

    def _inline_definitions(self, doc: ParsedDocument) -> list[DomainConcept]:
        results: list[DomainConcept] = []
        for sentence in extract_sentences(doc.content):
            for pat in self.INLINE_DEFINITION_PATTERNS:
                match = pat.search(sentence)
                if match:
                    term = match.group(1).strip().strip("*_")
                    definition = match.group(2).strip().rstrip(".")
                    if self._is_valid_term(term) and len(definition) >= 10:
                        results.append(
                            DomainConcept(
                                term=term,
                                definition=definition,
                                source=doc.source,
                            )
                        )
                    break
        return results

    def _table_concepts(self, doc: ParsedDocument) -> list[DomainConcept]:
        """Extract concepts from markdown table rows."""
        results: list[DomainConcept] = []
        # Strip code blocks first — they often contain pipe characters
        clean = re.sub(r"```[\s\S]*?```", "", doc.content)
        for line in clean.splitlines():
            stripped = line.strip()
            if not (stripped.startswith("|") and stripped.endswith("|")):
                continue
            # Skip separator rows like |------|------|
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                continue
            # Skip rows that look like code or list items
            if stripped.startswith("|-") or stripped.startswith("| -"):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 2:
                term = cells[0].strip().strip("*_")
                # Skip terms that look like code snippets or list items
                if term.startswith(("-", '"', "'", "`")):
                    continue
                definition = cells[1].strip().strip("*_")
                if self._is_valid_term(term) and len(definition) >= 10:
                    results.append(
                        DomainConcept(
                            term=term,
                            definition=definition[:200],
                            source=doc.source,
                        )
                    )
        return results

    def _is_valid_term(self, term: str) -> bool:
        """Check if a term looks like a project-specific concept.

        Valid terms are: acronyms (CES), multi-word proper nouns (Context IR),
        or single technical words (Builder). Not section titles or prose.
        """
        if len(term) < 2 or len(term) > 60:
            return False

        words = term.split()

        # Acronyms: all caps, 2+ letters (CES, API, ADR)
        if term.isupper() and len(term) >= 2 and term.isalpha():
            return True

        # Multi-word capitalized terms: each word starts with uppercase
        if len(words) >= 2:
            # Exclude section titles starting with articles/pronouns
            first = words[0].lower()
            if first in {"the", "a", "an", "our", "this", "that", "these", "those", "my", "your"}:
                return False
            if all(w[0].isupper() for w in words if w):
                return True

        # Single technical word: starts with uppercase, not a common word
        if len(words) == 1:
            if term[0].isupper() and len(term) >= 5:
                if term.lower() not in self._generic_words:
                    return True

        return False

    @property
    def _generic_words(self) -> set[str]:
        return {
            "overview", "summary", "introduction", "background", "conclusion",
            "references", "appendix", "setup", "installation", "usage",
            "configuration", "license", "contributing", "changelog",
            "getting started", "quick start", "prerequisites",
            "description", "example", "examples", "notes", "todo",
            "faq", "troubleshooting", "api", "endpoints",
            "context", "decision", "rationale", "consequences",
            "alternatives", "status", "date", "author",
            "purpose", "scope", "goals", "features", "constraints",
            "roadmap", "architecture", "dependencies", "design principles",
            "tech stack", "how it works", "philosophy",
            "what contextix is not", "the problem", "documentation",
            "license", "contributing", "long-term vision",
            "quick start", "output", "output files", "pipeline",
        }

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