# Database Philosophy

The database is the single source of truth for Jarvis. All operational state, user information, product context, workflow status, and AI interactions are persisted in PostgreSQL through Supabase.

The data model should avoid duplication and use normalized relationships where appropriate. References should use stable identifiers rather than names, and timestamps should be present on records to support auditing, history, and lifecycle management. Soft deletes are used when records need to be recoverable or when deletion should preserve context for downstream processes.

Auditability is a priority: every change should be traceable, and the database should support understanding who changed what and when.

# Data Domains

## Users

The users domain represents people who access Jarvis. It includes identity, profile details, authentication metadata, and user roles.

## Organizations

Organizations represent business entities or teams that own products, workflows, and operational processes within Jarvis.

## Products

Products represent individual business offerings or ventures, such as the English YouTube business. They provide context for goals, processes, and operational work.

## Projects

Projects group work around product initiatives or business outcomes. They provide structure for planning, execution, and progress tracking.

## Tasks

Tasks represent discrete units of work or operational actions. They are the building blocks of execution and can be linked to projects, products, or workflows.

## AI Agents

AI Agents represent autonomous execution entities that perform operational tasks, make decisions, or manage interactions on behalf of the system.

## Documents

Documents represent files, plans, reference materials, and content assets that support business operations and decisions.

## Knowledge

Knowledge represents structured information, best practices, and reusable content that the platform can reference to improve execution and consistency.

## Conversations

Conversations represent interactions, dialogues, or communication threads between users, AI agents, and the system.

## Workflows

Workflows represent structured processes and automation sequences that drive task execution and business outcomes.

## Settings

Settings store configuration, feature flags, and system-level preferences that affect behavior across Jarvis.

# Design Principles

- Foreign keys: enforce relationships between domains.
- Constraints: preserve data integrity and valid state.
- Indexes: support efficient queries and lookups.
- Transactions: ensure atomic operations across related updates.
- Migrations: manage schema evolution over time in a controlled way.
- UUID primary keys: use stable, globally unique identifiers for records.
- Created/Updated timestamps: capture creation and modification times for every record.

# Security

- Row Level Security: protect data access at the row level based on user and organization context.
- Authentication integration: tie database access to Supabase authentication and identity.
- Authorization: ensure application permissions are enforced before data access.
- Sensitive data handling: minimize storage of sensitive fields, protect them appropriately, and avoid exposing them without need.

# Future Expansion

The database architecture should support future capabilities, including vector embeddings for AI retrieval, analytics for operational insight, event sourcing patterns for richer history, multi-tenant scalability, and archiving for long-term retention.

- Vector embeddings: support AI retrieval and knowledge search.
- Analytics: enable reporting and operational metrics.
- Event sourcing: preserve state changes for audit and reconstruction.
- Multi-tenant architecture: support multiple organizations and businesses with appropriate isolation.
- Archiving: retain historical data in a controlled way.

# Naming Conventions

- All tables use snake_case.
- All columns use snake_case.
- Primary keys are named id.
- Foreign keys use the referenced table name followed by _id.
- UUID is the default identifier.
- created_at and updated_at exist on every table.
- deleted_at is used only for soft-delete entities.
- Boolean fields start with is_ or has_.
- Enums should be used only when values are stable.
- Avoid nullable columns unless necessary.

These conventions are mandatory across the entire platform.
