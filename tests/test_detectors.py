"""Tests for semantic detectors and upgraded BasicAnalyzer."""

from __future__ import annotations

from pathlib import Path

from contextix.analyzer import BasicAnalyzer
from contextix.analyzer.detectors import (
    ArchitectureDetector,
    ConstraintDetector,
    DecisionDetector,
    GoalDetector,
    RoadmapDetector,
    TechStackDetector,
)
from contextix.models import ParsedDocument


def make_doc(source: str, content: str, file_type: str = "markdown") -> ParsedDocument:
    return ParsedDocument(source=source, content=content, file_type=file_type)


class TestGoalDetector:
    def test_heading_based_goals(self) -> None:
        doc = make_doc("README.md", "## Goals\n\n- Preserve context\n- Reduce friction\n")
        goals = GoalDetector().detect([doc])
        assert "Preserve context" in goals
        assert "Reduce friction" in goals

    def test_heading_based_objectives(self) -> None:
        doc = make_doc("README.md", "## Objectives\n\n- Ship MVP by Q3\n")
        goals = GoalDetector().detect([doc])
        assert "Ship MVP by Q3" in goals

    def test_sentence_pattern_goal_is_to(self) -> None:
        doc = make_doc("README.md", "The goal is to preserve project understanding across sessions.")
        goals = GoalDetector().detect([doc])
        assert any("preserve project understanding" in g for g in goals)

    def test_sentence_pattern_aims_to(self) -> None:
        doc = make_doc("README.md", "Contextix aims to make project knowledge portable.")
        goals = GoalDetector().detect([doc])
        assert any("make project knowledge portable" in g for g in goals)

    def test_intent_line_should(self) -> None:
        # Intent lines are low confidence (0.4) and filtered out.
        # Only heading-based (0.9) and sentence patterns (0.6) are kept.
        doc = make_doc("README.md", "The project should preserve understanding beyond individual developers.")
        goals = GoalDetector().detect([doc])
        # Intent lines are dropped — they're not reliable enough
        assert len(goals) == 0

    def test_deduplicates_similar_goals(self) -> None:
        doc = make_doc("README.md", "## Goals\n\n- Preserve context\n\n- Preserve context\n")
        goals = GoalDetector().detect([doc])
        assert len(goals) == 1

    def test_non_markdown_skipped(self) -> None:
        doc = make_doc("notes.txt", "## Goals\n\n- Secret goal\n", file_type="text")
        goals = GoalDetector().detect([doc])
        assert goals == []


class TestDecisionDetector:
    def test_adr_decision_extraction(self) -> None:
        doc = make_doc(
            "docs/adr/0001-storage.md",
            "## Decision\n\n- Use filesystem storage.\n",
        )
        decisions = DecisionDetector().detect([doc])
        assert any("Use filesystem storage" in d.what for d in decisions)

    def test_adr_paragraph_decision(self) -> None:
        doc = make_doc(
            "docs/adr/0002-cache.md",
            "## Decision\n\nWe chose Redis for caching because it is fast and simple.\n",
        )
        decisions = DecisionDetector().detect([doc])
        assert any("Redis" in d.what for d in decisions)

    def test_heading_decisions_section(self) -> None:
        doc = make_doc(
            "README.md",
            "## Architecture Decisions\n\n- Use monolith first, split later\n",
        )
        decisions = DecisionDetector().detect([doc])
        assert any("Use monolith first" in d.what for d in decisions)

    def test_inline_chose_pattern(self) -> None:
        doc = make_doc(
            "README.md",
            "We chose Python over Rust because of faster prototyping speed.",
        )
        decisions = DecisionDetector().detect([doc])
        assert any("Python" in d.what for d in decisions)

    def test_inline_decided_to(self) -> None:
        doc = make_doc(
            "README.md",
            "We decided to use YAML for configuration instead of JSON.",
        )
        decisions = DecisionDetector().detect([doc])
        assert any("YAML" in d.what for d in decisions)

    def test_inline_trade_off(self) -> None:
        doc = make_doc(
            "README.md",
            "The trade-off is simplicity vs flexibility — we chose simplicity.",
        )
        decisions = DecisionDetector().detect([doc])
        assert any("simplicity" in d.what for d in decisions)

    def test_deduplicates(self) -> None:
        doc = make_doc(
            "README.md",
            "## Decisions\n\n- Use Redis\n\n- Use Redis\n",
        )
        decisions = DecisionDetector().detect([doc])
        assert len(decisions) == 1


