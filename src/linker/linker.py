"""Cross-document reference linker.

Builds a lightweight reference graph from markdown links and natural-language
reference patterns found in project documentation.
"""

from __future__ import annotations

import re

from contextix.models import ContextIR, DocumentReference, ParsedDocument


class DocumentLinker:
    """Resolve cross-document references in project documentation.

    Detects:
    - Markdown links: [text](path)
    - Natural-language references: "see also", "refer to", "as described in"
    - ADR references: "ADR 0003", "depends on ADR"
    """

    # Patterns that indicate a reference to another document
    REFERENCE_PATTERNS = [
        # "see also docs/architecture.md"
        re.compile(
            r"(?:see\s+(?:also|)\s*|refer\s+to\s+|described\s+in\s+|documented\s+in\s+)"
            r"([\w./-]+\.(?:md|yaml|yml|json|txt|toml|rst))",
            re.IGNORECASE,
        ),
        # "as described in the MANIFESTO"
        re.compile(
            r"(?:as\s+)?(?:described|documented|defined|explained|outlined)\s+in\s+(?:the\s+)?"
            r"([\w./-]+\.(?:md|yaml|yml|json|txt|toml|rst))",
            re.IGNORECASE,
        ),
        # "depends on ADR 0003"
        re.compile(
            r"depends?\s+on\s+(?:ADR\s+)?(\d{3,4})",
            re.IGNORECASE,
        ),
        # "ADR 0003 must be implemented first"
        re.compile(
            r"\bADR\s+(\d{3,4})\b",
            re.IGNORECASE,
        ),
    ]

    def link(self, documents: list[ParsedDocument], context: ContextIR) -> ContextIR:
        """Find and resolve cross-document references.

        Returns the context with the `references` field populated.
        """
        references: list[DocumentReference] = []
        doc_paths = {doc.source.lower() for doc in documents}

        for doc in documents:
            if doc.file_type != "markdown":
                continue

            # Strategy 1: Markdown links [text](path)
            references.extend(self._markdown_links(doc, doc_paths))

            # Strategy 2: Natural-language patterns
            references.extend(self._natural_language_refs(doc, doc_paths))

        # Deduplicate by (source, target) pair
        seen: set[tuple[str, str]] = set()
        unique: list[DocumentReference] = []
        for ref in references:
            key = (ref.source.lower(), ref.target.lower())
            if key not in seen:
                seen.add(key)
                unique.append(ref)

        context.references = unique
        return context

    def _markdown_links(
        self, doc: ParsedDocument, doc_paths: set[str]
    ) -> list[DocumentReference]:
        """Extract [text](path) links that point to known documents."""
        refs: list[DocumentReference] = []
        for match in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", doc.content):
            text = match.group(1)
            target = match.group(2)

            # Skip external URLs
            if target.startswith(("http://", "https://", "#")):
                continue

            # Normalize: remove anchors, resolve relative paths
            target = target.split("#")[0]
            normalized = self._resolve_path(doc.source, target)

            if normalized.lower() in doc_paths:
                # Skip self-references
                if normalized.lower() == doc.source.lower():
                    continue
                # Find the surrounding sentence for context
                context = self._surrounding_sentence(doc.content, match.start())
                refs.append(
                    DocumentReference(
                        source=doc.source,
                        target=normalized,
                        context=context,
                    )
                )
        return refs

    def _natural_language_refs(
        self, doc: ParsedDocument, doc_paths: set[str]
    ) -> list[DocumentReference]:
        """Extract natural-language references to other documents."""
        refs: list[DocumentReference] = []
        for pattern in self.REFERENCE_PATTERNS:
            for match in pattern.finditer(doc.content):
                target = match.group(1)

                # ADR number references: resolve to docs/adr/NNNN-*.md
                if target.isdigit():
                    adr_path = self._resolve_adr(target, doc_paths)
                    if adr_path and adr_path.lower() != doc.source.lower():
                        refs.append(
                            DocumentReference(
                                source=doc.source,
                                target=adr_path,
                                context=self._surrounding_sentence(
                                    doc.content, match.start()
                                ),
                            )
                        )
                    continue

                normalized = self._resolve_path(doc.source, target)
                if normalized.lower() in doc_paths:
                    # Skip self-references
                    if normalized.lower() == doc.source.lower():
                        continue
                    refs.append(
                        DocumentReference(
                            source=doc.source,
                            target=normalized,
                            context=self._surrounding_sentence(
                                doc.content, match.start()
                            ),
                        )
                    )
        return refs

    def _resolve_path(self, source: str, target: str) -> str:
        """Resolve a relative path from the source document's directory."""
        if "/" not in source:
            # Source is in root — target is relative to root
            return target.lstrip("/")

        source_dir = source.rsplit("/", 1)[0]
        # Simple relative path resolution
        parts = source_dir.split("/")
        for part in target.split("/"):
            if part == "..":
                if parts:
                    parts.pop()
            elif part == ".":
                continue
            else:
                parts.append(part)
        return "/".join(parts)

    def _resolve_adr(self, number: str, doc_paths: set[str]) -> str | None:
        """Find the ADR file matching the given number."""
        for path in doc_paths:
            if re.match(rf"docs/adr/{number}-", path, re.IGNORECASE):
                return path
        return None

    def _surrounding_sentence(self, content: str, pos: int) -> str:
        """Extract the sentence surrounding a position in the text."""
        # Find sentence start (previous .!? or start of text)
        start = pos
        while start > 0 and content[start - 1] not in ".!?\n":
            start -= 1
        # Find sentence end
        end = pos
        while end < len(content) and content[end] not in ".!?\n":
            end += 1
        if end < len(content) and content[end] in ".!?":
            end += 1

        sentence = content[start:end].strip()
        # Clean up markdown formatting
        sentence = re.sub(r"\s+", " ", sentence)
        # Truncate at word boundary
        if len(sentence) > 200:
            cut = sentence.rfind(" ", 0, 200)
            if cut == -1:
                cut = 200
            sentence = sentence[:cut].rstrip() + "..."
        return sentence