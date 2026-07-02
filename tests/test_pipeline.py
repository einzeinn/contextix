from pathlib import Path

import yaml

from contextix.core import generate_memory


def test_generate_memory_creates_context_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Demo\n\nA demo project.\n\n## Goals\n\n- Preserve context\n\n## Features\n\n- Memory export\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "0001-storage.md").write_text(
        "# ADR 0001: Storage\n\n## Decision\n\n- Use filesystem storage.\n\n## Consequences\n\n- Simple MVP.\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.txt").write_text("private notes", encoding="utf-8")
    (tmp_path / ".contextignore").write_text("notes.txt\n", encoding="utf-8")

    result = generate_memory(tmp_path)

    assert result.document_count == 2
    assert (tmp_path / ".context" / "context.yaml").exists()
    assert (tmp_path / ".context" / "snapshot.json").exists()
    assert (tmp_path / ".context" / "metadata.json").exists()

    context = yaml.safe_load((tmp_path / ".context" / "context.yaml").read_text(encoding="utf-8"))
    assert context["project"]["name"] == "Demo"
    assert context["goals"] == ["Preserve context"]
    assert context["features"] == ["Memory export"]
    # Decisions are now structured: list of {what, why, alternatives, source}
    assert len(context["decisions"]) == 1
    assert context["decisions"][0]["what"] == "Use filesystem storage."
    assert "notes.txt" not in context["documentation"]


def test_generate_memory_respects_parser_config(tmp_path: Path) -> None:
    (tmp_path / "contextix.yaml").write_text(
        "parser:\n  markdown: false\n  text: true\n  repo: false\n  pdf: false\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")

    result = generate_memory(tmp_path)

    assert result.document_count == 1


class TestFullPipelineIntegration:
    """End-to-end tests: raw files → .context/ output."""

    def test_all_output_files_generated(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text(
            "# Test\n\nA test project.\n\n## Goals\n\n- Goal 1\n",
            encoding="utf-8",
        )
        result = generate_memory(tmp_path)

        assert result.document_count >= 1
        context_dir = tmp_path / ".context"
        assert (context_dir / "bootstrap.md").exists()
        assert (context_dir / "summary.md").exists()
        assert (context_dir / "architecture.md").exists()
        assert (context_dir / "handoff.md").exists()
        assert (context_dir / "context.yaml").exists()
        assert (context_dir / "snapshot.json").exists()
        assert (context_dir / "metadata.json").exists()

    def test_adr_with_rationale_paired(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("# Test\n\nTest project.\n", encoding="utf-8")
        (tmp_path / "docs" / "adr").mkdir(parents=True)
        (tmp_path / "docs" / "adr" / "0001-cache.md").write_text(
            "# ADR 0001: Cache\n\n"
            "## Decision\n\n- Use Redis for caching.\n\n"
            "## Rationale\n\nRedis is fast and simple.\n\n"
            "## Alternatives\n\n- Memcached (rejected: less features)\n",
            encoding="utf-8",
        )

        generate_memory(tmp_path)
        context = yaml.safe_load(
            (tmp_path / ".context" / "context.yaml").read_text(encoding="utf-8")
        )

        decisions = context["decisions"]
        assert len(decisions) >= 1
        assert decisions[0]["what"] == "Use Redis for caching."
        assert decisions[0]["why"] == "Redis is fast and simple."

    def test_bootstrap_contains_key_info(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text(
            "# Demo\n\nA demo project.\n\n## Goals\n\n- Preserve context\n",
            encoding="utf-8",
        )
        (tmp_path / "docs" / "adr").mkdir(parents=True)
        (tmp_path / "docs" / "adr" / "0001-test.md").write_text(
            "# ADR 0001\n\n## Decision\n\n- Use filesystem.\n\n## Rationale\n\nSimple.\n",
            encoding="utf-8",
        )

        generate_memory(tmp_path)
        bootstrap = (tmp_path / ".context" / "bootstrap.md").read_text(encoding="utf-8")

        assert "Demo" in bootstrap
        assert "demo project" in bootstrap
        assert "Use filesystem" in bootstrap

    def test_references_between_docs(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text(
            "# Test\n\nSee [architecture](docs/architecture.md).\n",
            encoding="utf-8",
        )
        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "architecture.md").write_text(
            "# Architecture\n\nPipeline design.\n",
            encoding="utf-8",
        )

        generate_memory(tmp_path)
        context = yaml.safe_load(
            (tmp_path / ".context" / "context.yaml").read_text(encoding="utf-8")
        )

        refs = context.get("references", [])
        assert any(r["target"] == "docs/architecture.md" for r in refs)

    def test_validation_issues_for_missing_rationale(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("# Test\n\nTest.\n", encoding="utf-8")
        (tmp_path / "docs" / "adr").mkdir(parents=True)
        (tmp_path / "docs" / "adr" / "0001-no-rationale.md").write_text(
            "# ADR 0001\n\n## Decision\n\n- Use something.\n",
            encoding="utf-8",
        )

        generate_memory(tmp_path)
        context = yaml.safe_load(
            (tmp_path / ".context" / "context.yaml").read_text(encoding="utf-8")
        )

        issues = context.get("validation_issues", [])
        assert any("rationale" in i.lower() for i in issues)

    def test_output_deterministic(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("# Test\n\nTest project.\n", encoding="utf-8")

        result1 = generate_memory(tmp_path)
        result2 = generate_memory(tmp_path)

        assert result1.document_count == result2.document_count

        ctx1 = yaml.safe_load((tmp_path / ".context" / "context.yaml").read_text(encoding="utf-8"))
        # Run again — output must be identical
        generate_memory(tmp_path)
        ctx2 = yaml.safe_load((tmp_path / ".context" / "context.yaml").read_text(encoding="utf-8"))

        assert ctx1 == ctx2