class TestConstraintDetector:
    def test_heading_constraints(self) -> None:
        doc = make_doc(
            "README.md",
            "## Constraints\n\n- Must support 10k concurrent users\n",
        )
        constraints = ConstraintDetector().detect([doc])
        assert "Must support 10k concurrent users" in constraints

    def test_must_not_pattern(self) -> None:
        doc = make_doc(
            "README.md",
            "The system must not lose data during a crash.",
        )
        constraints = ConstraintDetector().detect([doc])
        assert any("must not lose data" in c for c in constraints)

    def test_cannot_pattern(self) -> None:
        doc = make_doc(
            "README.md",
            "We cannot use cloud services due to regulatory requirements.",
        )
        constraints = ConstraintDetector().detect([doc])
        assert any("cannot use cloud" in c for c in constraints)

    def test_limited_to_pattern(self) -> None:
        doc = make_doc(
            "README.md",
            "Storage is limited to 100GB per project.",
        )
        constraints = ConstraintDetector().detect([doc])
        assert any("limited to 100GB" in c for c in constraints)

    def test_compliance_pattern(self) -> None:
        doc = make_doc(
            "README.md",
            "The system must comply with GDPR requirements.",
        )
        constraints = ConstraintDetector().detect([doc])
        assert any("GDPR" in c for c in constraints)

    def test_must_support_quantified(self) -> None:
        doc = make_doc(
            "README.md",
            "The API must handle 50,000 requests per second.",
        )
        constraints = ConstraintDetector().detect([doc])
        assert any("50,000" in c for c in constraints)


class TestArchitectureDetector:
    def test_detects_microservices_pattern(self) -> None:
        doc = make_doc(
            "docs/architecture.md",
            "The system follows a microservices architecture.",
        )
        patterns = ArchitectureDetector().detect_patterns([doc])
        assert "microservices" in patterns

    def test_detects_pipeline_pattern(self) -> None:
        doc = make_doc(
            "README.md",
            "We use a pipeline architecture for data processing stages.",
        )
        patterns = ArchitectureDetector().detect_patterns([doc])
        assert "pipeline" in patterns

    def test_detects_event_driven(self) -> None:
        doc = make_doc(
            "README.md",
            "The communication layer is event-driven.",
        )
        patterns = ArchitectureDetector().detect_patterns([doc])
        assert "event-driven" in patterns

    def test_architecture_section_extraction(self) -> None:
        doc = make_doc(
            "docs/architecture.md",
            "## Architecture\n\nThe system is composed of three layers: parser, analyzer, and exporter.\n",
        )
        arch = ArchitectureDetector().detect([doc])
        assert "parser, analyzer, and exporter" in arch

    def test_component_detection(self) -> None:
        doc = make_doc(
            "README.md",
            "The analyzer module is responsible for extracting project understanding from parsed documents.",
        )
        arch = ArchitectureDetector().detect([doc])
        assert "**Components:**" in arch

    def test_relationship_detection(self) -> None:
        doc = make_doc(
            "README.md",
            "The pipeline engine depends on the analyzer, builder, and exporter modules.",
        )
        arch = ArchitectureDetector().detect([doc])
        assert "**Relationships:**" in arch

    def test_no_patterns_found(self) -> None:
        doc = make_doc("README.md", "# Hello\n\nJust a simple project.\n")
        patterns = ArchitectureDetector().detect_patterns([doc])
        assert patterns == []


