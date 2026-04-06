"""
download_pdfs.py — four-layer PDF download pipeline

Layer 1: Direct open-access URL from Semantic Scholar / arXiv metadata
Layer 2: Unpaywall — legal open-access versions (author manuscripts, repos)
Layer 3: Playwright MCP — browser automation through your institutional login
Layer 4: Sci-Hub — fallback for papers unavailable through other means

For papers that fail all four layers, generates:
  outputs/manual_downloads.csv  — pre-filled URLs sorted by citations + relevance

Features:
  - Papers sorted by citation count before downloading (most cited first)
  - Existing PDFs in any folder you specify are matched and excluded
  - Resumable: re-running never re-downloads what already exists locally

Usage:
  python scripts/download_pdfs.py [--layers 1,2,3,4] [--start-from N]
                                  [--existing-dirs /path/one /path/two]

Examples:
  # Standard run
  python scripts/download_pdfs.py

  # Exclude papers already stored in your main library folder
  python scripts/download_pdfs.py --existing-dirs ~/Documents/Papers ~/Zotero/storage

  # Open-access layers only, skip Sci-Hub
  python scripts/download_pdfs.py --layers 1,2,3

  # Resume an interrupted run from paper 23
  python scripts/download_pdfs.py --start-from 23

Security measures:
  - Random delays between requests (human-like pacing)
  - Rotating user agents
  - Per-domain rate limiting with jitter
  - Automatic backoff on 429 / 503
  - Sci-Hub DOIs never written to console or log
"""

import csv, os, time, random, json, argparse, hashlib, re
from pathlib import Path
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Configuration ──────────────────────────────────────────────────────────────

OUTDIR  = Path('outputs/pdfs')
LOGFILE = Path('outputs/download_log.json')
MANUAL  = Path('outputs/manual_downloads.csv')
MAILTO  = os.getenv('CROSSREF_MAILTO', 'researcher@example.com')

DOMAIN_DELAYS = {
    'unpaywall.org':           2.0,
    'api.semanticscholar.org': 1.0,
    'arxiv.org':               3.0,
    'default':                 4.0,
}

SCIHUB_MIRRORS = [
    'https://sci-hub.se',
    'https://sci-hub.st',
    'https://sci-hub.ru',
]

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 '
    '(KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) '
    'Gecko/20100101 Firefox/123.0',
]

OUTDIR.mkdir(parents=True, exist_ok=True)


# ── HTTP session ───────────────────────────────────────────────────────────────

def make_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET'],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

SESSION = make_session()
_last_request: dict[str, float] = {}


def polite_get(url: str, **kwargs):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    base   = DOMAIN_DELAYS.get(domain, DOMAIN_DELAYS['default'])
    since  = time.time() - _last_request.get(domain, 0)
    if since < base:
        time.sleep(base - since + random.uniform(0, base * 0.3))

    headers = kwargs.pop('headers', {})
    headers.setdefault('User-Agent', random.choice(USER_AGENTS))

    try:
        r = SESSION.get(url, headers=headers, timeout=30, **kwargs)
        _last_request[domain] = time.time()
        if r.status_code == 429:
            wait = int(r.headers.get('Retry-After', 60))
            print(f'    Rate limited — waiting {wait}s')
            time.sleep(wait)
            r = SESSION.get(url, headers=headers, timeout=30, **kwargs)
        return r
    except requests.RequestException as e:
        print(f'    Request error: {e}')
        return None


# ── Existing PDF index ─────────────────────────────────────────────────────────

def normalise_title(title: str) -> str:
    """Reduce a title to lowercase letters and digits for fuzzy matching."""
    return re.sub(r'[^a-z0-9]', '', title.lower())

def normalise_doi(doi: str) -> str:
    return doi.strip().lower().lstrip('https://doi.org/').lstrip('http://doi.org/')

