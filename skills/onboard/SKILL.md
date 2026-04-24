---
name: onboard
description: >
  Initialize or update the global user profile in ~/.mnemo/. Use when the user
  runs /mnemo:init for the first time, when no person-user.md exists in the global
  memory tier, or when the user says "update my profile", "change my preferences",
  "who am I in mnemo", or "my role has changed".
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:onboard). Other agentskills.io-compatible
  agents invoke by natural language. No external dependencies.
metadata:
  author: mnemo contributors
  version: "0.4.0"
allowed-tools: Read Write Glob
---

Create or update the user profile at `~/.mnemo/wiki/entities/person-user.md`.

## Steps

**1. Ensure global memory tier exists** — if `~/.mnemo/wiki/entities/` does not exist, create the full global tier:
```
~/.mnemo/
├── raw/
├── wiki/
│   ├── sources/
│   ├── entities/
│   ├── concepts/
│   ├── synthesis/
│   └── indexes/
├── index.md
└── log.md
```

Write `~/.mnemo/index.md` and `~/.mnemo/log.md` with empty stubs (same format as local init) if they do not exist.

**2. Detect existing profile** — check if `~/.mnemo/wiki/entities/person-user.md` exists.

- **If it exists**: read the file, display a summary of the current profile, then ask:
  > "Your profile is already set up. Want to review and update it? [y]es / [n]o"

  If `[n]o`: stop. Report: "Profile unchanged."

  If `[y]es`: enter **update mode** — go through each section below and for each one show the current value and ask "Still correct? [y]es / [e]dit". Skip unchanged sections.

- **If it does not exist**: enter **full interview mode** — run all questions below.

**3. Interview** — ask one question at a time. Wait for the answer before asking the next.

**Q1 — Role:**
> "Which best describes your role?
> 1. Solo developer
> 2. Team lead or engineering manager
> 3. Content creator or writer
> 4. Researcher or student
> 5. Business owner
> 6. Other — describe it"

**Q2 — Technical level:**
> "How technical are you with infrastructure and tooling?
> 1. Terminal native — I live in the shell
> 2. CLI comfortable — I use the terminal regularly
> 3. Config light — I prefer GUIs but can edit config files
> 4. Non-technical — I rely on visual tools"

**Q3 — Primary language for notes and responses:**

Infer from the conversation language first. If clear, pre-fill and confirm:
> "I'll write notes and responses in **<language>**. Correct? [y]es / [other language]"

If not clear from context, ask:
> "What language should I use for notes and responses? (e.g. English, French, Spanish)"

**Q4 — Main domains of interest:**
> "What are your main domains or topics? List them — e.g. 'distributed systems, Rust, personal finance' or 'UX research, product management'"

**Q5 — Knowledge base goal:**
> "What's the primary goal for your mnemo knowledge base?
> 1. Research and literature review
> 2. Project and code documentation
> 3. Personal learning and notes
> 4. Team knowledge sharing
> 5. Other — describe it"

**Q6 — Response style preference:**
> "How do you prefer responses?
> 1. Concise — short answers, minimal explanation
> 2. Balanced — enough detail to understand, not more
> 3. Detailed — full context, edge cases included"

**4. Preview and confirm** — show the profile before writing:

```
## Your mnemo profile

Role: <answer>
Technical level: <answer>
Language: <answer>
Domains: <answer>
Goal: <answer>
Response style: <answer>

Write this profile? [y]es / [e]dit
```

If `[e]dit`: ask what to change, update inline, show again. Repeat until approved.

**5. Write `~/.mnemo/wiki/entities/person-user.md`:**

```markdown
---
title: User Profile
category: entities
tags: [user, profile]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# User Profile

## Role
<role>

## Technical Level
<technical level>

## Language
<language>

## Domains
<domains as a comma-separated list or bullet list>

## Goal
<goal>

## Response Style
<style>

## Links
```

On update, preserve the original `created` date and set `updated` to today.

**6. Report:**
> "Profile saved to `~/.mnemo/wiki/entities/person-user.md`.
> I'll use it across all your projects to tailor responses to your role and preferences."
