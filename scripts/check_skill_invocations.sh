#!/usr/bin/env bash
# Checks that no SKILL.md file contains agent-invocation slash command syntax.
# User-facing output strings ("Run /mnemo:...") are allowed.
# Only imperative invocations directed at the agent are forbidden.

set -e

PATTERNS=(
  "invoke \`/mnemo:"
  "Invoke \`/mnemo:"
  "invoke /mnemo:"
  "Invoke /mnemo:"
)

FOUND=0
for pattern in "${PATTERNS[@]}"; do
  results=$(grep -rn "$pattern" skills/ --include="SKILL.md" 2>/dev/null || true)
  if [ -n "$results" ]; then
    echo "FAIL: found agent invocation pattern '$pattern':"
    echo "$results"
    FOUND=1
  fi
done

if [ "$FOUND" -eq 0 ]; then
  echo "OK: no agent slash-command invocations found in SKILL.md files."
fi
exit $FOUND
