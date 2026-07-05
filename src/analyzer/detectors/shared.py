"""Shared utilities for all detectors.

Markdown extraction uses mistune AST instead of regex for:
- Reliable section extraction (no code-block leaks)
- Proper list-item handling (no dangling sentences)
- Table-row filtering (no table artifacts in output)
"""

from __future__ import annotations

import re

import mistune


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _parse_ast(content: str) -> list[dict]:
    """Parse markdown content into a mistune AST."""
    md = mistune.create_markdown(renderer="ast")
    return md(content)


def _heading_text(node: dict) -> str:
    """Extract the plain text from a heading AST node."""
    return "".join(child.get("raw", "") for child in node.get("children", []))


def _ast_nodes_to_markdown(nodes: list[dict]) -> str:
    """Convert a list of AST nodes back to markdown text.

    Used by extract_section to return the section body as text that
    extract_bullets / extract_sentences can re-parse.
    """
    lines: list[str] = []
    for node in nodes:
        t = node["type"]
        if t == "blank_line":
            lines.append("")
        elif t == "paragraph":
            lines.append(_inline_text(node))
        elif t == "heading":
            level = node["attrs"]["level"]
            lines.append("#" * level + " " + _heading_text(node))
        elif t == "list":
            for item in node.get("children", []):
                if item["type"] == "list_item":
                    text = _list_item_text(item)
                    lines.append("- " + text)
        elif t == "block_code":
            # Preserve code blocks so the section text is complete.
            info = node.get("attrs", {}).get("info", "")
            lines.append("```" + info)
            lines.append(node.get("raw", "").rstrip("\n"))
            lines.append("```")
        elif t == "block_html":
            lines.append(node.get("raw", ""))
        elif t == "thematic_break":
            lines.append("---")
        # block_text, block_quote, etc. are handled recursively
    return "\n".join(lines)


def _inline_text(node: dict) -> str:
    """Extract plain text from an inline node (paragraph, block_text, etc.)."""
    parts: list[str] = []
    for child in node.get("children", []):
        if child["type"] == "text":
            parts.append(child.get("raw", ""))
        elif child["type"] == "softbreak":
            parts.append(" ")
        elif child["type"] == "linebreak":
            parts.append("\n")
        elif child["type"] == "codespan":
            parts.append(child.get("raw", ""))
        elif child["type"] in ("emphasis", "strong", "link", "image"):
            parts.append(_inline_text(child))
    return "".join(parts)


def _list_item_text(node: dict) -> str:
    """Extract plain text from a list_item AST node."""
    parts: list[str] = []
    for child in node.get("children", []):
        if child["type"] == "block_text":
            parts.append(_inline_text(child))
        elif child["type"] == "paragraph":
            parts.append(_inline_text(child))
        elif child["type"] == "list":
            # Nested list — flatten
            for item in child.get("children", []):
                if item["type"] == "list_item":
                    parts.append(_list_item_text(item))
    return " ".join(parts)


def _ensure_terminal(text: str) -> str:
    """Ensure text ends with sentence-terminating punctuation.

    Headings and list items often don't end with a period in the source
    markdown. When these fragments get joined into a single prose blob
    (see _ast_plain_text), a missing terminator lets sentence-splitting
    regexes bleed across unrelated headings/list items into one giant
    pseudo-sentence. Adding a terminator here fixes that at the source,
    for every detector that relies on extract_sentences().
    """
    stripped = text.strip()
    if not stripped:
        return stripped
    if stripped[-1] not in ".!?":
        stripped += "."
    return stripped


def _ast_plain_text(nodes: list[dict]) -> str:
    """Extract all prose text from AST nodes, skipping code blocks and blank lines.

    Used by extract_sentences to get clean prose for sentence splitting.

    Each heading and list item is terminated with punctuation before being
    joined, so that unrelated fragments never merge into a single sentence
    during splitting (see _ensure_terminal).
    """
    parts: list[str] = []
    for node in nodes:
        t = node["type"]
        if t == "paragraph":
            parts.append(_ensure_terminal(_inline_text(node)))
        elif t == "list":
            for item in node.get("children", []):
                if item["type"] == "list_item":
                    parts.append(_ensure_terminal(_list_item_text(item)))
        elif t == "block_code":
            continue  # code is never prose
        elif t == "block_html":
            continue
        elif t == "blank_line":
            continue
        elif t == "heading":
            # Heading text can be useful context — include it.
            parts.append(_ensure_terminal(_heading_text(node)))
        elif t == "thematic_break":
            continue
    return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Public API — identical signatures, AST-powered internals
# ---------------------------------------------------------------------------

def deduplicate_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for v in values:
        key = re.sub(r"\s+", " ", v).strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(v.strip())
    return result


def is_noise(text: str) -> bool:
    """Return True if the text looks like a non-prose artifact.

    Filters out: package names, dependency lists, table syntax,
    single-word identifiers, and other extraction garbage.
    All detectors must use this function — no local copies.
    """
    stripped = text.strip()
    if not stripped:
        return True
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
    # ADR titles and metadata
    if re.match(r"^ADR\s+\d{3,4}[:\s]", stripped, re.IGNORECASE):
        return True
    # Headings
    if re.match(r"^#{1,6}\s", stripped):
        return True
    # Metadata prefixes
    if re.match(r"^(Version|Status|Date|Author):", stripped, re.IGNORECASE):
        return True
    # Code blocks
    if stripped.startswith("```"):
        return True
    # Badges
    if stripped.startswith("[!"):
        return True
    # Numbered list (usually steps, not concepts)
    if re.match(r"^\d+\.\s", stripped):
        return True
    return False


