# Contributing Guide

Version: 1.0 | Status: Active

---

# Purpose

This document defines how contributors participate in Contextix.

The goal is to preserve architectural consistency and long-term vision while welcoming contributions.

Every contribution should improve Contextix without increasing unnecessary complexity.

---

# Core Philosophy

Contextix values:

- **Simplicity** - Simple systems survive
- **Predictability** - Deterministic behavior
- **Maintainability** - Code quality matters
- **Documentation** - Documentation is part of implementation
- **Long-term Thinking** - Engineering over hype

---

# Before Writing Code

Determine the contribution type:

- Bug Fix
- Refactor
- Documentation
- Performance Improvement
- Research
- New Feature

Different types follow different workflows.

---

# Local Development Workflow

Before creating a pull request, contributors should install the repository hooks and run the quality checks locally:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

The repository uses GitHub Actions to run `pytest` and `ruff` on `push` and `pull_request`, ensuring tests and linting pass before merging.

---

# Contribution Workflow

```
Idea → Discussion → Design → Implementation → Testing → Documentation → Pull Request
```

---

# Pull Request Checklist

Every Pull Request should include:

- [ ] Clear description
- [ ] Related issue (if applicable)
- [ ] Updated documentation
- [ ] Tests
- [ ] No breaking changes (unless intentional)
- [ ] Follows architecture guidelines

---

# Coding Principles

- Prefer readability over cleverness
- Prefer explicit behavior over hidden magic
- Prefer composition over inheritance
- Avoid premature optimization
- Keep modules focused

---

# Documentation Requirement

Every meaningful architectural change must update the relevant documentation.

**Documentation is considered part of the implementation.**

---

# Feature Acceptance Criteria

A feature should:

1. Solve a real problem
2. Align with Contextix philosophy
3. Fit the current roadmap
4. Avoid unnecessary complexity

---

# Architectural Changes

Major architectural changes require:

```
Discussion → ADR → Review → Implementation
```

Architecture should never change silently.

---

# Research Contributions

Research should include:

- Question
- Hypothesis
- Method
- Result
- Conclusion

Research findings are valuable even if they do not become product features.

---

# Code Review Principles

Reviews should focus on:

1. Correctness
2. Architecture
3. Maintainability
4. Documentation
5. Performance

Style remains secondary.

---

# Community Values

- Respect contributors
- Assume good intentions
- Discuss ideas, not people
- Critique designs, not individuals

---

# Definition of Done

A contribution is complete when:

- [ ] Implementation is finished
- [ ] Documentation is updated
- [ ] Tests pass
- [ ] The project remains understandable

---

# Guiding Principle

A contribution should leave the project clearer than it was before.

---

# Glossary

Terminology used throughout Contextix.

| Term | Definition |
|------|------------|
| **CES** | Context Exchange Specification. The standardized format for representing project understanding. |
| **Context IR** | Intermediate Representation used internally by Contextix before exporting CES. |
| **Snapshot** | The current state of project development. Includes completed work, current tasks, next tasks, and known issues. |
| **Project Memory** | The complete structured understanding of a software project. Not source code. Knowledge about the project. |
| **Compression** | Reducing project context while preserving essential understanding. |
| **Context Fidelity** | The degree to which understanding survives compression. Research topic. |
| **Core Engine** | The central orchestration layer of Contextix. All interfaces communicate through the Core Engine. |
| **Pipeline** | The sequence of processing stages transforming raw inputs into Project Memory. |
| **Parser** | Extracts raw information from supported inputs. |
| **Analyzer** | Interprets extracted information. Produces structured project understanding. |
| **Optimizer** | Reduces redundancy while preserving meaning. |
| **Exporter** | Converts Context IR into CES-compatible outputs. |
| **ADR** | Architecture Decision Record. Documents important architectural decisions. |
| **CEP** | Context Enhancement Proposal. Future mechanism for evolving CES. |
| **Project Identity** | The long-term characteristics that define a software project. Research topic. |
| **Living Memory** | Future concept describing continuously evolving project understanding. |
