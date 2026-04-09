"""
filter.py — deduplication, filtering, and research-brief-guided scoring

Usage:
  python scripts/filter.py

Reads:
  search_config.yml         — configuration (topic, research_brief, filters)
  outputs/raw_results.json  — raw papers from search.py
  examples/                 — optional example papers (DOIs + PDFs)

Writes:
  outputs/papers.csv        — final scored and filtered collection
  outputs/papers.json       — same data in JSON (if output_format includes json)
"""

import html, json, os, csv, yaml
from pathlib import Path
from dotenv import load_dotenv
import anthropic

load_dotenv()
CONFIG = yaml.safe_load(open('search_config.yml'))
client = anthropic.Anthropic()


# ── Example loading ────────────────────────────────────────────────────────────

def load_examples():
    """Load DOI/arXiv IDs and PDF text from the examples/ folder."""
    examples = []

    # Text file: one DOI or arXiv ID per line, # lines are comments
    txt = Path('examples/example_papers.txt')
    if txt.exists():
        for line in txt.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                examples.append({'type': 'id', 'value': line})

    # PDF files: extract first 3 pages of text
    try:
        import pdfplumber
        for pdf in Path('examples').glob('*.pdf'):
            with pdfplumber.open(pdf) as p:
                text = ' '.join(
                    page.extract_text() or '' for page in p.pages[:3]
                )
                examples.append({
                    'type': 'pdf',
                    'filename': pdf.name,
                    'text': text[:3000]
                })
    except ImportError:
        print('Note: install pdfplumber for PDF example support '
              '(pip install pdfplumber)')

    return examples


# ── Profile building ───────────────────────────────────────────────────────────

def build_example_profile(examples, research_brief):
    """
    Ask Claude Sonnet to synthesise a concrete relevance profile from
    the user's example papers, anchored to their research brief.
    If no examples are provided, the brief itself becomes the profile.
    """
    if not examples:
        print('No examples found — using research_brief directly as profile.')
        return research_brief

    example_text = '\n\n'.join([
        (f'Example {i+1} [{e["type"]}]: '
         f'{e.get("value") or e.get("filename")}\n'
         f'{e.get("text", "")[:500]}')
        for i, e in enumerate(examples)
    ])

    msg = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=500,
        messages=[{'role': 'user', 'content': f"""
You are helping a researcher curate an academic paper collection.

Their research brief:
{research_brief}

They have provided these example papers as models of what they want:
{example_text}

Write a concrete 200-word relevance profile that captures:
- The key theoretical constructs and frameworks involved
- The methods and study designs that are relevant
- The populations, settings, or contexts of interest
- What would make a paper a POOR fit (wrong context, wrong method, too tangential)

This profile will be used to score hundreds of papers, so be precise and specific.
"""}]
    )
    return msg.content[0].text.strip()


# ── Paper scoring ──────────────────────────────────────────────────────────────

def score_paper(title, abstract, research_brief, profile):
    """
    Score a paper 0-10 using both the research brief and the example profile.
    Returns (score: float, reason: str).
    """
    msg = client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=100,
        messages=[{'role': 'user', 'content': f"""
You are helping curate an academic paper collection.

Researcher's brief:
{research_brief[:600]}

Relevance profile (derived from their example papers):
{profile[:600]}

Paper to evaluate:
Title: {title}
Abstract: {(abstract or '')[:800]}

Score this paper 0-10 for inclusion in the collection:
10 = perfect fit on topic, theory, AND method
7-9 = strong fit, minor gaps
4-6 = partial fit, relevant but not central
0-3 = does not belong in this collection

Respond in this exact format — no other text:
SCORE: [number]
REASON: [one sentence explaining the score]
"""}]
    )
    text = msg.content[0].text.strip()
    try:
        score = float(text.split('SCORE:')[1].split('\n')[0].strip())
        reason = text.split('REASON:')[1].strip()
        return score, reason
    except Exception:
        return 5.0, 'Could not parse score'


