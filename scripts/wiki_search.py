#!/usr/bin/env python3
"""BM25-style wiki search. Python 3.10+ stdlib only.

Usage:
  wiki_search.py <wiki_dir> <query> [--type sources|entities|concepts|synthesis]
                 [--tag <tag>] [--since <YYYY-MM-DD>]
                 [--backlinks <title>] [--top-linked]
"""
import argparse
import re
import sys
from pathlib import Path


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
            fields[k.strip()] = v.strip().strip('"\'')
    return fields


def get_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        if line.startswith('# '):
            return line[2:].strip()
    return path.stem


def tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-z]{3,}\b', text.lower())


def bm25(query_terms: list[str], doc_tokens: list[str],
         title_tokens: list[str], tag_tokens: list[str],
         avg_dl: float, k1: float = 1.5, b: float = 0.75) -> float:
    dl = len(doc_tokens)
    freq: dict[str, int] = {}
    for t in doc_tokens:
        freq[t] = freq.get(t, 0) + 1
    score = 0.0
    # TF-normalized BM25 without IDF (corpus too small to compute document frequencies).
    # Title and tag bonuses are additive extensions, not part of standard BM25.
    for term in query_terms:
        tf = freq.get(term, 0)
        score += (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avg_dl, 1)))
        if term in title_tokens:
            score += 2.0
        if term in tag_tokens:
            score += 1.0
    return score


def snippet(text: str, terms: list[str], max_len: int = 120) -> str:
    for term in terms:
        idx = text.lower().find(term)
        if idx >= 0:
            start = max(0, idx - 60)
            return text[start:start + max_len].replace('\n', ' ').strip()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('---') and not stripped.startswith('#'):
            return stripped[:max_len]
    return ''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('wiki_dir')
    ap.add_argument('query', nargs='?', default='')
    ap.add_argument('--type', choices=['sources', 'entities', 'concepts', 'synthesis'])
    ap.add_argument('--tag')
    ap.add_argument('--since')
    ap.add_argument('--backlinks')
    ap.add_argument('--top-linked', action='store_true')
    args = ap.parse_args()

    wiki = Path(args.wiki_dir)
    if not wiki.exists():
        sys.exit(f'ERROR: wiki dir not found: {wiki}')

    subdirs = [args.type] if args.type else ['sources', 'entities', 'concepts', 'synthesis']
    pages = [p for sd in subdirs for p in (wiki / sd).glob('*.md') if (wiki / sd).exists()]

    if not pages:
        print('No pages found.')
        return

    # --- backlinks mode ---
    if args.backlinks:
        title = args.backlinks
        pat = re.compile(re.escape(f'[[{title}]]') + '|' + re.escape(f'[[{title}|'), re.IGNORECASE)
        results = []
        for p in pages:
            text = p.read_text(encoding='utf-8', errors='replace')
            if m := pat.search(text):
                start = max(0, m.start() - 80)
                snip = text[start:m.end() + 40].replace('\n', ' ')
                results.append((p.relative_to(wiki.parent), snip))
        print(f'## Pages linking to [[{title}]]: {len(results)} found\n')
        for rel, snip in results:
            print(f'- `{rel}` — *{snip[:100]}*')
        return

    # --- top-linked mode ---
    if args.top_linked:
        # Target: entities and concepts only (regardless of --type filter)
        target_pages = [
            p for sd in ['entities', 'concepts']
            for p in (wiki / sd).glob('*.md') if (wiki / sd).exists()
        ]
        # Corpus: all pages across all 4 subdirs (for counting inbound links)
        all_pages = [
            p for sd in ['sources', 'entities', 'concepts', 'synthesis']
            for p in (wiki / sd).glob('*.md') if (wiki / sd).exists()
        ]
        corpus_texts = {p: p.read_text(encoding='utf-8', errors='replace') for p in all_pages}
        counts: dict[Path, tuple[str, int]] = {}
        for p in target_pages:
            text = corpus_texts[p]
            title = get_title(text, p)
            n = sum(1 for op, ot in corpus_texts.items() if op != p and (
                f'[[{title}]]' in ot or f'[[{title}|' in ot))
            counts[p] = (title, n)
        ranked = sorted(counts.items(), key=lambda x: x[1][1], reverse=True)[:10]
        print('## Top-linked pages\n')
        for i, (_, (title, n)) in enumerate(ranked, 1):
            print(f'{i}. **[[{title}]]** — {n} inbound links')
        return

    # --- BM25 search ---
    query_terms = tokenize(args.query) if args.query else []

    candidates = []
    for p in pages:
        text = p.read_text(encoding='utf-8', errors='replace')
        fm = parse_frontmatter(text)
        if args.tag and args.tag.lower() not in fm.get('tags', '').lower():
            continue
        if args.since and fm.get('created', '') < args.since:
            continue
        candidates.append((p, text, fm, get_title(text, p)))

    print(f'## Results for "{args.query}"\n\nPages searched: {len(candidates)}\n')

    if not candidates:
        print('No pages match the filters.')
        return

    if not query_terms:
        print('### Filter matches\n')
        for p, text, fm, title in candidates[:10]:
            cat = fm.get('category', p.parent.name)
            print(f'- **[[{title}]]** — `{cat}` — *{snippet(text, [])}*')
        return

    all_tokens = [tokenize(t) for _, t, _, _ in candidates]
    avg_dl = sum(len(t) for t in all_tokens) / len(all_tokens)

    scored = []
    for (p, text, fm, title), doc_tokens in zip(candidates, all_tokens):
        s = bm25(query_terms, doc_tokens, tokenize(title), tokenize(fm.get('tags', '')), avg_dl)
        if s > 0:
            scored.append((s, p, text, fm, title))
    scored.sort(reverse=True)

    if not scored:
        print('No matches found.')
        return

    print('### BM25 matches\n')
    for s, p, text, fm, title in scored[:5]:
        cat = fm.get('category', p.parent.name)
        snip = snippet(text, query_terms)
        print(f'- **[[{title}]]** — `{cat}` — score: {s:.1f} — *{snip}*')


if __name__ == '__main__':
    main()
