---
name: mnemo-dispatch-inline
description: Universal inline fallback for mnemo heavy workflows.
---

Use this adapter when the current host does not expose a reliable native
sub-agent mechanism, or when the host is unknown.

## Inputs

- `workflow_name`
- `workflow_spec`
- `inputs_block`
- `preferred_reasoning`
- `allowed_tools`

## Behavior

1. Treat `workflow_spec` as the active workflow instruction set.
2. Append `inputs_block` to the end of the workflow spec.
3. Execute the resulting workflow inline in the current session.
4. Preserve every confirmation gate, stop condition, and write/no-write rule.
5. Treat `preferred_reasoning` as advisory only.
6. At the end, return the workflow's final report directly to the user.

## Notes

- Do not mention that inline fallback is a degraded mode.
- Do not attempt to emulate asynchronous waiting behavior.
- The user-facing result should match the delegated path as closely as possible.
