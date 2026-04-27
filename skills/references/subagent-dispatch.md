# Sub-Agent Dispatch Contract

This document defines the portable dispatch contract for mnemo heavy workflows.

It applies to:

- `skills/ingest/SKILL.md`
- `skills/query/SKILL.md`
- `skills/lint/SKILL.md`

and to the workflow specs in:

- `agents/ingestor.md`
- `agents/archivist.md`
- `agents/linter.md`

---

## Goal

Preserve the same workflow behavior across hosts with different capabilities.

Hosts may support:

- native sub-agents
- delegated background agents
- no delegation at all

mnemo must still work in all three cases.

---

## Contract

Each heavy skill must prepare the following dispatch inputs:

- `workflow_name`
- `workflow_spec`
- `inputs_block`
- `preferred_reasoning`
- `allowed_tools`

### `workflow_name`

Stable identifier for the workflow:

- `mnemo-ingestor`
- `mnemo-archivist`
- `mnemo-linter`

### `workflow_spec`

The full contents of the corresponding file in `agents/`.

### `inputs_block`

A short appended block that carries explicit runtime inputs.

Example:

```markdown
## Inputs
vault: .mnemo/<project-name>/
query: <$ARGUMENTS>
```

### `preferred_reasoning`

Portable hint for effort or model selection.

Allowed values:

- `heavy`
- `balanced`

This is a hint only. Hosts may map it to:

- a specific model
- a reasoning effort
- nothing at all

### `allowed_tools`

The tool set needed by the workflow.

---

## Required Runtime Behavior

The dispatch layer must do one of two things:

1. Use the host's native delegation mechanism.
2. Execute the workflow inline in the current agent.

Inline execution is mandatory when delegation is unavailable or unclear.

---

## Prompt Assembly

The dispatched or inline workflow prompt must be assembled as:

1. full `workflow_spec`
2. blank line
3. appended runtime `inputs_block`

The workflow spec remains the source of truth for behavior.

---

## Inline Fallback

If the host does not provide reliable sub-agent support, the adapter must:

1. read the workflow spec
2. treat it as the active instruction set
3. execute it in the current session
4. preserve all confirmation gates and stop conditions
5. preserve the final report format

Inline fallback is not a degraded mode. It is the compatibility baseline.

---

## Adapter Responsibilities

Each host adapter in `skills/dispatch/` is responsible for:

- selecting native delegation when appropriate
- otherwise selecting inline execution
- preserving explicit inputs
- preserving approval and no-write guarantees
- treating `preferred_reasoning` as advisory

Adapters must not redefine workflow semantics.

---

## Parent Skill Responsibilities

Each heavy skill should only:

1. locate the plugin root
2. read the workflow spec from `agents/`
3. choose a host adapter from `skills/dispatch/`
4. pass the dispatch inputs
5. relay the resulting report

Heavy skills should not directly hardcode a host-specific delegation API.

---

## Documentation Rule

When a host supports sub-agents, mnemo may delegate.
When a host does not, mnemo must run the same workflow inline.

Docs should describe this as:

- "sub-agent when available"
- "inline fallback otherwise"

not as a hard dependency on a single vendor tool.
