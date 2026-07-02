"""Architecture detection — finds system design patterns, components, and relationships."""

from __future__ import annotations

import re

from contextix.models import ParsedDocument

from .shared import (
    deduplicate_preserve_order,
    extract_bullets,
    extract_section,
    extract_sentences,
)


class ArchitectureDetector:
    """Detect architecture patterns, system components, and structural relationships.

    Strategies:
    1. Pattern name detection: "microservices", "event-driven", "CQRS", "hexagonal", etc.
    2. Component extraction: "module", "service", "component", "layer", "pipeline"
    3. Architecture section headings: "Architecture", "System Design", "Components"
    4. Relationship patterns: "calls", "depends on", "communicates with"
    """

    ARCHITECTURE_HEADINGS = [
        r"^architecture$",
        r"^high-level architecture$",
        r"^system (?:architecture|design|components?)$",
        r"^execution flow$",
        r"^data flow$",
        r"^component (?:overview|diagram|architecture)$",
        r"^module (?:structure|organization|architecture)$",
        r"^design (?:overview|principles|philosophy)$",
    ]

    KNOWN_PATTERNS = [
        ("microservices", re.compile(r"\bmicroservices?\b", re.IGNORECASE)),
        ("monolith", re.compile(r"\bmonolith(?:ic)?\b", re.IGNORECASE)),
        ("event-driven", re.compile(r"\bevent[- ]driven\b", re.IGNORECASE)),
        ("CQRS", re.compile(r"\bCQRS\b")),
        ("hexagonal", re.compile(r"\bhexagonal\s+architecture\b", re.IGNORECASE)),
        ("layered", re.compile(r"\blayered\s+architecture\b", re.IGNORECASE)),
        ("pipeline", re.compile(r"\bpipeline\s+(?:architecture|pattern|design)\b", re.IGNORECASE)),
        ("plugin", re.compile(r"\bplugin\s+(?:architecture|system|pattern)\b", re.IGNORECASE)),
        ("modular", re.compile(r"\bmodular\s+(?:architecture|design|system)\b", re.IGNORECASE)),
        ("client-server", re.compile(r"\bclient[- ]server\b", re.IGNORECASE)),
        ("REST API", re.compile(r"\bREST(?:ful)?\s+API\b", re.IGNORECASE)),
        ("GraphQL", re.compile(r"\bGraphQL\b")),
        ("message queue", re.compile(r"\bmessage\s+queue\b", re.IGNORECASE)),
        ("pub-sub", re.compile(r"\bpub[- ]sub\b", re.IGNORECASE)),
        ("ETL pipeline", re.compile(r"\bETL\s+pipeline\b", re.IGNORECASE)),
        ("serverless", re.compile(r"\bserverless\b", re.IGNORECASE)),
        ("MVC", re.compile(r"\bMVC\b")),
        ("actor model", re.compile(r"\bactor\s+model\b", re.IGNORECASE)),
        ("domain-driven", re.compile(r"\bdomain[- ]driven\b", re.IGNORECASE)),
    ]

    COMPONENT_INDICATORS = [
        re.compile(r"\b(?:module|service|component|layer|package|plugin|provider|adapter|handler|engine)\b\s+(?:is|are|contains|handles|manages|responsible|provides|exposes|implements)", re.IGNORECASE),
        re.compile(r"\b(the\s+)?(?:system|application|project)\s+(?:consists\s+of|is\s+composed\s+of|has|contains|includes)\b", re.IGNORECASE),
    ]

    RELATIONSHIP_PATTERNS = [
        re.compile(r"\b(?:calls|invokes|depends\s+on|relies\s+on|uses|consumes)\b", re.IGNORECASE),
        re.compile(r"\b(?:communicates?\s+with|talks?\s+to|sends?\s+to|receives?\s+from)\b", re.IGNORECASE),
        re.compile(r"\b(?:publishes?\s+to|subscribes?\s+to|emits?|listens?\s+(?:to|for))\b", re.IGNORECASE),
    ]

    def detect(self, documents: list[ParsedDocument]) -> str:
        parts: list[str] = []

        patterns = self._detect_patterns(documents)
        if patterns:
            parts.append("**Patterns:** " + ", ".join(patterns))

        for doc in documents:
            if doc.file_type != "markdown":
                continue
            for heading in self.ARCHITECTURE_HEADINGS:
                section = extract_section(doc.content, heading)
                if section:
                    clean = self._strip_code_blocks(section)
                    if len(clean) > 30:
                        parts.append(clean)
                        break

        components = self._detect_components(documents)
        if components:
            parts.append("**Components:**\n" + "\n".join(f"- {c}" for c in components))

        relationships = self._detect_relationships(documents)
        if relationships:
            parts.append("**Relationships:**\n" + "\n".join(f"- {r}" for r in relationships))

        if not parts:
            return "Architecture summary was not detected."
        return "\n\n".join(parts)

    def detect_patterns(self, documents: list[ParsedDocument]) -> list[str]:
        return self._detect_patterns(documents)

    def _detect_patterns(self, documents: list[ParsedDocument]) -> list[str]:
        found: set[str] = set()
        for doc in documents:
            for name, pattern in self.KNOWN_PATTERNS:
                if pattern.search(doc.content):
                    found.add(name)
        return sorted(found)

    def _detect_components(self, documents: list[ParsedDocument]) -> list[str]:
        results: list[str] = []
        for doc in documents:
            if doc.file_type != "markdown":
                continue
            for sentence in extract_sentences(self._strip_code_blocks(doc.content)):
                for pat in self.COMPONENT_INDICATORS:
                    if pat.search(sentence) and len(sentence) < 200:
                        results.append(sentence)
                        break
        return deduplicate_preserve_order(results)[:8]

    def _detect_relationships(self, documents: list[ParsedDocument]) -> list[str]:
        results: list[str] = []
        for doc in documents:
            if doc.file_type != "markdown":
                continue
            for sentence in extract_sentences(self._strip_code_blocks(doc.content)):
                for pat in self.RELATIONSHIP_PATTERNS:
                    if pat.search(sentence) and len(sentence) < 200:
                        results.append(sentence)
                        break
        return deduplicate_preserve_order(results)[:6]

    @staticmethod
    def _strip_code_blocks(content: str) -> str:
        """Remove fenced code blocks (```...```) so regex/source artifacts
        inside code samples are not mistaken for architecture descriptions."""
        return re.sub(r"```[\s\S]*?```", "", content)