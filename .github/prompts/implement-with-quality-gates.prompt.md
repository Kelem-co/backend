---
name: "Implement With Quality Gates"
description: "Implement a requested change and enforce lint fix, type checking, tests, and test execution in the development container"
argument-hint: "Describe the feature or bugfix to implement"
agent: "agent"
---

Implement the requested change from chat context and the prompt argument.

Follow this workflow every time:

1. Understand the request and inspect relevant files before editing.
2. Implement the smallest correct code changes.
3. After each implementation batch, run these checks from the repository root inside the container:
   - `docker compose -f docker-compose.local.yml run --rm django uv run ruff check --fix .`
   - `docker compose -f docker-compose.local.yml run --rm django uv run mypy backend`
   - If output shows Docker entrypoint startup lines such as `wait-for-it: waiting ... for postgres:5432`, do not send any terminal input; keep waiting for the command to finish and produce real check output.
4. Add or update tests for every behavior change.
5. Run tests in the container:
   - `docker compose -f docker-compose.local.yml run --rm django pytest`
   - Treat startup logs (including `wait-for-it` messages) as non-interactive; only provide terminal input if there is an explicit prompt asking for user data.
6. If checks fail, fix the issues and rerun until passing or clearly blocked.
7. Report:
   - What changed and why
   - Files touched
   - Which commands were run and a concise result summary
   - Any blocker, risk, or follow-up needed

Use project conventions from [AGENTS.md](../AGENTS.md) and [copilot-instructions.md](../copilot-instructions.md).
