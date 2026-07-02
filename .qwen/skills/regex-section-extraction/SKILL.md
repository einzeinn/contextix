---
name: regex-section-extraction
description: Extract markdown sections by matching regex against heading text, avoiding double-anchoring bugs
source: auto-skill
extracted_at: '2026-07-02T16:57:45.622Z'
---

# Regex Section Extraction from Markdown

When extracting content under markdown headings using regex patterns, avoid the common **double-anchoring bug**.

## The bug

Building a full-line regex by wrapping a heading pattern with `^#+\s+...\s*$`:

```python
# BROKEN: heading regex already has ^ and $ anchors
heading_pattern = re.compile(rf"^#+\s+{re.escape(heading)}\s*$")
# e.g., heading = r"^goals?$" produces: ^#+\s+\^goals\?\$\s*$
#                                        ^^              ^^
#                                        double anchors — never matches
```

Even without `re.escape`, the inner `^` and `$` create invalid regex:

```python
# ALSO BROKEN: inner anchors break the outer pattern
rf"^#+\s+{heading}\s*$"  # → ^#+\s+^goals?$\s*$  (two ^ anchors)
```

## The fix

Match the heading text directly, separate from the `#` markers:

```python
def extract_section(content: str, heading: str) -> str:
    """`heading` is a regex matched against heading text after '#' markers."""
    lines = content.splitlines()
    heading_re = re.compile(heading, re.IGNORECASE)
    in_section = False
    collected: list[str] = []
    heading_level = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(stripped.split()[0])
            heading_text = stripped[level:].strip()  # text after '#' markers
            if heading_re.match(heading_text):        # match against text only
                in_section = True
                heading_level = level
                continue
            if in_section and level <= heading_level:
                break
            continue
        if in_section:
            collected.append(line.rstrip())

    # Strip trailing blank lines and horizontal rules
    while collected and (
        not collected[-1].strip()
        or re.match(r"^\s*([-*_])\1{2,}\s*$", collected[-1])
    ):
        collected.pop()

    return "\n".join(collected).strip()
```

## Why this works

- Callers can pass natural regex patterns like `r"^goals?$"` or `r"^non-functional requirements?$"`
- The `^` and `$` anchors work correctly because they match against just the heading text
- No escaping needed — the heading is treated as a raw regex
- Literal headings without special chars (like `"Features"`) still work fine