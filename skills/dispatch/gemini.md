---
name: mnemo-dispatch-gemini
description: Gemini CLI dispatch adapter for mnemo heavy workflows.
---

Use this adapter when running inside Gemini CLI.

## Inputs

- `workflow_name`
- `workflow_spec`
- `inputs_block`
- `preferred_reasoning`
- `allowed_tools`

## Behavior

1. Use native delegation only if the host supports it clearly.
2. Otherwise, execute inline via `skills/dispatch/inline.md`.
3. Treat `preferred_reasoning` as advisory only.
4. Return the workflow's final report directly.
