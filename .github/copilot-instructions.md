# Workspace Copilot Instructions

Keep these instructions short and actionable for coding agents. Prefer linking to project docs rather than embedding long explanations.

- **Primary sources:** [AGENTS.md](../AGENTS.md), [README.md](../README.md), [pyproject.toml](../pyproject.toml), [justfile](../justfile), [docs/index.rst](../docs/index.rst).
- **Always run Django management commands from the repository root** (where `manage.py` lives).
-- Run everything inside the development container (preferred). Use `docker compose -f docker-compose.local.yml run --rm django <command>` or the `justfile` helpers.

  ```bash
  docker compose -f docker-compose.local.yml run --rm django python manage.py <command>
  docker compose -f docker-compose.local.yml run --rm django pytest
  docker compose -f docker-compose.local.yml run --rm django uv run mypy backend
  docker compose -f docker-compose.local.yml run --rm django uv run ruff check --fix .
  # or use just helpers when available:
  just manage migrate
  just up
  ```

- **Imports & structure:** use `backend.` absolute imports for in-repo modules; main app code is in `backend/`, config in `config/`, Docker assets in `compose/`, docs in `docs/`.
- **Settings:** do not put environment-specific changes in `config/settings/base.py`; use `config/settings/local.py` or `config/settings/production.py`.
- **Tests & CI:** tests run with `pytest` using `config.settings.test`. Add tests for any behavior change and keep changes small and focused.
- **Formatting & linting:** `ruff` is primary; `djlint` for templates. Note migrations are excluded from Ruff — review migrations manually when editing.
- **Background jobs:** put Celery tasks in each app's `tasks.py`. In local non-docker dev Celery runs in eager mode by default; when using docker, use the Celery service. Flower is available at `localhost:5555` when enabled; credentials come from `.envs`.
- **Dependencies:** update `pyproject.toml` when adding packages and rebuild images; do not rely on container-only installs.

If you want stricter or file-scoped rules (for example: template formatting, tests-only, or API handlers), ask and I will create a focused `*.instructions.md` file or a skill for that scope.

— End of instructions —
