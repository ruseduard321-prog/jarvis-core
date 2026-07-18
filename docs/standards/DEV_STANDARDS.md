# General Standards

- Readability over cleverness.
- Consistency over personal preference.
- Small focused modules.
- Reuse before creating new code.
- Simplicity over premature optimization.

# Naming Conventions

## Backend

- snake_case for files, folders, variables and functions.
- PascalCase for classes.
- UPPER_SNAKE_CASE for constants.

## Frontend

- PascalCase for React components.
- camelCase for variables and functions.
- kebab-case only where framework conventions require it.

## Database

- snake_case everywhere.

# Project Structure

Every new feature must respect the existing architecture.

No feature may bypass:

- API layer
- Service layer
- Repository layer

No business logic in controllers.

No database access outside repositories.

# Code Standards

- Maximum function length: around 50 lines unless justified.
- Single Responsibility Principle.
- Prefer composition over inheritance.
- Avoid global state.
- Prefer explicit code over magic.
- Every public function must have type hints.
- Remove dead code.
- No commented-out code.

# Error Handling

- Never silently ignore exceptions.
- Return meaningful error messages.
- Log unexpected errors.
- Validate every external input.
- Fail fast when assumptions are violated.

# Testing Philosophy

- New features should be testable.
- Business logic should be isolated.
- Keep components loosely coupled.
- Design for maintainability.

# Performance

- Avoid unnecessary database queries.
- Cache only when justified.
- Async where appropriate.
- Optimize after measuring.

# Code Reviews

Every pull request or AI-generated change should be reviewed for:

- correctness
- readability
- architecture compliance
- security
- maintainability

Code quality is a long-term investment.
Every line of code should make the project easier to maintain.
