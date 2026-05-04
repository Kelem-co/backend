# Agent Instructions

This repository is a Cookiecutter Django project. Before making broad changes, use the existing docs as the source of truth: [README.md](README.md), [pyproject.toml](pyproject.toml), and [justfile](justfile).

- Run Django commands inside container from the repository root where `manage.py` lives.
- Use `backend.` absolute imports for in-repo Python modules.
- Keep environment-specific settings in `config/settings/local.py` or `config/settings/production.py`; avoid putting those changes in `config/settings/base.py`.
- The main app code lives in `backend/`, project wiring lives in `config/`, docs live in `docs/`, and Docker assets live in `compose/`.
- Tests use `pytest` with `config.settings.test`, linting and formatting use `ruff`, type checking uses `mypy`, and template formatting uses `djlint`.
- Migrations are excluded from Ruff checks, so review them directly when needed.
- When editing templates or docs, keep formatting compatible with the existing Django and Sphinx tooling.

## Project instructions (concise)

- Stack: Python 3.14, Django 6, Django Ninja, django-allauth, PostgreSQL (prod), Redis (cache/broker), Mailpit (dev), Celery for background jobs.

- Docker / Compose: prefer using `docker compose -f docker-compose.local.yml` or the provided `justfile` (`just manage`, `just up`, `just build`). See Cookiecutter-Django docs: https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally-docker.html

- Canonical commands (container-first):

	- Management commands: `docker compose -f docker-compose.local.yml run --rm django python manage.py <command>` or `just manage <command>`
	- Tests: `docker compose -f docker-compose.local.yml run --rm django pytest`
	- Type checking: `docker compose -f docker-compose.local.yml run --rm django uv run mypy backend`
	- Lint & format: `docker compose -f docker-compose.local.yml run --rm django uv run ruff check --fix .` (or use a `just` helper)

- Adding packages: update `pyproject.toml` and rebuild images (don't only install inside containers).

## Background jobs

- Use Celery for async/long-running work; put tasks in each app's `tasks.py`.
- Local development runs Celery in eager mode when not using Docker (see `CELERY_TASK_ALWAYS_EAGER` in `config/settings/local.py`).
- Flower is available in the local Compose stack at `localhost:5555` when enabled; credentials are controlled via `.envs` entries — see Cookiecutter-Django docs (search "Celery Flower").

## Quick links

- Getting up & running with Docker: https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally-docker.html
- Testing guide (pytest/coverage): https://cookiecutter-django.readthedocs.io/en/latest/4-guides/testing.html
- Linters & formatting guidance: https://cookiecutter-django.readthedocs.io/en/latest/4-guides/linters.html