class TestTechStackDetector:
    def test_detects_python(self) -> None:
        doc = make_doc("main.py", "print('hello')", file_type="python")
        stack = TechStackDetector().detect([doc])
        assert "Python" in stack

    def test_detects_from_requirements(self) -> None:
        doc = make_doc("requirements.txt", "fastapi>=0.100.0\npydantic>=2.0\n")
        stack = TechStackDetector().detect([doc])
        assert "fastapi" in stack
        assert "pydantic" in stack

    def test_detects_from_pyproject(self) -> None:
        doc = make_doc("pyproject.toml", 'dependencies = [\n  "click>=8.0",\n  "rich>=13.0",\n]\n')
        stack = TechStackDetector().detect([doc])
        assert "click" in stack
        assert "rich" in stack

    def test_detects_databases(self) -> None:
        doc = make_doc("README.md", "We use PostgreSQL as the primary database and Redis for caching.")
        stack = TechStackDetector().detect([doc])
        assert "PostgreSQL" in stack
        assert "Redis" in stack

    def test_detects_infrastructure(self) -> None:
        doc = make_doc("README.md", "Deployed on AWS with Docker containers and GitHub Actions CI.")
        stack = TechStackDetector().detect([doc])
        assert "Docker" in stack
        assert "AWS" in stack
        assert "GitHub Actions" in stack

    def test_detects_multiple_languages(self) -> None:
        docs = [
            make_doc("app.py", "...", file_type="python"),
            make_doc("utils.ts", "...", file_type="typescript"),
        ]
        stack = TechStackDetector().detect(docs)
        assert "Python" in stack
        assert "TypeScript" in stack


class TestRoadmapDetector:
    def test_heading_roadmap_bullets(self) -> None:
        doc = make_doc(
            "README.md",
            "## Roadmap\n\n- Add PDF parser\n- Add LLM integration\n- Ship v1.0\n",
        )
        roadmap = RoadmapDetector().detect([doc])
        assert "Add PDF parser" in roadmap
        assert "Add LLM integration" in roadmap

    def test_heading_next_steps(self) -> None:
        doc = make_doc(
            "README.md",
            "## Next Steps\n\n- Improve test coverage\n- Add CI pipeline\n",
        )
        roadmap = RoadmapDetector().detect([doc])
        assert "Improve test coverage" in roadmap

    def test_heading_future_work(self) -> None:
        doc = make_doc(
            "README.md",
            "## Future Work\n\nPlugin system and community contributions.\n",
        )
        roadmap = RoadmapDetector().detect([doc])
        assert any("Plugin system" in r for r in roadmap)

    def test_version_timeline_items(self) -> None:
        doc = make_doc(
            "README.md",
            "- v1.0 ships by end of Q3 2026 with core memory engine\n",
        )
        roadmap = RoadmapDetector().detect([doc])
        assert any("v1.0" in r for r in roadmap)

    def test_phase_detection(self) -> None:
        doc = make_doc(
            "README.md",
            "- Phase 1: MVP foundation by Q4\n- Phase 2: Advanced detection by Q1 2027\n",
        )
        roadmap = RoadmapDetector().detect([doc])
        assert any("Phase 1" in r for r in roadmap)
        assert any("Phase 2" in r for r in roadmap)

    def test_timeline_progression_fallback(self) -> None:
        doc = make_doc(
            "README.md",
            "We plan to release the stable version by next quarter.\n",
        )
        roadmap = RoadmapDetector().detect([doc])
        assert any("next quarter" in r for r in roadmap)


