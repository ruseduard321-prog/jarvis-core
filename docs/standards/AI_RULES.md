# General Principles

- Always read the existing code before modifying it.
- Never rewrite large files unnecessarily.
- Prefer improving existing code over replacing it.
- Keep changes as small as possible.
- Never invent requirements.
- Respect existing architecture.
- Ask for clarification only when absolutely necessary.

# Coding Behaviour

- One task at a time.
- One logical change per commit.
- Never introduce unused code.
- Avoid duplication.
- Keep functions small.
- Prefer readability over cleverness.

# Documentation

- Update documentation when architecture changes.
- Keep Markdown concise.
- Do not duplicate information.

# Git Rules

- Small commits.
- Clear commit messages.
- Never modify unrelated files.

# Communication Rules

- Explain decisions briefly.
- Report risks.
- Stop after completing the requested task.
- Never continue with additional work unless requested.

# Quality Rules

- Type safety.
- Error handling.
- Logging.
- Validation.
- Security by default.
- Performance awareness.

These rules are mandatory for every AI working on Jarvis.

# Architecture Rules

- Never bypass the service layer.
- Never access the database directly from the frontend.
- Business logic belongs in services.
- Data access belongs in repositories.
- API endpoints should remain thin.
- Every feature must follow the existing project architecture.
- Prefer composition over duplication.
- Reuse existing modules before creating new ones.
- Keep dependencies minimal.
- Remove dead code instead of leaving it commented.

Architecture consistency is more important than implementation speed.
