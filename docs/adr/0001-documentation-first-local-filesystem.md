# ADR 0001: Documentation-First and Local Filesystem MVP

Status: Accepted

Date: 2026-07-02

## Context

Contextix exists to preserve project understanding, not just inspect source code. The early project state is documentation-heavy and the roadmap requires Stage 0 to complete product philosophy, architecture, specification, roadmap, research direction, and ADRs before production implementation expands.

## Decision

The MVP starts with a documentation-first, local-filesystem implementation:

- Project memory is generated into `.context/`.
- Pipeline stages communicate through Context IR.
- The first implementation uses deterministic local parsing and heuristic analysis.
- Advanced AI providers, cloud sync, graph memory, incremental updates, and plugin execution stay outside the initial MVP path.

## Rationale

This keeps the first usable version simple, inspectable, offline-friendly, and aligned with the project manifesto. A deterministic baseline also gives future AI-assisted analysis something concrete to improve against.

## Consequences

- Early output quality is limited by heuristics.
- The architecture remains easy to test and replace stage by stage.
- Filesystem storage remains the source of truth for generated memory.
