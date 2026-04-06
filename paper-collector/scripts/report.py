"""report.py — generate outputs/summary.md"""
import csv, yaml
from pathlib import Path
from collections import Counter

CONFIG = yaml.safe_load(open('search_config.yml'))
rows   = list(csv.DictReader(open('outputs/papers.csv')))

years     = Counter(r['year'] for r in rows)
jrnls     = Counter(r['journal'] for r in rows if r['journal'])
top20     = sorted(rows, key=lambda r: int(r.get('citations') or 0), reverse=True)[:20]
uncertain = [r for r in rows if 5 <= float(r.get('relevance_score') or 0) < 6.5]
top_score = sorted(rows, key=lambda r: float(r.get('relevance_score') or 0), reverse=True)[:5]

# Use research_brief if present, fall back gracefully
brief = CONFIG.get('research_brief', '').strip()
brief_summary = (brief[:200] + '...') if len(brief) > 200 else brief

md = []
md.append('# Paper collection summary')
md.append('')
md.append(f'**Topic:** {CONFIG.get("topic", "—")}')

if brief_summary:
    md.append(f'**Research brief:** {brief_summary}')

if CONFIG.get('journals'):
    md.append(f'**Journal filter:** {", ".join(CONFIG["journals"])}')

md.append(f'**Total papers collected:** {len(rows)}')
md.append(f'**Year range:** {CONFIG.get("year_min", "?")}–{CONFIG.get("year_max", "?")}')
md.append(f'**Min citations:** {CONFIG.get("min_citations", "?")}  '
          f'**Min relevance score:** {CONFIG.get("min_relevance", "?")}')
md.append('')

# ── Year distribution ──────────────────────────────────────────────────────────
md.append('## Year distribution')
for y in sorted(years):
    md.append(f'- {y}: {years[y]} papers')
md.append('')

# ── Top journals ───────────────────────────────────────────────────────────────
if jrnls:
    md.append('## Top journals')
    for j, n in jrnls.most_common(10):
        md.append(f'- {j}: {n}')
    md.append('')

# ── Top 5 by relevance score ───────────────────────────────────────────────────
md.append('## Top 5 by relevance score')
for r in top_score:
    score  = r.get('relevance_score', '?')
    reason = r.get('score_reason', '').strip()
    cit    = r.get('citations', '?')
    md.append(f'- **{r["title"]}**')
    md.append(f'  Score: {score} · Citations: {cit} · {r.get("year", "?")}')
    if reason:
        md.append(f'  _{reason}_')
md.append('')

# ── Top 20 most cited ──────────────────────────────────────────────────────────
md.append('## Top 20 most cited')
for r in top20:
    md.append(
        f'- {r["title"]} — '
        f'{r.get("citations", "?")} citations, {r.get("year", "?")} '
        f'(score {r.get("relevance_score", "?")})'
    )
md.append('')

# ── Borderline papers for manual review ───────────────────────────────────────
md.append('## Papers to review (borderline relevance score 5–6.5)')
if uncertain:
    md.append(
        '_These papers scored just above or near the threshold. '
        'Check the score_reason column to decide whether to keep or exclude them. '
        'Add clear exclusions to examples/negative_examples.txt to sharpen future runs._'
    )
    md.append('')
    for r in uncertain[:15]:
        score  = r.get('relevance_score', '?')
        reason = r.get('score_reason', '').strip()
        md.append(f'- **{r["title"]}** (score {score})')
        if reason:
            md.append(f'  _{reason}_')
else:
    md.append('_No borderline papers — all collected papers scored above 6.5._')

Path('outputs/summary.md').write_text('\n'.join(md))
print(f'Report saved: outputs/summary.md ({len(rows)} papers)')