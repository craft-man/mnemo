---
name: mnemo-dispatch-codex
description: Codex dispatch adapter for mnemo heavy workflows.
---

Use this adapter when running inside Codex.

## Inputs

- `workflow_name`
- `workflow_spec`
- `inputs_block`
- `preferred_reasoning`
- `allowed_tools`

## Behavior

1. Prefer the host's native delegation mechanism if one is available in the
   current environment.
2. If native delegation is not available, execute the workflow inline via
   `skills/dispatch/inline.md`.
3. Treat `preferred_reasoning` as a reasoning-effort hint, not as a required model.
4. Return the workflow's final report to the user.