# ── Main pipeline ──────────────────────────────────────────────────────────────

def main():
    raw = json.loads(Path('outputs/raw_results.json').read_text())
    c = CONFIG

    # Config values
    min_score   = c.get('min_relevance', 6)
    target      = c.get('count', 100)
    journals    = [j.lower() for j in c.get('journals', [])]
    brief       = c.get('research_brief', '')

    if not brief:
        print('WARNING: research_brief is empty in search_config.yml. '
              'Scoring will be very generic.')

    # ── 1. Deduplicate by DOI > arXiv ID > title ──────────────────────────────
    seen, unique = set(), []
    for paper in raw:
        ids      = paper.get('externalIds') or {}
        doi      = ids.get('DOI', '')
        arxiv_id = ids.get('ArXiv', '') or paper.get('arxivId', '')
        key      = doi or arxiv_id or paper.get('title', '')
        if key and key.lower() not in seen:
            seen.add(key.lower())
            unique.append(paper)
    print(f'After dedup: {len(unique)} papers (from {len(raw)} raw)')

    # ── 2. Journal filter ─────────────────────────────────────────────────────
    if journals:
        unique = [
            p for p in unique
            if any(j in html.unescape(p.get('venue') or '').lower() for j in journals)
        ]
        print(f'After journal filter: {len(unique)}')

    # ── 3. Build relevance profile from examples ──────────────────────────────
    examples = load_examples() if c.get('use_examples', True) else []
    print(f'Loaded {len(examples)} example(s) from examples/')
    profile = build_example_profile(examples, brief)
    print(f'Relevance profile built ({len(profile)} chars)')

    # ── 4. Score all papers ───────────────────────────────────────────────────
    print(f'Scoring {len(unique)} papers...')
    for i, paper in enumerate(unique):
        score, reason = score_paper(
            paper.get('title', ''),
            paper.get('abstract', ''),
            brief,
            profile
        )
        paper['relevance_score'] = score
        paper['score_reason']    = reason
        if i % 10 == 0:
            print(f'  {i}/{len(unique)} scored')

    # ── 5. Filter, sort, trim ─────────────────────────────────────────────────
    filtered = [p for p in unique if p.get('relevance_score', 0) >= min_score]
    filtered.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)
    filtered = filtered[:target]
    print(f'Final: {len(filtered)} papers at score >= {min_score}')

    # ── 6. Write CSV ──────────────────────────────────────────────────────────
    fieldnames = [
        'title', 'authors', 'year', 'doi', 'arxiv_id',
        'journal', 'citations', 'relevance_score', 'score_reason',
        'abstract', 'pdf_url'
    ]
    Path('outputs').mkdir(exist_ok=True)
    with open('outputs/papers.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        for p in filtered:
            ids = p.get('externalIds') or {}
            pdf = (p.get('openAccessPdf') or {}).get('url', '')
            w.writerow({
                'title':           p.get('title', ''),
                'authors':         '; '.join(
                                       a.get('name', '') if isinstance(a, dict) else str(a)
                                       for a in (p.get('authors') or [])
                                   ),
                'year':            p.get('year', ''),
                'doi':             ids.get('DOI', ''),
                'arxiv_id':        ids.get('ArXiv', p.get('arxivId', '')),
                'journal':         p.get('venue', ''),
                'citations':       p.get('citationCount', ''),
                'relevance_score': p.get('relevance_score', ''),
                'score_reason':    p.get('score_reason', ''),
                'abstract':        (p.get('abstract') or '')[:500],
                'pdf_url':         pdf,
            })
    print('Saved: outputs/papers.csv')

    # ── 7. Write JSON (optional) ──────────────────────────────────────────────
    if 'json' in c.get('output_format', []):
        Path('outputs/papers.json').write_text(
            json.dumps(filtered, indent=2, ensure_ascii=False)
        )
        print('Saved: outputs/papers.json')


if __name__ == '__main__':
    main()