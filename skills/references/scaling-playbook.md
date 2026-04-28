# Scaling Playbook

## Thresholds at a Glance

| Page count | Status | Action |
|---|---|---|
| < 50 | Flat | `index.md` is sufficient. No structural changes needed. |
| 50–99 | Growing | Start using `tags:` frontmatter for filtering. Review SCHEMA.md. |
| 100–149 | Approaching shard | Run lint monthly. Check for orphans and bloated pages. |
| ≥ 150 | Shard required | Split index into per-category shards in `wiki/indexes/`. |
| ≥ 300 | Search backend review | qmd recommended. BM25 remains a simple fallback, but query quality and latency degrade as the wiki grows. |
| ≥ 500 | Lint weekly | Run structural lint after every 5 ingests. Semantic lint weekly. |
| ≥ 1000 | Consider database | Markdown portability starts to trade off against query latency. |

---

## Index Sharding (≥ 150 pages)

When total wiki pages exceed 150:

1. `index.md` becomes a master TOC with links to shards:
   ```markdown
   - [Sources Index](wiki/indexes/sources.md)
   - [Entities Index](wiki/indexes/entities.md)
   - [Concepts Index](wiki/indexes/concepts.md)
   - [Synthesis Index](wiki/indexes/synthesis.md)
   ```
2. Each new page is appended to its category shard, not to `index.md`.
3. Queries read the relevant shard (or all shards if no `category:` filter).

---

## Search Backend Scaling

BM25 is the zero-dependency fallback. It is useful for small wikis and offline portability, but the stdlib implementation is intentionally simple and should not be treated as a full search engine.

Use qmd when the wiki becomes medium-sized or search quality matters:

- < 100 pages: BM25 is usually fine.
- 100-299 pages: qmd recommended if queries are frequent or nuanced.
- ≥ 300 pages: qmd strongly recommended; BM25 remains available as fallback.

`/mnemo:stats` reports the active backend from `config.json` and warns when a large wiki is still on BM25.

---

## Page Size Limits

- **Soft cap — 400 lines**: warn the user. Consider splitting.
- **Hard cap — 800 lines**: split into `<slug>-part-1.md` and `<slug>-part-2.md`. Update source page `## Links` to reference both parts.

Rule of thumb: if a page covers more than one distinct sub-topic, it should be two pages linked by wikilinks.

---

## Four Failure Modes

### 1. Bloated index
**Symptom**: `index.md` is hundreds of lines; queries scan the whole file.  
**Fix**: Shard the index when approaching 150 pages. Use `wiki/indexes/` category files.

### 2. Unbounded page growth
**Symptom**: entity or concept pages grow indefinitely as sources accumulate.  
**Fix**: Use surgical edits (append bullets to `## Sources` only). Cap at 800 lines hard. Split at 400 lines soft.

### 3. Vague source summaries
**Symptom**: source pages contain copy-pasted text rather than synthesis; search quality degrades.  
**Fix**: Enforce the 2–4 sentence synthesis rule. Re-ingest sources where summaries are weak.

### 4. Unreliable index
**Symptom**: index entries point to deleted or renamed files (broken links detected by lint).  
**Fix**: Run structural lint after every batch of ingests. Never delete pages without updating the index.

---

## Lint Cadence Recommendations

| Wiki size | Structural lint | Semantic lint | Gap-finding |
|---|---|---|---|
| < 100 pages | After every ingest | Monthly | Quarterly |
| 100–300 pages | After every 5 ingests | Weekly | Monthly |
| > 300 pages | Weekly | Weekly | Monthly |

- **Structural**: run `wiki_lint.py` for orphans, broken links, missing frontmatter, oversized pages.
- **Semantic**: read recently-updated hub pages; check for outdated claims.
- **Gap-finding**: run `wiki_lint.py --suggest-pages` to discover topics with no dedicated page.