def build_existing_index(existing_dirs: list) -> tuple:
    """
    Scan existing_dirs recursively for PDFs.
    Returns two sets for fast lookup:
      existing_dois   — normalised DOIs extracted from filenames / paths
      existing_titles — normalised titles extracted from filenames
    """
    existing_dois   = set()
    existing_titles = set()

    if not existing_dirs:
        return existing_dois, existing_titles

    print(f'\nScanning {len(existing_dirs)} folder(s) for existing PDFs...')
    total = 0
    for d in existing_dirs:
        p = Path(d).expanduser()
        if not p.exists():
            print(f'  Warning: folder not found — {p}')
            continue
        pdfs = list(p.rglob('*.pdf'))
        print(f'  {p}: {len(pdfs)} PDFs found')
        total += len(pdfs)
        for pdf in pdfs:
            # Extract DOI-like strings from filename
            doi_match = re.search(r'10\.\d{4,}[/_][^\s\.]+', pdf.stem)
            if doi_match:
                existing_dois.add(normalise_doi(doi_match.group()))
            # Add normalised filename as title proxy
            existing_titles.add(normalise_title(pdf.stem))

    print(f'  Total indexed: {total} existing PDFs\n')
    return existing_dois, existing_titles


def already_have(row: dict,
                 existing_dois: set,
                 existing_titles: set,
                 dest: Path) -> bool:
    """
    Return True if we already own this paper, checking:
      1. Destination file exists and is a valid PDF
      2. DOI matches something in the existing index
      3. Normalised title matches something in the existing index
    """
    if dest.exists() and is_valid_pdf(dest.read_bytes()):
        return True
    doi = normalise_doi(row.get('doi', ''))
    if doi and doi in existing_dois:
        return True
    title_norm = normalise_title(row.get('title', ''))
    if len(title_norm) > 10 and title_norm in existing_titles:
        return True
    return False


# ── Prioritisation ─────────────────────────────────────────────────────────────

def prioritise(rows: list) -> list:
    """
    Sort papers before downloading:
      Primary   — citation count descending (most cited first)
      Secondary — relevance score descending
      Tertiary  — year descending (newer first within ties)

    This ensures that if a run is interrupted, the most valuable
    papers are already saved. Highly cited papers are also more
    likely to have open-access versions (authors self-archive them).
    """
    def sort_key(r):
        citations = int(r.get('citations') or 0)
        score     = float(r.get('relevance_score') or 0)
        year      = int(r.get('year') or 0)
        return (-citations, -score, -year)

    sorted_rows = sorted(rows, key=sort_key)

    print('Papers prioritised by: citations ↓  relevance score ↓  year ↓')
    print('Top 5 in download order:')
    for i, r in enumerate(sorted_rows[:5], 1):
        cit   = r.get('citations', '?')
        score = r.get('relevance_score', '?')
        print(f'  {i}. {r.get("title","")[:58]}')
        print(f'     {cit} citations · score {score}')
    print()
    return sorted_rows


# ── Helpers ────────────────────────────────────────────────────────────────────

def is_valid_pdf(content: bytes) -> bool:
    return len(content) > 10_000 and content[:4] == b'%PDF'

def save_pdf(content: bytes, dest: Path) -> bool:
    if is_valid_pdf(content):
        dest.write_bytes(content)
        return True
    return False

def doi_to_filename(title: str, doi: str) -> str:
    slug   = ''.join(c for c in title[:50] if c.isalnum() or c in ' -_')
    slug   = slug.strip().replace(' ', '_')
    suffix = hashlib.md5((doi or title).encode()).hexdigest()[:6]
    return f'{slug}_{suffix}.pdf'

def load_log() -> dict:
    if LOGFILE.exists():
        return json.loads(LOGFILE.read_text())
    return {}

def save_log(log: dict):
    LOGFILE.write_text(json.dumps(log, indent=2))


# ── Layer 1: Direct URL ────────────────────────────────────────────────────────

def layer1_direct(row: dict, dest: Path) -> bool:
    url = row.get('pdf_url', '').strip()
    if not url:
        return False
    print(f'    L1 direct: {url[:70]}')
    r = polite_get(url)
    if r and r.status_code == 200:
        return save_pdf(r.content, dest)
    return False


# ── Layer 2: Unpaywall ─────────────────────────────────────────────────────────

