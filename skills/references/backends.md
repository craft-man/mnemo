# Search Backend Reference

A mnemo search backend is a command that accepts a query and returns ranked results.

## Built-in Backends

| Name | Requires | Description |
|---|---|---|
| `bm25` | Python 3.10+ | Default. BM25 keyword ranking via `scripts/wiki_search.py`. No setup. |
| `qmd` | [qmd](https://github.com/qmd-lab/qmd) installed | Hybrid BM25 + semantic vector search. Higher recall on paraphrase queries. |

## Config Format

`.mnemo/config.json` for BM25 (default):

```json
{"search_backend": "bm25"}
```

For qmd:

```json
{"search_backend": "qmd", "qmd_collection": "mnemo-wiki"}
```

## Backward Compatibility

Configs written by older versions of mnemo use `"semantic_search"` instead of `"search_backend"`. Both are supported — the query skill reads `semantic_search` as a fallback when `search_backend` is absent. New installs always write `search_backend`.

To migrate, rename `"semantic_search"` to `"search_backend"` in `.mnemo/config.json`. No other changes needed.

## Adding a Custom Backend

1. **Implement the command interface** — your backend must:
   - Accept at minimum a query string as argument
   - Print results to stdout
   - Exit 0 on success, non-zero on failure (triggers BM25 fallback)
   - Note: `$ARGUMENTS` includes raw modifiers (`tag:redis`, `since:2026-01-01`, etc.). If your backend doesn't handle them, Step 0b re-runs the search and applies filters post-hoc.

2. **Register in `.mnemo/config.json`**:
   ```json
   {"search_backend": "my-backend"}
   ```

3. **Add a dispatch case in `skills/query/SKILL.md` Step 0**, between the `"qmd"` case and the "Any other value" fallback:
   ```
   - **`"my-backend"`** — run: `my-backend-cli query "$ARGUMENTS"`
     If exit code is 0: present results directly and **stop** — skip steps 0b through 8.
     If exit code is non-zero or backend is unavailable: warn and fall through to Step 0b.
   ```