class TestBasicAnalyzerIntegration:
    def test_full_pipeline_with_new_detectors(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text(
            "\n".join([
                "# Contextix",
                "",
                "A project memory engine.",
                "",
                "## Goals",
                "",
                "- Preserve project understanding",
                "- Make knowledge portable",
                "",
                "## Features",
                "",
                "- Memory export to YAML",
                "- CLI interface",
                "",
                "## Architecture Decisions",
                "",
                "- Use filesystem-first storage",
                "",
                "## Constraints",
                "",
                "- Must support 10k documents",
                "",
                "## Roadmap",
                "",
                "- Add LLM integration by Q4",
                "",
            ]),
            encoding="utf-8",
        )

        (tmp_path / "docs" / "adr").mkdir(parents=True)
        (tmp_path / "docs" / "adr" / "0001-storage.md").write_text(
            "# ADR 0001: Storage\n\n## Decision\n\n- Use JSON files for memory storage.\n",
            encoding="utf-8",
        )

        analyzer = BasicAnalyzer()
        from contextix.models import ParsedDocument

        docs = [
            ParsedDocument(
                source="README.md",
                content=(tmp_path / "README.md").read_text(encoding="utf-8"),
                file_type="markdown",
            ),
            ParsedDocument(
                source="docs/adr/0001-storage.md",
                content=(tmp_path / "docs/adr/0001-storage.md").read_text(encoding="utf-8"),
                file_type="markdown",
            ),
        ]

        result = analyzer.analyze(docs, tmp_path)

        assert len(result.goals) >= 2
        assert any("Preserve project understanding" in g for g in result.goals)
        assert any("Make knowledge portable" in g for g in result.goals)

        assert len(result.features) >= 2
        assert "Memory export to YAML" in result.features

        assert len(result.decisions) >= 1
        assert any("filesystem-first" in d.what for d in result.decisions)

        assert len(result.constraints) >= 1
        assert any("10k documents" in c for c in result.constraints)

        assert len(result.roadmap) >= 1
        assert any("LLM integration" in r for r in result.roadmap)

        assert hasattr(result, "architecture_patterns")
        assert isinstance(result.architecture_patterns, list)


class TestExtractionRegression:
    """Regression tests for leaks, dangling sentences, and duplication."""

    def test_code_blocks_not_leaked_into_relationships(self) -> None:
        detector = ArchitectureDetector()
        readme = make_doc(
            "README.md",
            "## Architecture\n\nThe parser depends on the analyzer.\n",
        )
        source_code = make_doc(
            "src/analyzer/basic.py",
            'import re\nre.compile(r"\\b(?:calls|invokes|depends\\s+on)\\b")\n',
            file_type="python",
        )
        arch = detector.detect([readme, source_code])
        assert "re.compile" not in arch
        assert "depends on" in arch

    def test_docstrings_not_leaked_into_components(self) -> None:
        detector = ArchitectureDetector()
        readme = make_doc(
            "README.md",
            "The analyzer module is responsible for extraction.\n",
        )
        source_code = make_doc(
            "src/plugin.py",
            'def cleanup():\n    """Called when provider is no longer needed."""\n    pass\n',
            file_type="python",
        )
        arch = detector.detect([readme, source_code])
        assert "no longer needed" not in arch

    def test_markdown_table_rows_not_extracted_as_sentences(self) -> None:
        doc = make_doc(
            "README.md",
            "## Decisions\n\n| Decision | Reason |\n|----------|--------|\n| Use Redis | Speed |\n",
        )
        decisions = DecisionDetector().detect([doc])
        assert "| Decision | Reason |" not in decisions
        assert "|----------|--------|" not in decisions

    def test_code_blocks_in_markdown_not_leaked(self) -> None:
        detector = ArchitectureDetector()
        doc = make_doc(
            "README.md",
            "## Architecture\n\nThe pipeline is modular and processes documents through multiple stages.\n\n```python\nimport re\nre.compile(r'calls|invokes')\n```\n",
        )
        arch = detector.detect([doc])
        assert "re.compile" not in arch
        assert "pipeline is modular" in arch

    def test_multi_line_list_item_not_dangling(self) -> None:
        from contextix.analyzer.detectors.shared import extract_sentences

        text = "- Contextix is not trying to become:\n  a replacement for developers\n  or a documentation tool.\n"
        sentences = extract_sentences(text)
        combined = " ".join(sentences)
        assert "become: a replacement for developers" in combined or "become: a replacement for developers or a documentation tool" in combined

    def test_multi_line_paragraph_not_dangling(self) -> None:
        from contextix.analyzer.detectors.shared import extract_sentences

        text = "Contextix is not trying to become:\na replacement for developers or documentation.\n"
        sentences = extract_sentences(text)
        combined = " ".join(sentences)
        assert "become: a replacement" in combined

    def test_table_rows_filtered_from_extract_sentences(self) -> None:
        from contextix.analyzer.detectors.shared import extract_sentences

        text = "Some text.\n| Header | Value |\n|--------|-------|\n| Foo | Bar |\nMore text here.\n"
        sentences = extract_sentences(text)
        assert "| Header | Value |" not in sentences
        assert "| Foo | Bar |" not in sentences
        assert any("Some text" in s for s in sentences)
        assert any("More text here" in s for s in sentences)

    def test_context_yaml_includes_roadmap_and_patterns(self) -> None:
        from contextix.models import ProjectMemory, ProjectIdentity
        from contextix.exporter import FileSystemExporter

        memory = ProjectMemory(
            project=ProjectIdentity(name="Test", description="Test project"),
            architecture="The system uses a pipeline architecture for processing.",
            architecture_patterns=["pipeline", "modular"],
            roadmap=["Add PDF parser by Q4", "Ship v1.0"],
            goals=["Preserve context"],
            tech_stack=["Python"],
            documentation=["README.md"],
        )
        exporter = FileSystemExporter.__new__(FileSystemExporter)
        data = exporter._context_data(memory)

        assert "architecture_patterns" in data
        assert data["architecture_patterns"] == ["pipeline", "modular"]
        assert "roadmap" in data
        assert data["roadmap"] == ["Add PDF parser by Q4", "Ship v1.0"]
        assert len(data["architecture"]) < 200

    def test_architecture_summary_is_concise(self) -> None:
        from contextix.models import ProjectMemory, ProjectIdentity
        from contextix.exporter import FileSystemExporter

        long_arch = "**Patterns:** pipeline, modular\n\n" + "The system uses a pipeline architecture for processing documents through stages.\n" + "**Components:**\n- Parser\n- Analyzer\n- Exporter\n" + "**Relationships:**\n- Parser depends on Analyzer\n"
        memory = ProjectMemory(
            project=ProjectIdentity(name="Test", description="Test"),
            architecture=long_arch,
            architecture_patterns=["pipeline"],
            goals=[],
            tech_stack=[],
            documentation=[],
        )
        exporter = FileSystemExporter.__new__(FileSystemExporter)
        summary = exporter._architecture_summary(memory)

        assert "**Patterns:**" not in summary
        assert "**Components:**" not in summary
        assert "**Relationships:**" not in summary
        assert len(summary) < 200


class TestMemoryBuilder:
    def test_merge_near_duplicate_strings(self) -> None:
        from contextix.builder import MemoryBuilder
        from contextix.models import ContextIR, ProjectIdentity

        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            goals=[
                "Preserve project understanding",
                "Preserve project understanding across AI sessions",
                "Completely different goal",
            ],
        )
        builder = MemoryBuilder()
        result = builder.build(context)

        # "Preserve project understanding" is a subset of the longer one
        assert "Preserve project understanding across AI sessions" in result.goals
        assert "Completely different goal" in result.goals
        # The shorter one should be merged away
        assert result.goals.count("Preserve project understanding") == 0 or len(result.goals) == 2

    def test_merge_keeps_distinct_items(self) -> None:
        from contextix.builder import MemoryBuilder
        from contextix.models import ContextIR, ProjectIdentity

        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            goals=["Reduce token usage", "Preserve context", "Enable cross-LLM handoff"],
        )
        builder = MemoryBuilder()
        result = builder.build(context)
        assert len(result.goals) == 3

    def test_merge_decisions_deduplicates_by_what(self) -> None:
        from contextix.builder import MemoryBuilder
        from contextix.models import ContextIR, Decision, ProjectIdentity

        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            decisions=[
                Decision(what="Use Redis", why="Fast", source="adr1.md"),
                Decision(what="Use Redis", why="", source="adr2.md"),
            ],
        )
        builder = MemoryBuilder()
        result = builder.build(context)
        assert len(result.decisions) == 1
        assert result.decisions[0].why == "Fast"

    def test_token_budget_caps_lists(self) -> None:
        from contextix.builder.memory import MemoryBuilder, CATEGORY_BUDGET
        from contextix.models import ContextIR, ProjectIdentity

        goals = [f"Goal {i}" for i in range(20)]
        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            goals=goals,
        )
        builder = MemoryBuilder()
        result = builder.build(context)
        assert len(result.goals) == CATEGORY_BUDGET["goals"]

    def test_empty_lists_unchanged(self) -> None:
        from contextix.builder import MemoryBuilder
        from contextix.models import ContextIR, ProjectIdentity

        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
        )
        builder = MemoryBuilder()
        result = builder.build(context)
        assert result.goals == []
        assert result.decisions == []
        assert result.domain_concepts == []