def layer2_unpaywall(row: dict, dest: Path) -> bool:
    doi = row.get('doi', '').strip()
    if not doi:
        return False
    url = f'https://api.unpaywall.org/v2/{doi}?email={MAILTO}'
    print(f'    L2 Unpaywall: doi={doi}')
    r = polite_get(url)
    if not r or r.status_code != 200:
        return False
    try:
        data    = r.json()
        pdf_url = None
        best    = data.get('best_oa_location') or {}
        pdf_url = best.get('url_for_pdf') or best.get('url')
        if not pdf_url:
            for loc in (data.get('oa_locations') or []):
                pdf_url = loc.get('url_for_pdf') or loc.get('url')
                if pdf_url:
                    break
        if not pdf_url:
            return False
        print(f'    L2 found: {pdf_url[:70]}')
        r2 = polite_get(pdf_url)
        if r2 and r2.status_code == 200:
            return save_pdf(r2.content, dest)
    except Exception as e:
        print(f'    L2 error: {e}')
    return False


# ── Layer 3: Playwright MCP ────────────────────────────────────────────────────
#
# Writes instructions to outputs/playwright_queue.jsonl for processing
# by Claude Code's Playwright MCP agent in a separate step.
# Actual browser download happens when you tell Claude Code:
# "Process the Playwright download queue"

def layer3_playwright_instruction(row: dict):
    doi = row.get('doi', '').strip()
    if not doi:
        return None
    title = row.get('title', 'this paper')
    dest  = OUTDIR / doi_to_filename(title, doi)

    return (
        f"Use the browser to download the PDF for this paper:\n"
        f"Title: {title}\n"
        f"DOI URL: https://doi.org/{doi}\n"
        f"Instructions:\n"
        f"1. Navigate to https://doi.org/{doi}\n"
        f"2. Wait for the page to fully load including any institutional SSO redirect\n"
        f"3. Look for a Download PDF, Full Text PDF, or Get PDF button\n"
        f"4. Wait a random interval between 8 and 20 seconds before clicking\n"
        f"5. Click the PDF download link\n"
        f"6. Save the file to: {dest.resolve()}\n"
        f"7. If access is denied or no PDF button exists, "
        f"report: PLAYWRIGHT_FAILED for doi={doi}\n"
        f"8. If successful, report: PLAYWRIGHT_OK for doi={doi}"
    )


# ── Layer 4: Sci-Hub ───────────────────────────────────────────────────────────

def layer4_scihub(row: dict, dest: Path) -> bool:
    doi = row.get('doi', '').strip()
    if not doi:
        return False

    mirrors = SCIHUB_MIRRORS.copy()
    random.shuffle(mirrors)

    for mirror in mirrors:
        url = f'{mirror}/{doi}'
        print(f'    L4 Sci-Hub via mirror...')   # DOI not printed intentionally
        time.sleep(random.uniform(5, 12))

        r = polite_get(url)
        if not r or r.status_code not in (200, 301, 302):
            continue

        if 'pdf' in r.headers.get('Content-Type', ''):
            if save_pdf(r.content, dest):
                return True
            continue

        try:
            from html.parser import HTMLParser

            class PDFLinkParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.pdf_url = None

                def handle_starttag(self, tag, attrs):
                    attrs = dict(attrs)
                    if tag == 'iframe' and 'src' in attrs:
                        src = attrs['src']
                        if '.pdf' in src or 'pdf' in src.lower():
                            self.pdf_url = (src if src.startswith('http')
                                            else f'https:{src}')
                    if tag == 'embed' and 'src' in attrs:
                        src = attrs['src']
                        if '.pdf' in src.lower():
                            self.pdf_url = (src if src.startswith('http')
                                            else f'https:{src}')
                    if tag == 'a' and 'href' in attrs:
                        href = attrs['href']
                        if href.endswith('.pdf'):
                            self.pdf_url = (href if href.startswith('http')
                                            else f'{mirror}{href}')

            parser = PDFLinkParser()
            parser.feed(r.text)

            if parser.pdf_url:
                time.sleep(random.uniform(3, 7))
                r2 = polite_get(parser.pdf_url)
                if r2 and r2.status_code == 200:
                    if save_pdf(r2.content, dest):
                        return True
        except Exception as e:
            print(f'    L4 parse error: {e}')
            continue

    return False


