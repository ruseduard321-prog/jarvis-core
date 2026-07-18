# Architecture Overview

Jarvis is designed as a modular platform that connects a modern frontend with an API-driven backend, AI services, automation tooling, and a managed database. The system supports the first product, an English YouTube business, while providing a foundation for future businesses and products.

The platform is built with a web frontend on Next.js and React, a Python backend with FastAPI, and a Supabase-managed PostgreSQL database. Authentication is handled by Supabase Auth, automation is orchestrated through n8n, and the first AI provider is Claude.

# Core Components

## Frontend

The frontend is the user-facing interface where humans interact with Jarvis. It provides dashboards, planning surfaces, and operational controls using Next.js, React, TypeScript, and Tailwind CSS. The frontend communicates with the backend through APIs and displays state derived from the backend and database.

## Backend

The backend is the API layer and execution engine. It is responsible for serving frontend requests, coordinating with AI services, managing business logic, and enforcing validation. The backend is built with Python and FastAPI to support a clean, API-first design.

## Database

The database stores persistent operational state, user data, configuration, and system metadata. Supabase provides a managed PostgreSQL service that supports secure storage and reliable data access.

## Authentication

Authentication is managed through Supabase Auth. It handles user identity, session management, and access to protected APIs, while enabling the backend to verify user context for authorization decisions.

## Automation

Automation is orchestrated through n8n. It enables the platform to model workflows, trigger processes, and integrate external services without embedding workflow logic directly inside the frontend or backend.

## AI Layer

The AI layer is responsible for operational execution by agents. In Sprint 1, Claude is the primary provider. The architecture allows for future expansion to additional AI providers, maintaining a clear separation between the AI layer and core business logic.

# System Responsibilities

- Frontend: present information, capture user intent, and make it easy for humans to direct strategy.
- Backend: expose APIs, enforce business rules, validate inputs, and coordinate interactions between systems.
- Database: persist the platform’s state and support queryable access to operational data.
- Authentication: verify users, manage sessions, and provide identity context for authorization.
- Automation: execute predefined workflows, handle event-driven tasks, and connect actions across systems.
- AI Layer: perform operational work, execute agent tasks, and surface exceptions for human review.

# Data Flow

User → Frontend → Backend → AI → Database → Frontend

A human user interacts with the frontend. The frontend sends requests to the backend, which validates them and applies business rules. The backend may call the AI layer to execute operational work or make decisions. Results and state changes are persisted in the database. The frontend reads the updated state and presents it to the user.

# Scalability Principles

- Loose coupling: Each component is independent and communicates through defined APIs or workflow triggers.
- Modular architecture: The platform separates frontend, backend, AI, automation, and data responsibilities.
- Stateless backend: The backend treats requests independently whenever possible, relying on the database for persistent state.
- Reusable services: Core services are designed to support multiple products and business contexts.
- API-first design: The backend exposes clear APIs for the frontend and integration points.
- Separation of concerns: Presentation, business logic, data access, automation, and AI execution are distinct layers.

# Security Principles

- Authentication: All user access is authenticated through Supabase Auth.
- Authorization: The backend enforces authorization checks based on user roles and context.
- Server-side validation: The backend validates inputs and requests before processing them.
- Secrets management: Sensitive keys and credentials are kept out of source control and managed securely by hosting services.
- Least privilege: Services and integrations are granted only the permissions they need.
- HTTPS: All communication is secured over HTTPS to protect data in transit.

# Future Expansion

The architecture is intended to support future growth, including multiple AI providers, multiple products, and multiple businesses. It also anticipates adding background workers, vector database support, and event-driven patterns as the platform evolves.

- Multiple AI providers: The AI layer can integrate additional providers beyond Claude.
- Multiple products: The same core platform can operate new business lines and product types.
- Multiple businesses: Jarvis is built to support a portfolio of businesses through a shared operating system.
- Background workers: As needs grow, background processing can handle longer-running tasks and asynchronous work.
- Vector databases: Future capabilities may include vector search and embeddings for richer AI retrieval.
- Event-driven architecture: Workflow triggers and events can enable more responsive, decoupled processing.

# Repository Structure

The repository is organized to separate frontend, backend, documentation, and static assets while keeping backend concerns modular and explicit.

jarvis-core/
│
├── app/
├── backend/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   ├── agents/
│   ├── utils/
│   └── main.py
│
├── docs/
├── public/
└── ...

- backend/api/: API route definitions, request handling, and versioned endpoints.
- backend/core/: Shared business logic, application setup, and orchestration utilities.
- backend/models/: Domain and ORM models representing business entities.
- backend/services/: Service layer classes that implement business operations.
- backend/repositories/: Data access and persistence abstractions following the repository pattern.
- backend/schemas/: Pydantic schemas for request, response, and validation models.
- backend/agents/: AI agent coordination, task orchestration, and agent-specific logic.
- backend/utils/: Utility functions, helpers, and common infrastructure code.
- backend/main.py: Backend application entry point and service initialization.

# Backend Design Principles

- Async FastAPI: Use FastAPI with asynchronous endpoints to support responsive API behavior and efficient concurrency.
- API versioning (/api/v1): Maintain versioned API routes to support evolution and backward compatibility.
- Repository pattern: Separate data access from business logic through repository abstractions.
- Service layer: Encapsulate business operations in services to keep controllers thin.
- Dependency Injection: Use dependency injection to manage component wiring and improve testability.
- Pydantic validation: Validate incoming and outgoing data with Pydantic schemas.
- Structured logging: Emit structured logs for observability and easier troubleshooting.
- Environment-based configuration: Manage configuration through environment variables and deployment-specific settings.
- Type safety: Prefer typed interfaces and models for clearer code contracts.
- Small reusable modules: Keep backend modules small, focused, and reusable.

# Frontend Design Principles

- Component-based architecture: Build the UI as composable components.
- Reusable UI components: Create shared components for consistent behavior and appearance.
- Server Components where appropriate: Use server-side rendering and server components for data-driven views when feasible.
- Client Components only when needed: Restrict client-side components to interactive or stateful UI.
- API-driven UI: Drive the frontend from backend APIs and data contracts.
- Strong typing: Use TypeScript to enforce type safety across the UI.
- Clean folder organization: Organize frontend code clearly to reflect pages, components, and shared utilities.