def is_quoted_example(text: str) -> bool:
    """Return True if the sentence is a quoted example/illustration rather
    than an actual assertion.

    Docs often illustrate a writing convention like:
        "We chose Redis because X" is portable.
        "We chose Redis" is not.
    These contain decision/constraint keywords (e.g. "chose", "cannot")
    purely as teaching examples, not as real project decisions or
    constraints. All detectors that scan free-text sentences for keyword
    patterns must call this before treating a sentence as a match.
    """
    stripped = text.strip()
    if not stripped:
        return False
    # Sentence opens with a quotation mark — almost always an illustration
    # or citation, not a first-person assertion about the project.
    if stripped[0] in "\"'\u201c\u2018":
        return True
    # Quoted span immediately followed by a short meta-comment
    # ("... is portable.", "... is not.", "... means X").
    if re.search(
        r'["\u201c].{3,}?["\u201d]\s+(?:is|isn\'t|is\s+not|was|means|implies)\b',
        stripped,
        re.IGNORECASE,
    ):
        return True
    return False

def is_rhetorical_negation(text: str) -> bool:
    """Return True if the sentence is a rhetorical contrast opener rather
    than a real constraint or decision.

    Persuasive/philosophy docs often use a "Not because X. But because Y."
    structure to build an argument:
        "Not because the AI cannot read source code."
        "But because the AI has lost the project's accumulated understanding."
    The first half contains constraint-like keywords ("cannot") purely as
    part of a rhetorical setup, not as an actual project rule.
    """
    stripped = text.strip()
    return bool(re.match(r"^not\s+because\b", stripped, re.IGNORECASE))


def strip_table_rows(content: str) -> str:
    """Remove markdown table rows from text.

    Lines that start and end with | are table rows — not prose.
    All detectors must use this function — no local copies.
    """
    lines = content.splitlines()
    kept = [line for line in lines if not (
        line.strip().startswith("|") and line.strip().endswith("|")
    )]
    return "\n".join(kept)


def extract_section(content: str, heading: str) -> str:
    """Extract text under a markdown heading until the next heading of equal or higher level.

    `heading` is a regex pattern matched case-insensitively against the heading text.
    """
    ast = _parse_ast(content)
    heading_re = re.compile(heading, re.IGNORECASE)
    in_section = False
    target_level = 0
    collected: list[dict] = []

    for node in ast:
        if node["type"] == "heading":
            level = node["attrs"]["level"]
            text = _heading_text(node)
            if heading_re.match(text):
                in_section = True
                target_level = level
                continue
            if in_section and level <= target_level:
                break
            if in_section:
                collected.append(node)
            continue
        if in_section:
            collected.append(node)

    # Strip trailing blank lines and horizontal rules.
    while collected and collected[-1]["type"] in ("blank_line", "thematic_break"):
        collected.pop()

    return _ast_nodes_to_markdown(collected).strip()


def extract_bullets(text: str) -> list[str]:
    """Extract text from markdown list items."""
    ast = _parse_ast(text)
    items: list[str] = []
    for node in ast:
        if node["type"] == "list":
            for item in node.get("children", []):
                if item["type"] == "list_item":
                    items.append(_list_item_text(item))
    return items


def extract_sentences(text: str) -> list[str]:
    """Split text into sentences, filtering out code blocks and table rows.

    Uses mistune AST to skip code blocks and join multi-line paragraphs
    before sentence splitting.
    """
    ast = _parse_ast(text)
    prose = _ast_plain_text(ast)

    sentences: list[str] = []
    for part in re.split(r"(?<=[.!?])\s+", prose):
        clean = part.strip()
        if clean and len(clean) >= 10:
            sentences.append(clean)

    return sentences


def find_sections_by_headings(
    content: str,
    heading_patterns: list[str],
) -> list[str]:
    """Find sections whose heading matches any of the given patterns (case-insensitive).

    Returns the text content of each matching section.
    """
    ast = _parse_ast(content)
    patterns = [re.compile(p, re.IGNORECASE) for p in heading_patterns]
    results: list[str] = []
    in_target = False
    target_level = 0
    collected: list[dict] = []

    for node in ast:
        if node["type"] == "heading":
            level = node["attrs"]["level"]
            text = _heading_text(node)
            is_match = any(p.match(text) for p in patterns)
            if is_match:
                # Flush previous section if any
                if in_target and collected:
                    results.append(_ast_nodes_to_markdown(collected).strip())
                in_target = True
                target_level = level
                collected = []
                continue
            if in_target and level <= target_level:
                if collected:
                    results.append(_ast_nodes_to_markdown(collected).strip())
                in_target = False
                collected = []
                continue
            if in_target:
                collected.append(node)
            continue
        if in_target:
            collected.append(node)

    if in_target and collected:
        results.append(_ast_nodes_to_markdown(collected).strip())

    return results