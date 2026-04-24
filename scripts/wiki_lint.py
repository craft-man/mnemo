#!/usr/bin/env python3
"""Structural audit of a mnemo knowledge base. Python 3.10+ stdlib only.

Usage: wiki_lint.py <mnemo_dir>
"""
import argparse
import datetime
import re
import sys
from collections import defaultdict
from pathlib import Path

REQUIRED_DIRS = [
    'wiki/sources', 'wiki/entities', 'wiki/concepts',
    'wiki/synthesis', 'wiki/indexes',
]
STALE_RE = re.compile(
    r'\bcurrently\b|\brecently\b|\bas of\b|\bat the time of writing\b'
    r'|\bthe latest\b|\bupcoming\b|\bwill be\b|\bis planned\b',
    re.IGNORECASE,
)
YEAR_RE = re.compile(r'\bin (20\d{2})\b', re.IGNORECASE)
CURRENT_YEAR = datetime.date.today().year
CAP_PHRASE_RE = re.compile(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)\b')
WIKILINK_RE = re.compile(r'\[\[[^\]]+\]\]')


def parse_frontmatter(text: str) -> dict:
    fields: dict[str, str] = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return fields
    for line in lines[1:]:
        if line.strip() == '---':
            break
        if ':' in line:
            k, _, v = line.partition(':')
            fields[k.strip()] = v.strip()
    return fields


def get_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        if line.startswith('# '):
            return line[2:].strip()
    return path.stem


