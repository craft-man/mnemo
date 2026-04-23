#!/usr/bin/env python3
"""Size metrics for a mnemo knowledge base. Python 3.10+ stdlib only.

Usage: wiki_stats.py <mnemo_dir>
"""
import sys
from pathlib import Path

CATEGORIES = ['sources', 'entities', 'concepts', 'synthesis']


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('Usage: wiki_stats.py <mnemo_dir>')

    root = Path(sys.argv[1]).resolve()
    wiki = root / 'wiki'
    if not wiki.exists():
        sys.exit('ERROR: wiki/ not found. Run /mnemo:init first.')

    counts: dict[str, int] = {}
    all_pages: list[Path] = []
    for cat in CATEGORIES:
        d = wiki / cat
        try:
            pages = list(d.glob('*.md')) if d.exists() else []
        except OSError:
            pages = []
        counts[cat] = len(pages)
        all_pages.extend(pages)

    total_pages = sum(counts.values())

    page_lines: list[tuple[int, Path]] = []
    total_lines = 0
    for p in all_pages:
        try:
            n = p.read_text(encoding='utf-8', errors='replace').count('\n') + 1
        except PermissionError:
            continue
        total_lines += n
        page_lines.append((n, p))
    page_lines.sort(reverse=True)

    oversized = [(n, p) for n, p in page_lines if n > 400]
    critical = [(n, p) for n, p in page_lines if n > 800]

    if total_pages >= 150:
        index_status = 'sharded (or recommended)'
    elif total_pages >= 100:
        index_status = f'flat — approaching threshold ({total_pages}/150)'
    else:
        index_status = f'flat ({total_pages}/150)'

    print('## Knowledge Base Stats\n')
    print('| Category | Pages |')
    print('|---|---|')
    for cat in CATEGORIES:
        print(f'| {cat.capitalize()} | {counts[cat]} |')
    print(f'| **Total** | **{total_pages}** |\n')
    print(f'**Total lines:** {total_lines}\n')
    print('### Largest pages\n')
    if page_lines:
        for i, (n, p) in enumerate(page_lines[:5], 1):
            rel = p.relative_to(root).as_posix()
            flag = ' ⚠ critical' if n > 800 else (' ⚠ oversized' if n > 400 else '')
            print(f'{i}. `{rel}` — {n} lines{flag}')
    else:
        print('No pages found.')
    print('\n### Scaling status\n')
    print(f'- Index: {index_status}')
    print(f'- Oversized pages (>400 lines): {len(oversized) if oversized else "none"}')
    print(f'- Critical pages (>800 lines): {len(critical) if critical else "none"}')
    for n, p in critical:
        print(f'  - `{p.relative_to(root).as_posix()}` ({n} lines) — split required')


if __name__ == '__main__':
    main()
