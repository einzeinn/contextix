---
name: markdown-sentence-extraction
description: Extract sentences from markdown without dangling fragments — join continuation lines, skip code blocks and tables
source: auto-skill
extracted_at: '2026-07-02T17:24:13.896Z'
---

# Markdown Sentence Extraction Without Dangling Fragments

When extracting sentences from markdown content for semantic analysis, naive line-by-line splitting produces dangling fragments. Multi-line list items, wrapped paragraphs, and table rows all break.

## The problem

Naive approach:

```python
# BROKEN: splits on newlines, loses list item continuations
for line in text.splitlines():
    for part in re.split(r"(?<=[.!?])\s+", line.strip()):
        sentences.append(part)
```

This produces fragments like `"Contextix is not trying to become:"` — the continuation `"a replacement for developers"` is on the next line and gets treated as a separate sentence.

## The fix: join then split

1. **Strip code blocks** first — fenced blocks (` ```...``` `) are never prose
2. **Join continuation lines** — indented lines that don't start a new bullet are part of the previous item
3. **Skip non-prose** — headings, horizontal rules, table rows (`|...|`)
4. **Split into sentences** only after joining

```python
def extract_sentences(text: str) -> list[str]:
    # 1. Strip fenced code blocks
    clean = re.sub(r"```[\s\S]*?```", "", text)

    lines = clean.splitlines()
    joined: list[str] = []
    buf = ""

    for line in lines:
        stripped = line.strip()

        # 2. Skip headings, horizontal rules, table rows, empty lines
        if not stripped or stripped.startswith("#"):
            if buf: joined.append(buf); buf = ""
            continue
        if re.match(r"^\s*([-*_])\1{2,}\s*$", stripped):
            if buf: joined.append(buf); buf = ""
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            if buf: joined.append(buf); buf = ""
            continue

        # 3. Continuation line: indented, not a new bullet
        if buf and (
            line.startswith((" ", "\t"))
            and not re.match(r"^\s*[-*+]\s", line)
            and not re.match(r"^\s*\d+\.\s", line)
        ):
            buf += " " + stripped
            continue

        # 4. Flush previous and start new
        if buf: joined.append(buf)
        buf = stripped

    if buf: joined.append(buf)

    # 5. Split joined paragraphs into sentences
    sentences = []
    for para in joined:
        for part in re.split(r"(?<=[.!?])\s+", para):
            clean = part.strip()
            if clean and len(clean) >= 10:
                sentences.append(clean)

    return sentences
```

## Why this works

- Multi-line list items like `"- Contextix is not trying to become:\n  a replacement for developers"` are joined into a single paragraph before sentence splitting
- Table rows (`| Header | Value |`) are skipped entirely — they're not prose
- Code blocks are removed before any processing — they often contain regex patterns or keywords that would otherwise be mistaken for architecture descriptions
- The `len(clean) >= 10` threshold filters out noise fragments without losing real content

## When to apply

Any time you need to extract natural language sentences from markdown files for semantic analysis (goal detection, decision detection, constraint detection, etc.).