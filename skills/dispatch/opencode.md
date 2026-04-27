---
name: mnemo-dispatch-opencode
description: OpenCode dispatch adapter for mnemo heavy workflows.
---

Use this adapter when running inside OpenCode.

## Inputs

- `workflow_name`
- `workflow_spec`
- `inputs_block`
- `preferred_reasoning`
- `allowed_tools`

## Behavior

1. Use host delegation if a stable mechanism exists.
2. Otherwise, use `skills/dispatch/inline.md`.
3. Keep workflow semantics unchanged.