class TestDocumentLinker:
    def test_markdown_links_detected(self) -> None:
        from contextix.linker import DocumentLinker
        from contextix.models import ContextIR, ParsedDocument, ProjectIdentity

        docs = [
            ParsedDocument(
                source="README.md",
                content="See [architecture](docs/architecture.md) for details.",
                file_type="markdown",
            ),
            ParsedDocument(
                source="docs/architecture.md",
                content="# Architecture\n\nThe system is a pipeline.",
                file_type="markdown",
            ),
        ]
        context = ContextIR(project=ProjectIdentity(name="Test", description=""))
        linker = DocumentLinker()
        result = linker.link(docs, context)

        assert len(result.references) >= 1
        assert any(r.target == "docs/architecture.md" for r in result.references)

    def test_self_references_skipped(self) -> None:
        from contextix.linker import DocumentLinker
        from contextix.models import ContextIR, ParsedDocument, ProjectIdentity

        docs = [
            ParsedDocument(
                source="docs/adr/0001-test.md",
                content="# ADR 0001: Test\n\nSee [ADR 0001](docs/adr/0001-test.md).",
                file_type="markdown",
            ),
        ]
        context = ContextIR(project=ProjectIdentity(name="Test", description=""))
        linker = DocumentLinker()
        result = linker.link(docs, context)

        # No self-references
        assert not any(
            r.source == r.target for r in result.references
        )

    def test_adr_number_references(self) -> None:
        from contextix.linker import DocumentLinker
        from contextix.models import ContextIR, ParsedDocument, ProjectIdentity

        docs = [
            ParsedDocument(
                source="README.md",
                content="Depends on ADR 0001 being implemented.",
                file_type="markdown",
            ),
            ParsedDocument(
                source="docs/adr/0001-storage.md",
                content="# ADR 0001: Storage",
                file_type="markdown",
            ),
        ]
        context = ContextIR(project=ProjectIdentity(name="Test", description=""))
        linker = DocumentLinker()
        result = linker.link(docs, context)

        assert any("0001" in r.target for r in result.references)

    def test_external_urls_skipped(self) -> None:
        from contextix.linker import DocumentLinker
        from contextix.models import ContextIR, ParsedDocument, ProjectIdentity

        docs = [
            ParsedDocument(
                source="README.md",
                content="See [GitHub](https://github.com/example).",
                file_type="markdown",
            ),
        ]
        context = ContextIR(project=ProjectIdentity(name="Test", description=""))
        linker = DocumentLinker()
        result = linker.link(docs, context)

        assert not any("github.com" in r.target for r in result.references)


