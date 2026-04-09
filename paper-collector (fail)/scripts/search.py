"""
search.py — queries Semantic Scholar, arXiv, CrossRef, and OpenAlex

Usage:
  python scripts/search.py --source semantic_scholar
  python scripts/search.py --source arxiv
  python scripts/search.py --source crossref
  python scripts/search.py --source openalex
  python scripts/search.py --source all
"""
import argparse, json, os, time, yaml
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
SS_KEY   = os.getenv('SEMANTIC_SCHOLAR_API_KEY', '')
MAILTO   = os.getenv('CROSSREF_MAILTO', 'researcher@example.com')
CONFIG   = yaml.safe_load(open('search_config.yml'))


def search_semantic_scholar(topic, count, year_min, year_max, journals, min_citations):
    """Paginate Semantic Scholar Graph API until count is reached."""
    results, offset = [], 0
    headers = {'x-api-key': SS_KEY} if SS_KEY else {}
    fields = 'paperId,title,authors,year,citationCount,abstract,externalIds,venue,openAccessPdf'

    while len(results) < count:
        batch = min(100, count - len(results))
        params = {
            'query': topic,
            'fields': fields,
            'limit': batch,
            'offset': offset,
            'year': f'{year_min}-{year_max}',
            'minCitationCount': min_citations,
        }
        r = requests.get('https://api.semanticscholar.org/graph/v1/paper/search',
                         params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        batch_papers = data.get('data', [])
        if not batch_papers:
            break
        results.extend(batch_papers)
        offset += len(batch_papers)
        total = data.get('total', 0)
        print(f'  Semantic Scholar: {len(results)}/{min(count, total)} fetched')
        if offset >= total:
            break
        time.sleep(0.5)
    return results


def search_arxiv(topic, count, year_min, year_max):
    """Query arXiv via its Atom API."""
    import xml.etree.ElementTree as ET
    results, start = [], 0
    ns = 'http://www.w3.org/2005/Atom'
    while len(results) < count:
        batch = min(100, count - len(results))
        params = {
            'search_query': f'all:{topic}',
            'start': start,
            'max_results': batch,
            'sortBy': 'relevance',
        }
        r = requests.get('https://export.arxiv.org/api/query', params=params, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        entries = root.findall(f'{{{ns}}}entry')
        if not entries:
            break
        for e in entries:
            year = e.find(f'{{{ns}}}published').text[:4]
            if not (year_min <= int(year) <= year_max):
                continue
            arxiv_id = e.find(f'{{{ns}}}id').text.split('/')[-1]
            results.append({
                'source': 'arxiv',
                'arxivId': arxiv_id,
                'title': e.find(f'{{{ns}}}title').text.strip(),
                'abstract': e.find(f'{{{ns}}}summary').text.strip(),
                'year': int(year),
                'authors': [a.find(f'{{{ns}}}name').text
                            for a in e.findall(f'{{{ns}}}author')],
                'openAccessPdf': {'url': f'https://arxiv.org/pdf/{arxiv_id}'},
                'citationCount': None,
            })
        start += len(entries)
        print(f'  arXiv: {len(results)} fetched')
        time.sleep(3)
    return results


def search_crossref(count, year_min, year_max, min_citations, issns=None, topic=None):
    """
    Query CrossRef by ISSN (journal-specific) or topic keyword.

    If issns is provided, fetches works directly from those journals via
    /journals/{issn}/works — guaranteed to be from that journal.
    If topic is provided (no issns), falls back to keyword search with
    filter=from-pub-date.
    """
    results = []
    headers = {'User-Agent': f'PaperCollector/1.0 (mailto:{MAILTO})'}

    if issns:
        # Per-ISSN fetch — most reliable for journal-specific collections
        per_issn = max(1, count // len(issns))
        for issn in issns:
            fetched, cursor = [], '*'
            print(f'  CrossRef ISSN {issn}...')
            while len(fetched) < per_issn:
                batch = min(100, per_issn - len(fetched))
                params = {
                    'mailto': MAILTO,
                    'rows': batch,
                    'cursor': cursor,
                    'filter': f'from-pub-date:{year_min},until-pub-date:{year_max}',
                    'select': 'DOI,title,author,published,abstract,is-referenced-by-count,'
                              'container-title,URL,link',
                    'sort': 'is-referenced-by-count',
                    'order': 'desc',
                }
                r = requests.get(f'https://api.crossref.org/journals/{issn}/works',
                                 params=params, headers=headers, timeout=30)
                if r.status_code == 404:
                    print(f'  CrossRef: ISSN {issn} not found')
                    break
                r.raise_for_status()
                data = r.json().get('message', {})
                items = data.get('items', [])
                if not items:
                    break
                fetched.extend(items)
                cursor = data.get('next-cursor', '')
                print(f'  CrossRef ISSN {issn}: {len(fetched)} fetched')
                if not cursor:
                    break
                time.sleep(0.4)  # polite pool: ~3 req/s
            results.extend(fetched)
    else:
        # Keyword search fallback
        cursor = '*'
        while len(results) < count:
            batch = min(100, count - len(results))
            params = {
                'query': topic or '',
                'mailto': MAILTO,
                'rows': batch,
                'cursor': cursor,
                'filter': f'from-pub-date:{year_min},until-pub-date:{year_max}',
                'select': 'DOI,title,author,published,abstract,is-referenced-by-count,'
                          'container-title,URL,link',
            }
            r = requests.get('https://api.crossref.org/works',
                             params=params, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json().get('message', {})
            items = data.get('items', [])
            if not items:
                break
            results.extend(items)
            cursor = data.get('next-cursor', '')
            print(f'  CrossRef keyword: {len(results)} fetched')
            if not cursor:
                break
            time.sleep(0.4)

    # Normalise to shared schema
    normalised = []
    for p in results:
        title = (p.get('title') or [''])[0]
        authors = [
            f"{a.get('given','')} {a.get('family','')}".strip()
            for a in (p.get('author') or [])
        ]
        pub = p.get('published', {})
        parts = pub.get('date-parts', [[None]])[0]
        year = parts[0] if parts else None
        citations = p.get('is-referenced-by-count', 0) or 0
        if citations < min_citations:
            continue
        doi = p.get('DOI', '')
        # Best open-access PDF link from CrossRef 'link' array
        pdf_url = ''
        for lnk in (p.get('link') or []):
            if lnk.get('content-type') == 'application/pdf':
                pdf_url = lnk.get('URL', '')
                break
        normalised.append({
            'source': 'crossref',
            'title': title,
            'abstract': p.get('abstract', ''),
            'year': year,
            'authors': [{'name': a} for a in authors],
            'citationCount': citations,
            'venue': (p.get('container-title') or [''])[0],
            'externalIds': {'DOI': doi},
            'openAccessPdf': {'url': pdf_url} if pdf_url else None,
        })
    print(f'  CrossRef: {len(normalised)} papers after citation filter')
    return normalised


def search_openalex(count, year_min, year_max, min_citations, issns=None, topic=None):
    """
    Query OpenAlex by ISSN or keyword topic.

    OpenAlex has reliable venue/ISSN metadata — much better than
    Semantic Scholar for journal-specific queries.
    """
    results = []
    params_base = {
        'mailto': MAILTO,
        'per-page': 100,
        'sort': 'cited_by_count:desc',
        'select': 'id,doi,title,authorships,publication_year,cited_by_count,'
                  'abstract_inverted_index,primary_location,open_access',
    }

    filters = [
        f'publication_year:{year_min}-{year_max}',
        f'cited_by_count:>{max(0, min_citations - 1)}',
    ]
    if issns:
        # Use only the first ISSN — OpenAlex deduplicates by journal,
        # so both print and online ISSNs return the same set of papers
        filters.append(f'primary_location.source.issn:{issns[0]}')
    elif topic:
        params_base['search'] = topic

    params_base['filter'] = ','.join(filters)

    cursor = '*'
    while len(results) < count:
        params = {**params_base, 'cursor': cursor}
        r = requests.get('https://api.openalex.org/works',
                         params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        items = data.get('results', [])
        if not items:
            break
        results.extend(items)
        cursor = (data.get('meta') or {}).get('next_cursor', '')
        print(f'  OpenAlex: {len(results)} fetched')
        if not cursor:
            break
        time.sleep(0.2)

    # Reconstruct abstract from inverted index
    def rebuild_abstract(inv):
        if not inv:
            return ''
        tokens = [''] * (max(max(v) for v in inv.values()) + 1)
        for word, positions in inv.items():
            for pos in positions:
                tokens[pos] = word
        return ' '.join(tokens)

    normalised = []
    for p in results:
        loc = p.get('primary_location') or {}
        source = loc.get('source') or {}
        venue_name = source.get('display_name', '')
        pdf_url = loc.get('pdf_url', '') or ''
        oa = p.get('open_access') or {}
        if not pdf_url:
            pdf_url = oa.get('oa_url', '') or ''
        doi = (p.get('doi') or '').replace('https://doi.org/', '')
        authors = [
            {'name': (a.get('author') or {}).get('display_name', '')}
            for a in (p.get('authorships') or [])
        ]
        normalised.append({
            'source': 'openalex',
            'title': p.get('title', ''),
            'abstract': rebuild_abstract(p.get('abstract_inverted_index')),
            'year': p.get('publication_year'),
            'authors': authors,
            'citationCount': p.get('cited_by_count', 0),
            'venue': venue_name,
            'externalIds': {'DOI': doi},
            'openAccessPdf': {'url': pdf_url} if pdf_url else None,
        })
    print(f'  OpenAlex: {len(normalised)} papers normalised')
    return normalised


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='all',
                        choices=['semantic_scholar', 'arxiv', 'crossref',
                                 'openalex', 'all'])
    args = parser.parse_args()
    c = CONFIG
    issns  = c.get('issns', [])
    journals = c.get('journals', [])

    all_results = []

    if args.source in ('semantic_scholar', 'all') and 'semantic_scholar' in c['sources']:
        print('Querying Semantic Scholar...')
        papers = search_semantic_scholar(
            c['topic'], c['count'], c['year_min'], c['year_max'],
            journals, c.get('min_citations', 0)
        )
        all_results.extend(papers)

    if args.source in ('arxiv', 'all') and 'arxiv' in c['sources']:
        print('Querying arXiv...')
        papers = search_arxiv(c['topic'], c['count'], c['year_min'], c['year_max'])
        all_results.extend(papers)

    if args.source in ('crossref', 'all') and 'crossref' in c['sources']:
        print('Querying CrossRef...')
        papers = search_crossref(
            c['count'], c['year_min'], c['year_max'],
            c.get('min_citations', 0),
            issns=issns or None,
            topic=c.get('topic') if not issns else None,
        )
        all_results.extend(papers)

    if args.source in ('openalex', 'all') and 'openalex' in c['sources']:
        print('Querying OpenAlex...')
        papers = search_openalex(
            c['count'], c['year_min'], c['year_max'],
            c.get('min_citations', 0),
            issns=issns or None,
            topic=c.get('topic') if not issns else None,
        )
        all_results.extend(papers)

    Path('outputs').mkdir(exist_ok=True)
    out = Path('outputs/raw_results.json')
    existing = json.loads(out.read_text()) if out.exists() else []
    combined = existing + all_results
    out.write_text(json.dumps(combined, indent=2, ensure_ascii=False))
    print(f'Raw results saved: {len(combined)} papers')


if __name__ == '__main__':
    main()
