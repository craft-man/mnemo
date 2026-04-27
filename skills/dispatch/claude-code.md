---
name: mnemo-dispatch-claude-code
description: Claude Code dispatch adapter for mnemo heavy workflows.
---

Use this adapter when the current host exposes a native sub-agent or Agent tool.

## Inputs

- `workflow_name`
- `workflow_spec`
- `inputs_block`
- `preferred_reasoning`
- `allowed_tools`

## Behavior

1. Assemble the prompt as `workflow_spec` followed by `inputs_block`.
2. If native sub-agent delegation is available:
   - delegate the workflow
   - map `preferred_reasoning` to the host's preferred model or effort
   - pass the requested `allowed_tools`
   - wait for completion
   - relay the final report
3. If delegation is unavailable, blocked, or ambiguous, use `skills/dispatch/inline.md`.

## Reasoning Hint Mapping

- `heavy` → higher-capability reasoning path
- `balanced` → standard synthesis path

The exact host mapping is advisory.
