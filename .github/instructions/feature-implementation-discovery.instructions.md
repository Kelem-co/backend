---
description: "Use when implementing features in Django or Django Ninja: review official docs first, then check project conventions and similar in-repo implementations before coding."
name: "Feature Implementation Discovery"
---

# Feature Implementation Discovery

Before writing implementation code for a new feature, do this discovery sequence first:

1. Confirm framework guidance from current docs:
   - Check Django documentation for the relevant API or pattern.
   - Check Django Ninja documentation for route/schema/request-response behavior when API code is involved.
   - Use doc tooling (for example `mcp_context7` for library docs) when available to ensure current syntax and best practices.
2. Check repository conventions:
   - Read [AGENTS.md](../../AGENTS.md) and [.github/copilot-instructions.md](../copilot-instructions.md).
   - Follow container-first command conventions and project structure rules.
3. Find a similar feature already implemented in this codebase:
   - Locate a comparable endpoint/view/form/model/task/test pattern.
   - Reuse the existing architecture and style instead of introducing a new pattern without need.
4. Only after steps 1-3, implement the smallest focused change.
5. Include tests for behavior changes and run quality checks required by the repository instructions.

If docs, conventions, and existing patterns conflict, prefer this order:

1. Repository instructions and existing architecture constraints
2. Official framework correctness
3. New pattern introduction only when justified in the final report