class TestContextValidator:
    def test_missing_rationale_flagged(self) -> None:
        from contextix.validator import ContextValidator
        from contextix.models import ContextIR, Decision, ProjectIdentity

        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            decisions=[
                Decision(what="Use Redis", why="", source="docs/adr/0001-test.md"),
            ],
        )
        validator = ContextValidator()
        result = validator.validate([], context)
        assert len(result.validation_issues) >= 1
        assert "rationale" in result.validation_issues[0].lower()

    def test_broken_reference_flagged(self) -> None:
        from contextix.validator import ContextValidator
        from contextix.models import (
            ContextIR,
            DocumentReference,
            ParsedDocument,
            ProjectIdentity,
        )

        docs = [
            ParsedDocument(
                source="README.md",
                content="# Test",
                file_type="markdown",
            ),
        ]
        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            references=[
                DocumentReference(
                    source="README.md",
                    target="docs/missing.md",
                    context="",
                ),
            ],
        )
        validator = ContextValidator()
        result = validator.validate(docs, context)
        assert len(result.validation_issues) >= 1
        assert "broken" in result.validation_issues[0].lower()

    def test_duplicate_goals_flagged(self) -> None:
        from contextix.validator import ContextValidator
        from contextix.models import ContextIR, ProjectIdentity

        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            goals=[
                "Preserve project understanding",
                "preserve project understanding",
            ],
        )
        validator = ContextValidator()
        result = validator.validate([], context)
        assert len(result.validation_issues) >= 1

    def test_stale_roadmap_flagged(self) -> None:
        from contextix.validator import ContextValidator
        from contextix.models import ContextIR, ProjectIdentity

        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            roadmap=["Ship v1.0 by Q1 2020"],
        )
        validator = ContextValidator()
        result = validator.validate([], context)
        assert len(result.validation_issues) >= 1
        assert "stale" in result.validation_issues[0].lower()

    def test_valid_context_no_issues(self) -> None:
        from contextix.validator import ContextValidator
        from contextix.models import ContextIR, Decision, ProjectIdentity

        context = ContextIR(
            project=ProjectIdentity(name="Test", description=""),
            decisions=[
                Decision(
                    what="Use Redis",
                    why="It is fast",
                    source="docs/adr/0001-test.md",
                ),
            ],
            goals=["Preserve context"],
            roadmap=["Ship v2.0 by Q4 2027"],
        )
        validator = ContextValidator()
        result = validator.validate([], context)
        assert result.validation_issues == []