"""Shared utilities for all detectors."""

from __future__ import annotations

import re


def deduplicate_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for v in values:
        key = re.sub(r"\s+", " ", v).strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(v.strip())
    return result


def extract_section(content: str, heading: str) -> str:
    """Extract text under a markdown heading until the next heading of equal or higher level.

    `heading` is a regex pattern matched case-insensitively against the heading text
    (the part after the `#` markers). Pass a literal string if you want exact match;
    use regex for flexibility (e.g. `r"^goals?$"`).
    """
    lines = content.splitlines()
    heading_re = re.compile(heading, re.IGNORECASE)
    in_section = False
    collected: list[str] = []
    heading_level = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(stripped.split()[0])
            heading_text = stripped[level:].strip()
            if heading_re.match(heading_text):
                in_section = True
                heading_level = level
                continue
            if in_section and level <= heading_level:
                break
            continue
        if in_section:
            collected.append(line.rstrip())

    while collected and (
        not collected[-1].strip()
        or re.match(r"^\s*([-*_])\1{2,}\s*$", collected[-1])
    ):
        collected.pop()

    return "\n".join(collected).strip()


def extract_bullets(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            items.append(stripped[2:].strip())
        elif re.match(r"^\d+\.\s+", stripped):
            items.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
    return items


def extract_sentences(text: str) -> list[str]:
    """Split text into sentences, filtering out headings, code blocks, and table rows.

    Multi-line paragraphs and list items are joined before sentence splitting
    to avoid dangling fragments like "Contextix is not trying to become:".
    """
    # Strip fenced code blocks first — they are never prose.
    clean = re.sub(r"```[\s\S]*?```", "", text)

    lines = clean.splitlines()
    joined: list[str] = []
    buf = ""

    for line in lines:
        stripped = line.strip()

        # Skip headings, horizontal rules, table rows, and empty lines.
        if not stripped or stripped.startswith("#"):
            if buf:
                joined.append(buf)
                buf = ""
            continue
        if re.match(r"^\s*([-*_])\1{2,}\s*$", stripped):
            if buf:
                joined.append(buf)
                buf = ""
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            if buf:
                joined.append(buf)
                buf = ""
            continue

        # Continuation line: indented, starts with a word char (not a new bullet).
        if buf and (
            line.startswith((" ", "\t"))
            and not re.match(r"^\s*[-*+]\s", line)
            and not re.match(r"^\s*\d+\.\s", line)
        ):
            buf += " " + stripped
            continue

        # Flush previous buffer and start a new one.
        if buf:
            joined.append(buf)
        buf = stripped

    if buf:
        joined.append(buf)

    # Now split each joined paragraph into sentences.
    sentences: list[str] = []
    for para in joined:
        for part in re.split(r"(?<=[.!?])\s+", para):
            clean_part = part.strip()
            if clean_part and len(clean_part) >= 10:
                sentences.append(clean_part)

    return sentences


def find_sections_by_headings(
    content: str,
    heading_patterns: list[str],
) -> list[str]:
    """Find sections whose heading matches any of the given patterns (case-insensitive)."""
    lines = content.splitlines()
    results: list[str] = []
    in_target = False
    target_level = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(stripped.split()[0])
            heading_text = stripped[level:].strip()
            is_match = any(
                re.match(pattern, heading_text, re.IGNORECASE)
                for pattern in heading_patterns
            )
            if is_match:
                in_target = True
                target_level = level
            elif in_target and level <= target_level:
                in_target = False
            continue
        if in_target:
            results.append(stripped)

    return results