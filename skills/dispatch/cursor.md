---
name: mnemo-dispatch-cursor
description: Cursor dispatch adapter for mnemo heavy workflows.
---

Use this adapter when running inside Cursor.

## Inputs

- `workflow_name`
- `workflow_spec`
- `inputs_block`
- `preferred_reasoning`
- `allowed_tools`

## Behavior

1. If the host exposes a reliable agent delegation mechanism, use it.
2. Otherwise, execute the workflow inline via `skills/dispatch/inline.md`.
3. Preserve all confirmation steps and final report formatting.