def extract_cap_phrases(text: str) -> list[str]:
    """Return unique Title-Case phrases (2+ words) from body, excluding wikilinks and headings."""
    lines = text.splitlines()
    in_fm = True
    body_lines = []
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == '---':
            continue
        if in_fm and line.strip() == '---':
            in_fm = False
            continue
        if in_fm:
            continue
        if line.startswith('#'):
            continue
        body_lines.append(WIKILINK_RE.sub('', line))
    # If frontmatter never closed, fall back to treating whole file as body
    if in_fm and len(lines) > 1:
        body_lines = [
            WIKILINK_RE.sub('', l) for l in lines
            if not l.startswith('#')
        ]
    return list(set(CAP_PHRASE_RE.findall('\n'.join(body_lines))))


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Structural audit of a mnemo knowledge base.'
    )
    parser.add_argument('mnemo_dir', help='Path to .mnemo/ directory')
    parser.add_argument(
        '--suggest-pages', action='store_true',
        help='Report multi-word capitalized phrases with no dedicated page (3+ occurrences)',
    )
    args = parser.parse_args()
    root = Path(args.mnemo_dir)
    issues: list[tuple[str, str, str]] = []  # (type, path, detail)

    # 1. Structure check
    for d in REQUIRED_DIRS:
        if not (root / d).exists():
            issues.append(('missing_structure', d, 'Directory missing'))
    if not (root / 'SCHEMA.md').exists():
        issues.append(('missing_structure', 'SCHEMA.md', 'File missing'))

    # 2. Build indexed_paths from index.md and shard files
    indexed_paths: set[str] = set()
    index_md = root / 'index.md'
    shard_dir = root / 'wiki' / 'indexes'
    shard_files = list(shard_dir.glob('*.md')) if shard_dir.exists() else []
    for src in [index_md] + shard_files:
        if src.exists():
            for line in src.read_text(encoding='utf-8').splitlines():
                if m := re.search(r'\]\((wiki/[^)]+\.md)\)', line):
                    indexed_paths.add(m.group(1))

    # 3. Build wiki_files set (exclude indexes/ and SCHEMA.md)
    wiki_root = root / 'wiki'
    wiki_files: set[str] = set()
    if wiki_root.exists():
        try:
            for f in wiki_root.rglob('*.md'):
                rel = f.relative_to(root).as_posix()
                if 'indexes/' not in rel and 'SCHEMA.md' not in rel:
                    wiki_files.add(rel)
        except PermissionError:
            pass

    # 4. Build processed set from log.md
    processed: set[str] = set()
    log = root / 'log.md'
    if log.exists():
        for line in log.read_text(encoding='utf-8').splitlines():
            # Skip [generated] entries — they reference wiki pages, not raw files
            if '[generated]' in line:
                continue
            # Format: "- filename.ext | ISO-timestamp"
            if m := re.match(r'-\s+(\S+)\s+\|', line):
                processed.add(m.group(1))

    # 5. Raw files
    raw_dir = root / 'raw'
    try:
        raw_files = {f.name for f in raw_dir.iterdir() if f.is_file()} if raw_dir.exists() else set()
    except PermissionError:
        raw_files = set()

    # 6. Orphans and broken links
    for wf in wiki_files:
        if wf not in indexed_paths:
            issues.append(('orphan', wf, 'Not referenced in index'))
    for ip in indexed_paths:
        if not (root / ip).exists():
            issues.append(('broken_link', ip, 'Index entry points to missing file'))

    # 7. Unprocessed raw files
    for rf in raw_files:
        if rf not in processed:
            issues.append(('unprocessed', f'raw/{rf}', 'Not yet ingested'))

    # 8–11. Per-page checks — read all pages once
    all_texts: dict[str, tuple[str, Path]] = {}
    for wf in wiki_files:
        p = root / wf
        text = p.read_text(encoding='utf-8', errors='replace')
        all_texts[wf] = (text, p)
        lines_list = text.splitlines()

        # Oversized
        if len(lines_list) > 800:
            issues.append(('oversized', wf, f'{len(lines_list)} lines (hard cap 800)'))

        # Missing frontmatter
        if not lines_list or lines_list[0].strip() != '---':
            issues.append(('missing_frontmatter', wf, 'Does not start with YAML frontmatter'))

        # Frontmatter field checks (parse once, reuse for all checks)
        fm = parse_frontmatter(text)
        if 'wiki/sources/' in wf and 'source' not in fm:
            issues.append(('missing_source_citation', wf, 'No source: field in frontmatter'))
        if fm and 'updated' not in fm:
            issues.append(('missing_updated', wf, 'No updated: field in frontmatter'))

        # Superseded without History section
        _superseded_by = fm.get('superseded_by')
        _supersedes = fm.get('supersedes')
        if _superseded_by or _supersedes:
            fm_end = text.find('---', 3)  # end of frontmatter
            body = text[fm_end + 3:] if fm_end != -1 else text
            if '## History' not in body:
                which = f'superseded_by: {_superseded_by!r}' if _superseded_by else f'supersedes: {_supersedes!r}'
                issues.append((
                    'superseded_without_history', wf,
                    f'{which} but no ## History section',
                ))

    # 10. No inbound links (entities and concepts only)
    for wf, (text, p) in all_texts.items():
        if 'wiki/entities/' not in wf and 'wiki/concepts/' not in wf:
            continue
        title = get_title(text, p)
        found = any(
            (f'[[{title}]]' in ot or f'[[{title}|' in ot)
            for owf, (ot, _) in all_texts.items()
            if owf != wf
        )
        if not found:
            issues.append(('no_inbound_links', wf, f'No [[{title}]] wikilink from any other page'))

    # 11. Stale claims
    quotes_re = re.compile(r'## Quotes.*?(?=\n##|\Z)', re.DOTALL)
    for wf, (text, _) in all_texts.items():
        body = quotes_re.sub('', text)
        for lineno, line in enumerate(body.splitlines(), 1):
            if STALE_RE.search(line):
                if m := YEAR_RE.search(line):
                    if int(m.group(1)) >= CURRENT_YEAR - 1:
                        continue
                issues.append(('stale_claim', wf, f'Line {lineno}: {line.strip()[:80]}'))
                break  # one per page

    # Report
    if not issues:
        print('## Lint Results\n\nKnowledge base is healthy — 0 issues.')
    else:
        by_type: dict[str, list] = defaultdict(list)
        for t, path, detail in issues:
            by_type[t].append((path, detail))

        print(f'## Lint Results\n\n{len(issues)} issue(s) found\n')
        for t in sorted(by_type):
            entries = by_type[t]
            print(f'### {t} ({len(entries)})\n')
            for path, detail in entries:
                print(f'- `{path}` — {detail}')
            print()

    if args.suggest_pages:
        existing_titles = {
            get_title(text, p).lower()
            for text, p in all_texts.values()
        }
        phrase_pages: dict[str, set[str]] = defaultdict(set)
        for wf, (text, _) in all_texts.items():
            for phrase in extract_cap_phrases(text):
                phrase_pages[phrase].add(wf)

        candidates = sorted(
            (
                (ph, pgs)
                for ph, pgs in phrase_pages.items()
                if len(pgs) >= 3 and ph.lower() not in existing_titles
            ),
            key=lambda x: -len(x[1]),
        )
        print('\n## Suggested New Pages\n')
        if candidates:
            for phrase, pages in candidates[:20]:
                print(f'- **{phrase}** — mentioned in {len(pages)} pages')
        else:
            print('No candidates found (no phrase appears in 3+ pages without a dedicated page).')


if __name__ == '__main__':
    main()
