"""Contextix CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from contextix.config import load_settings
from contextix.core import generate_memory, initialize_project
from contextix.validator import validate_context


def main() -> int:
    parser = argparse.ArgumentParser(prog="contextix", description="Generate AI-ready project memory.")
    parser.add_argument("command", nargs="?", default="generate", choices=["generate", "init", "validate", "version"])
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if args.command == "init":
        config_path = initialize_project(root)
        print(f"Initialized Contextix: {config_path}")
        return 0

    if args.command == "version":
        print("contextix 0.1.0")
        return 0

    if args.command == "validate":
        settings = load_settings(root)
        context_file = root / settings.output_directory / "context.yaml"
        valid, errors = validate_context(context_file)
        if valid:
            print("CES Valid")
            return 0
        print("CES Invalid")
        for error in errors:
            print(f"- {error}")
        return 3

    result = generate_memory(root)
    print("Done.")
    print(f"Parsed documents: {result.document_count}")
    print(f"Generated: {result.output_directory}")
    for path in result.generated_files:
        print(f"- {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
