"""Roadmap detection — finds future plans, milestones, and upcoming work."""

from __future__ import annotations

import re

from contextix.models import ParsedDocument

from .shared import (
    deduplicate_preserve_order,
    extract_bullets,
    extract_section,
    extract_sentences,
    is_noise,
)


class RoadmapDetector:
    """Detect roadmap, milestones, and planned future work.

    Strategies:
    1. Heading-based: "Roadmap", "Milestones", "Upcoming", "Future Work", "Planned"
    2. Version patterns: "v1.0", "v2.0", "Phase 1", "Phase 2"
    3. Timeline patterns: "Q1", "Q2", "by end of", "next quarter"
    4. Progress sections: "Next Steps", "Future Enhancements"
    """

    ROADMAP_HEADINGS = [
        r"^roadmap$",
        r"^milestones?$",
        r"^upcoming$",
        r"^future\s+work$",
        r"^future\s+enhancements?$",
        r"^planned$",
        r"^plans?$",
        r"^what.s?\s+next$",
        r"^next\s+steps?$",
        r"^looking\s+forward$",
        r"^looking\s+ahead$",
        r"^on\s+the\s+horizon$",
        r"^backlog$",
        r"^wishlist$",
        r"^ideas?$",
    ]

    VERSION_PATTERNS = [
        re.compile(r"\bv(\d+\.\d+(?:\.\d+)?)\b"),
        re.compile(r"\bversion\s+(\d+\.\d+(?:\.\d+)?)\b", re.IGNORECASE),
        re.compile(r"\bphase\s+(\d+|I{1,3}|one|two|three)\b", re.IGNORECASE),
        re.compile(r"\bstage\s+(\d+|I{1,3}|one|two|three)\b", re.IGNORECASE),
        re.compile(r"\bmilestone\s+(\d+|I{1,3}|one|two|three)\b", re.IGNORECASE),
    ]

    TIMELINE_PATTERNS = [
        re.compile(r"\bQ[1-4]\s*(?:'?\d{2})?\b"),
        re.compile(r"\b(?:by|before|after|in)\s+(?:end\s+of\s+)?(?:Q[1-4]|January|February|March|April|May|June|July|August|September|October|November|December|next\s+(?:month|quarter|year|week))(?:\b|[.,;:!?]|$)", re.IGNORECASE),
        re.compile(r"\b(?:next|this|coming)\s+(?:quarter|sprint|release|version)(?:\b|[.,;:!?]|$)", re.IGNORECASE),
        re.compile(r"\b(?:short[- ]term|medium[- ]term|long[- ]term)\b", re.IGNORECASE),
    ]

    def detect(self, documents: list[ParsedDocument]) -> list[str]:
        roadmap: list[str] = []

        for doc in documents:
            if doc.file_type != "markdown":
                continue
            roadmap.extend(self._stage_items(doc))
            roadmap.extend(self._heading_roadmap(doc))
            roadmap.extend(self._version_items(doc))

        if not roadmap:
            roadmap.extend(self._progression_lines(documents))

        return deduplicate_preserve_order(roadmap)

    def _is_poetic(self, text: str) -> bool:
        """Filter out poetic/philosophical sentences that aren't real milestones."""
        stripped = text.strip().lower()
        poetic_starts = [
            "perhaps",
            "perhaps one day", "perhaps every", "if that future",
            "maybe someday", "one can dream", "in a perfect world",
            "looking forward", "we believe", "we hope",
        ]
        for start in poetic_starts:
            if stripped.startswith(start):
                return True
        return False

    # Matches "## Stage N: Title" or "## Stage N: Title (Status)" headings
    _STAGE_HEADING = re.compile(
        r"^Stage\s+(\d+)\s*:\s*(.+)$", re.IGNORECASE
    )

    def _stage_items(self, doc: ParsedDocument) -> list[str]:
        """Extract roadmap items from ## Stage N: subheadings.

        Each stage heading is followed by deliverable/feature bullet lists.
        Items are prefixed with the stage title for context.
        """
        results: list[str] = []
        lines = doc.content.splitlines()
        in_stage = False
        stage_title = ""
        in_bullets = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("## "):
                heading_text = stripped[3:].strip()
                match = self._STAGE_HEADING.match(heading_text)
                if match:
                    in_stage = True
                    stage_title = f"Stage {match.group(1)}: {match.group(2).strip()}"
                    in_bullets = False
                else:
                    in_stage = False
                    in_bullets = False
                continue

            if not in_stage:
                continue

            # Enter bullet section at **Deliverables:** or **Features:**
            if re.match(
                r"^\*\*(?:Deliverables?|Features?|Success\s+Criteria):\*\*$",
                stripped,
                re.IGNORECASE,
            ):
                in_bullets = True
                continue

            # Exit bullet section at next bold header
            if in_bullets and re.match(r"^\*\*[^*]+\*\*$", stripped):
                in_bullets = False
                continue

            # Collect bullet items
            if in_bullets and (stripped.startswith("- ") or stripped.startswith("* ")):
                item = stripped[2:].strip()
                if not is_noise(item) and not self._is_poetic(item):
                    results.append(f"{stage_title} — {item}")

        return results

    def _heading_roadmap(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for pattern in self.ROADMAP_HEADINGS:
            section = extract_section(doc.content, pattern)
            if not section:
                continue
            # Truncate at first ## subheading if the top-level heading
            # matched is # Roadmap (H1) — prevents extracting the entire file.
            if pattern in (r"^roadmap$",) and "##" in section:
                section = section.split("\n## ")[0]
            bullets = extract_bullets(section)
            if bullets:
                results.extend(
                    b for b in bullets
                    if not self._is_poetic(b) and not is_noise(b)
                )
            else:
                for sentence in extract_sentences(section):
                    if (
                        len(sentence) > 15
                        and not self._is_poetic(sentence)
                        and not is_noise(sentence)
                    ):
                        results.append(sentence)
        return results

    def _version_items(self, doc: ParsedDocument) -> list[str]:
        results: list[str] = []
        for line in doc.content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for pat in self.VERSION_PATTERNS:
                if pat.search(stripped):
                    timeline_hit = any(
                        tp.search(stripped) for tp in self.TIMELINE_PATTERNS
                    )
                    if timeline_hit:
                        if stripped.startswith("- ") or stripped.startswith("* "):
                            results.append(stripped[2:].strip())
                        elif re.match(r"^\d+\.\s+", stripped):
                            results.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
                        else:
                            results.append(stripped)
                    break
        return results

    def _progression_lines(self, documents: list[ParsedDocument]) -> list[str]:
        results: list[str] = []
        for doc in documents:
            if doc.file_type != "markdown":
                continue
            for line in doc.content.splitlines():
                stripped = line.strip()
                for pat in self.TIMELINE_PATTERNS:
                    if pat.search(stripped) and len(stripped) > 20:
                        if self._is_poetic(stripped):
                            break
                        if stripped.startswith("- ") or stripped.startswith("* "):
                            results.append(stripped[2:].strip())
                        elif re.match(r"^\d+\.\s+", stripped):
                            results.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
                        else:
                            results.append(stripped)
                        break
        return deduplicate_preserve_order(results)[:10]