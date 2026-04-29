---
name: context
description: >
  Load minimal mnemo startup context manually for the current project. Use when
  the user runs /mnemo:context, says "Load the minimum mnemonic context for this project", or needs a fallback because startup auto-load did not happen.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:context). Other agentskills.io-compatible
  agents invoke by natural language. Optional: Python 3.10+ for the read-only
  fast path (scripts/show_session_brief.py).
metadata:
  author: mnemo contributors
  version: "0.16.5"
allowed-tools: Read Glob Bash
---

Load only the minimal startup context for `.mnemo/<project-name>/`.

This skill is strictly read-only:
- Do not write, edit, create, delete, move, or regenerate any file.
- Do not run `/mnemo:lint`, `/mnemo:ingest`, `/mnemo:query`, `/mnemo:graphify`, or any update script.
- Never read `wiki/**/*.md`, except the global profile path explicitly allowed below.
- Never load the whole wiki.

## Arguments

- No argument: load the project session brief and global user profile if present.
- `--code`: also load `graphify-out/GRAPH_REPORT.md` if present.

## Step 0 - Python fast path (optional)

1. Resolve `<project-name>` as the current directory name.
2. Use `Glob('**/scripts/show_session_brief.py')` to locate the public CLI.
3. If found at `<script_path>`, run:
   ```
   python3 <script_path> --vault .mnemo/<project-name>
   ```
   Add `--code` when the slash command argument includes `--code`.
4. If exit code is 0:
   - Read `~/.mnemo/wiki/entities/person-user.md` if it exists.
   - Reply briefly:
     ```
     Mnemo context loaded.
     Files read:
     - .mnemo/<project-name>/SESSION_BRIEF.md
     - ~/.mnemo/wiki/entities/person-user.md (if present)
     - graphify-out/GRAPH_REPORT.md (only with --code and if present)
     ```
   - Include any warnings from the script: stale brief, missing profile, or graphify report not present.
   - Stop.
5. If exit code is non-zero because `SESSION_BRIEF.md` is missing, stop and tell the user:
   ```
   SESSION_BRIEF.md not found. Regenerate with:
   python scripts/update_session_brief.py --vault .mnemo/<project-name>
   ```
   Do not regenerate it automatically.
6. If Python is unavailable or the script is not found, continue to the manual steps below.

## Manual Steps

**1. Resolve vault root** - `<project-name>` = current directory name. The vault root is `.mnemo/<project-name>/`.

**2. Check the brief** - If `.mnemo/<project-name>/SESSION_BRIEF.md` does not exist, stop:

```
SESSION_BRIEF.md not found. Regenerate with:
python scripts/update_session_brief.py --vault .mnemo/<project-name>
```

Do not create or regenerate the file.

**3. Check freshness** - Compare timestamps for `SESSION_BRIEF.md` against `index.md`, `log.md`, and `config.json`.
If any of those files is newer than `SESSION_BRIEF.md`, still read the brief, but warn:

```
Warning: SESSION_BRIEF.md may be outdated. Regenerate it with:
python scripts/update_session_brief.py --vault .mnemo/<project-name>
```

**4. Read allowed files only**

Read:
- `.mnemo/<project-name>/SESSION_BRIEF.md`
- `~/.mnemo/wiki/entities/person-user.md` if present
- `graphify-out/GRAPH_REPORT.md` only when `--code` is present and the file exists

If the global profile is absent, report `profil absent` as a warning. If `--code` is present and the graphify report is absent, report `graphify-out/GRAPH_REPORT.md not present`.

**5. Report**

Reply briefly:

```
Mnemo context loaded.
Files read:
- .mnemo/<project-name>/SESSION_BRIEF.md
- ~/.mnemo/wiki/entities/person-user.md (if present)
- graphify-out/GRAPH_REPORT.md (only with --code and if present)
Warnings:
- <brief stale | profil absent | graphify absent>
```