# ── Manual URL collection ──────────────────────────────────────────────────────

def build_manual_urls(row: dict) -> list:
    urls  = []
    doi   = row.get('doi', '').strip()
    title = row.get('title', '').strip()

    if doi:
        urls.append(('Publisher page',
                     f'https://doi.org/{doi}'))
        urls.append(('Unpaywall page',
                     f'https://unpaywall.org/{doi}'))
        urls.append(('Open Access Button',
                     f'https://openaccessbutton.org/?id={doi}'))
    if title:
        q = title.replace(' ', '+')
        urls.append(('Google Scholar',
                     f'https://scholar.google.com/scholar?q={q}'))
        urls.append(('ResearchGate',
                     f'https://www.researchgate.net/search?q={q}'))
        urls.append(('Semantic Scholar',
                     f'https://www.semanticscholar.org/search?q={q}'))
    return urls


# ── Main ───────────────────────────────────────────────────────────────────────

def main(layers: list, start_from: int, existing_dirs: list):

    rows = list(csv.DictReader(open('outputs/papers.csv')))
    log  = load_log()

    # Always include local output folder in existing check
    all_dirs = [str(OUTDIR)] + existing_dirs
    existing_dois, existing_titles = build_existing_index(all_dirs)

    # Sort by citation count → relevance → year before downloading
    rows = prioritise(rows)

    results = {'ok': [], 'playwright': [], 'manual': [], 'skipped': []}

    print(f'Download pipeline — {len(rows)} papers, layers {layers}')
    print('─' * 60)

    for i, row in enumerate(rows):
        if i < start_from:
            continue

        title = row.get('title', 'untitled')
        doi   = row.get('doi', '')
        fname = doi_to_filename(title, doi)
        dest  = OUTDIR / fname
        cit   = row.get('citations', '?')
        score = row.get('relevance_score', '?')

        print(f'\n[{i+1}/{len(rows)}] {title[:60]}')
        print(f'  {cit} citations · score {score}')

        # ── Already owned — skip ───────────────────────────────────────────
        if already_have(row, existing_dois, existing_titles, dest):
            print('  ✓ Already have this paper — skipping')
            log[doi or title] = {'status': 'skipped_existing'}
            results['skipped'].append(row)
            if doi:
                existing_dois.add(normalise_doi(doi))
            existing_titles.add(normalise_title(title))
            continue

        downloaded = False

        # ── Layer 1 ────────────────────────────────────────────────────────
        if 1 in layers and not downloaded:
            downloaded = layer1_direct(row, dest)
            if downloaded:
                print('  ✓ Layer 1 (direct URL)')
                log[doi or title] = {'status': 'ok', 'layer': 1,
                                     'file': str(dest)}
                results['ok'].append({**row, 'download_layer': 1})

        # ── Layer 2 ────────────────────────────────────────────────────────
        if 2 in layers and not downloaded:
            downloaded = layer2_unpaywall(row, dest)
            if downloaded:
                print('  ✓ Layer 2 (Unpaywall)')
                log[doi or title] = {'status': 'ok', 'layer': 2,
                                     'file': str(dest)}
                results['ok'].append({**row, 'download_layer': 2})

        # ── Layer 3 — queue for Playwright ────────────────────────────────
        if 3 in layers and not downloaded and doi:
            instruction = layer3_playwright_instruction(row)
            if instruction:
                queue = Path('outputs/playwright_queue.jsonl')
                with open(queue, 'a') as f:
                    f.write(json.dumps({
                        'doi':         doi,
                        'title':       title,
                        'dest':        str(dest),
                        'instruction': instruction,
                        'queued_at':   datetime.now().isoformat(),
                    }) + '\n')
                print('  → Layer 3 (Playwright) queued')
                log[doi or title] = {'status': 'playwright_queued'}
                results['playwright'].append(row)
                save_log(log)
                continue   # wait for Playwright before trying L4

        # ── Layer 4 ────────────────────────────────────────────────────────
        if 4 in layers and not downloaded:
            print('  → Layer 4 (Sci-Hub)...')
            downloaded = layer4_scihub(row, dest)
            if downloaded:
                print('  ✓ Layer 4 (Sci-Hub)')
                # Deliberately omit DOI from log entry for Sci-Hub
                log[title] = {'status': 'ok', 'layer': 4, 'file': str(dest)}
                results['ok'].append({**row, 'download_layer': 4})

        # ── All layers failed ──────────────────────────────────────────────
        if not downloaded:
            print('  ✗ All layers failed — queued for manual download')
            log[doi or title] = {'status': 'manual_required'}
            results['manual'].append(row)

        # Update in-memory index so later papers in same run benefit
        if downloaded:
            if doi:
                existing_dois.add(normalise_doi(doi))
            existing_titles.add(normalise_title(title))

        save_log(log)

    # ── Manual downloads CSV ───────────────────────────────────────────────────
    # Already in citation/score order from prioritise() — no re-sort needed
    if results['manual']:
        fieldnames = [
            'priority', 'title', 'authors', 'year', 'journal',
            'doi', 'citations', 'relevance_score', 'score_reason',
            'url_1_label', 'url_1',
            'url_2_label', 'url_2',
            'url_3_label', 'url_3',
            'url_4_label', 'url_4',
            'url_5_label', 'url_5',
            'notes',
        ]
        with open(MANUAL, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            for rank, row in enumerate(results['manual'], 1):
                urls  = build_manual_urls(row)
                entry = {
                    'priority':        rank,
                    'title':           row.get('title', ''),
                    'authors':         row.get('authors', ''),
                    'year':            row.get('year', ''),
                    'journal':         row.get('journal', ''),
                    'doi':             row.get('doi', ''),
                    'citations':       row.get('citations', ''),
                    'relevance_score': row.get('relevance_score', ''),
                    'score_reason':    row.get('score_reason', ''),
                    'notes': (
                        'Try URLs in order. Open Access Button often finds '
                        'legal free versions other layers missed. '
                        'Priority 1 = most cited + most relevant.'
                    ),
                }
                for j, (label, url) in enumerate(urls[:5], 1):
                    entry[f'url_{j}_label'] = label
                    entry[f'url_{j}']       = url
                w.writerow(entry)

        print(f'\nManual list: {MANUAL} — '
              f'{len(results["manual"])} papers, sorted by citations + score')

    # ── Summary ────────────────────────────────────────────────────────────────
    total = len(rows)
    auto  = len(results['ok'])
    skip  = len(results['skipped'])
    play  = len(results['playwright'])
    man   = len(results['manual'])
    pct   = round((auto + skip) / total * 100) if total else 0

    print('\n' + '═' * 60)
    print(f'Download summary ({total} papers total):')
    print(f'  ✓ Downloaded automatically : {auto}')
    print(f'  ✓ Already had locally      : {skip}  (skipped)')
    print(f'  → Playwright queued        : {play}')
    print(f'  ✗ Manual download needed   : {man}')
    print(f'  Coverage so far            : {auto + skip}/{total} ({pct}%)')
    if play:
        print(f'\n  Next — tell Claude Code: "Process the Playwright download queue"')
    if man:
        print(f'\n  Next — open outputs/manual_downloads.csv')
        print(f'  Papers are sorted: most cited + highest relevance first.')
        print(f'  Open Access Button URL is the best first stop for each.')
    print('═' * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download PDFs for papers in outputs/papers.csv'
    )
    parser.add_argument(
        '--layers', default='1,2,3,4',
        help='Layers to use, comma-separated (default: 1,2,3,4)'
    )
    parser.add_argument(
        '--start-from', type=int, default=0,
        help='Skip first N papers — use to resume an interrupted run'
    )
    parser.add_argument(
        '--existing-dirs', nargs='*', default=[],
        metavar='DIR',
        help=(
            'Paths to folders already containing your PDFs. '
            'Papers matched by DOI or title will be skipped. '
            'Example: --existing-dirs ~/Documents/Papers ~/Zotero/storage'
        )
    )
    args   = parser.parse_args()
    layers = [int(x) for x in args.layers.split(',')]
    main(layers=layers,
         start_from=args.start_from,
         existing_dirs=args.existing_dirs)