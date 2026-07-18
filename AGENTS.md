<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Jarvis Core AI Agent Guidance

This repository combines a Next.js frontend and a Python FastAPI backend. Keep instructions concise, preserve existing architecture, and prefer documented conventions.

## Key points

- Frontend: `app/` with Next.js `16.2.10`, React `19.2.4`, Tailwind CSS.
- Backend: `backend/` with FastAPI, Pydantic, service/repository layers, and `backend/main.py` entrypoint.
- Documentation: use `docs/architecture/ARCHITECTURE.md`, `docs/standards/DEV_STANDARDS.md`, `docs/standards/AI_RULES.md` rather than duplicating details.

## Build / run

- Frontend commands:
  - `npm run dev`
  - `npm run build`
  - `npm run start`
  - `npm run lint`
- Backend:
  - The backend is a Python FastAPI app in `backend/main.py`.
  - No repository-level Python CLI scripts are defined in `package.json`.

## Architecture rules

- Do not bypass the service layer.
- Keep API routes thin and focused.
- Place business logic in `backend/services/`.
- Place data access in `backend/repositories/`.
- Use `backend/schemas/` for request/response validation.
- Avoid direct database access from the frontend.
- Respect the flow: frontend → backend → AI → database.

## Coding conventions

- Backend: `snake_case` for files, folders, variables, functions; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- Frontend: `PascalCase` for React components; `camelCase` for variables and functions.
- Keep modules small and reusable.
- Prefer explicit code over magic.
- Remove dead code; do not leave large blocks commented out.

## AI-specific guidance

- Always read existing code before modifying it.
- Never invent requirements.
- Keep changes small and targeted.
- Respect existing architecture and conventions.
- Link to repo docs for deeper context.

