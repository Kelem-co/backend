# Project Instructions

Backend-only Django project; the admin site is the only browser UI by default.

## Stack

- Python 3.14
- Django 6
- Django Ninja (API)
- django-allauth
- PostgreSQL (prod), Redis (cache/broker), Mailpit (dev)
- Celery for background jobs
- `uv`, Docker Compose, `just`

## Working Rules

- Consult official docs (Django / Django Ninja) before changing framework behavior.
- Keep changes small and local; follow existing patterns.
- Add tests for every feature and avoid touching unrelated code.

## Code Organization

- API: orchestration and request/response handling
- services: business logic and side-effectful operations
- selectors: queries and read-only operations

Avoid business logic in API handlers, side effects in models, and fat views.

## Validation (Local-first)

Run in order on the host development environment:

```bash
uv run ruff check --fix .
uv run mypy kelem_co_backend
uv run pytest
```

Use Docker Compose only when services (DB, cache, mail) are required for integration tests or commands.

## Dependencies

- Update `pyproject.toml` directly and pin versions.
- Do not rely solely on container-only installs (`uv add`) without committing pins to `pyproject.toml`.

## Background Jobs

- Use Celery for async or long-running work; define tasks in each app's `tasks.py`.
- Use Flower to inspect queues and running tasks when needed.

## Definition of Done

- Relevant docs consulted
- Small, focused change that follows project conventions
- Lint, type checks, and tests pass
- Tests added/updated for the change
