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
