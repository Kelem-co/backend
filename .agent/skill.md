---
name: kelem-co-backend
description: Guidance for working on the Django/Ninja backend: workflow, testing, dependencies, and background jobs.
---

# Kelem.co Backend Agent Guidance

Use this file when making changes to the backend. It captures the project's conventions, validation steps, and preferred workflows so agents and contributors can move quickly and consistently.

## Project Shape

- Python 3.14, Django 6
- Django Ninja for the API layer
- django-allauth for authentication
- PostgreSQL (production), Redis (cache/broker), Mailpit (dev)
- `uv` for local Python tooling and dependency management

## Workflow Rules

1. Inspect nearest implementation before adding new behavior.
2. Consult the official docs (Django / Django Ninja) for framework-level behavior.
3. Make the smallest coherent change that solves the task.
4. Add tests in the same feature slice; run lint/type/tests locally.

## Validation (Local-first)

- Run static checks on the host environment by default:

```bash
uv run ruff check --fix .
uv run mypy kelem_co_backend
uv run pytest
```

- Use Docker Compose only for service-dependent integration tests or commands that require the full stack (migrations, real DB/caching, etc.).

## Testing Guidelines

- Every feature must include tests. Prefer `pytest` and `pytest-django`.
- Use `factory_boy` when factories exist.
- For API changes, cover auth states, status codes, payload shapes, and schema where relevant.
- If touching migrations, include migration checks.

## Dependency Management

- Edit `pyproject.toml` directly to add or pin third-party packages.
- Do not rely on ephemeral container-only installs (e.g. `uv add`) without updating `pyproject.toml`.

## Background Jobs

- Use Celery for long-running or IO-bound tasks. Place tasks in the app's `tasks.py` and call them via the Celery worker.
- Use Flower for monitoring queues and task execution when needed.

## Commands & Shortcuts

- Local tooling: `uv run ...`
- Docker compose (dev): `docker compose -f docker-compose.local.yml ...`
- Docs stack: `docker compose -f docker-compose.docs.yml ...`

## Good Defaults

- Keep admin as the only browser UI unless explicitly requested.
- Avoid changing unrelated code.
- Prefer explicit tests over implicit assumptions.
- Match existing style and naming conventions.
