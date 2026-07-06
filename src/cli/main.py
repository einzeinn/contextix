"""Contextix CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from contextix.config import load_settings
from contextix.core import generate_memory, initialize_project
from contextix.validator import validate_context


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="contextix", description="Generate AI-ready project memory."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="generate",
        choices=["generate", "init", "validate", "version"],
    )
    parser.add_argument(
        "--root", default=".", help="Project root. Defaults to current directory."
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    if args.command == "init":
        config_path = initialize_project(root)
        logger.info("Initialized Contextix: {}", config_path)
        return 0

    if args.command == "version":
        logger.info("contextix 0.1.0")
        return 0

    if args.command == "validate":
        settings = load_settings(root)
        context_file = root / settings.output_directory / "context.yaml"
        valid, errors = validate_context(context_file)
        if valid:
            logger.info("CES Valid")
            return 0
        logger.error("CES Invalid")
        for error in errors:
            logger.error("- {}", error)
        return 3

    result = generate_memory(root)
    logger.info("Done.")
    logger.info("Parsed documents: {}", result.document_count)
    logger.info("Generated: {}", result.output_directory)
    for path in result.generated_files:
        logger.info("- {}", path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
