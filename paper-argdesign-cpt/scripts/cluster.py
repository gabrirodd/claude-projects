"""
cluster.py — aggregate all paper profiles for Claude Code's typology analysis

Reads all JSON profiles from corpus/profiles/ and writes a single
aggregated file corpus/all_profiles.json that Claude Code reads in
the clustering and synthesis steps.

Also prints a quick consistency report so Claude Code can see at a
glance what has been extracted and what might need re-checking.

Usage:
  python scripts/cluster.py
"""

import json, csv
from pathlib import Path
from collections import Counter

PROFILES_DIR = Path('corpus/profiles')
OUTDIR       = Path('outputs')
OUTDIR.mkdir(exist_ok=True)

profiles = []
for p in sorted(PROFILES_DIR.glob('*.json')):
    try:
        data = json.loads(p.read_text())
        data['_source_file'] = p.name
        profiles.append(data)
    except Exception as e:
        print(f'ERROR reading {p.name}: {e}')

if not profiles:
    print('No profiles found in corpus/profiles/')
    print('Run the analysis step first.')
    raise SystemExit(1)

print(f'\nLoaded {len(profiles)} paper profiles')
print('=' * 60)

# ── Quick consistency report ───────────────────────────────────────────────────

epistemic_counts = Counter()
move_lengths     = []
has_case         = Counter()
reflexive        = Counter()
journals         = Counter()

for p in profiles:
    em = p.get('epistemic_mode', {})
    if isinstance(em, dict):
        epistemic_counts[em.get('primary', 'unknown')] += 1
    seq = p.get('move_sequence', [])
    move_lengths.append(len(seq))
    ct = p.get('case_type', {})
    has_case[ct.get('has_case', 'unknown')] += 1
    reflexive[p.get('reflexive_move', 'unknown')] += 1
    journals[p.get('journal', 'unknown')] += 1

print('\nEpistemic mode distribution:')
for mode, n in epistemic_counts.most_common():
    bar = '█' * n
    print(f'  {mode:<45} {n:>3}  {bar}')

print('\nCase usage:')
for val, n in has_case.most_common():
    print(f'  has_case={val}: {n}')

print('\nReflexive move (meta-critique of own position):')
for val, n in reflexive.most_common():
    print(f'  reflexive={val}: {n}')

print(f'\nMove sequence length: '
      f'min={min(move_lengths)} max={max(move_lengths)} '
      f'avg={sum(move_lengths)/len(move_lengths):.1f}')

print('\nJournals:')
for j, n in journals.most_common():
    print(f'  {j}: {n}')

# ── Write aggregated JSON ──────────────────────────────────────────────────────
agg_path = Path('corpus/all_profiles.json')
agg_path.write_text(json.dumps(profiles, indent=2, ensure_ascii=False))
print(f'\nAggregated profiles written to: {agg_path}')

# ── Write epistemic map CSV ────────────────────────────────────────────────────
csv_path = OUTDIR / 'epistemic_map.csv'
fieldnames = [
    'paper_id', 'title', 'author', 'year', 'journal',
    'epistemic_primary', 'epistemic_secondary',
    'empirical_evidence', 'quant_methods', 'qual_methods',
    'has_case', 'case_medium', 'case_function',
    'normative_level', 'closure_type',
    'move_count', 'reflexive_move',
    'move_sequence_summary'
]
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    w.writeheader()
    for p in profiles:
        em = p.get('epistemic_mode', {})
        ct = p.get('case_type', {})
        ns = p.get('normative_stake', {})
        seq = p.get('move_sequence', [])
        w.writerow({
            'paper_id':              p.get('paper_id', ''),
            'title':                 p.get('title', ''),
            'author':                p.get('author', ''),
            'year':                  p.get('year', ''),
            'journal':               p.get('journal', ''),
            'epistemic_primary':     em.get('primary', ''),
            'epistemic_secondary':   em.get('secondary', ''),
            'empirical_evidence':    em.get('empirical_evidence_present', ''),
            'quant_methods':         em.get('quantitative_methods', ''),
            'qual_methods':          em.get('qualitative_methods', ''),
            'has_case':              ct.get('has_case', ''),
            'case_medium':           ct.get('case_medium', ''),
            'case_function':         ct.get('case_function', ''),
            'normative_level':       ns.get('level', ''),
            'closure_type':          ns.get('closure_type', ''),
            'move_count':            len(seq),
            'reflexive_move':        p.get('reflexive_move', ''),
            'move_sequence_summary': ' → '.join(seq),
        })

print(f'Epistemic map CSV written to: {csv_path}')
print(f'\nNext step: tell Claude Code to run the clustering and typology synthesis')
print(f'Claude Code reads: corpus/all_profiles.json')
print(f'Claude Code writes: outputs/typology_report.md')
