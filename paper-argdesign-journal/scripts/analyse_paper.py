"""
analyse_paper.py — analyse a single paper's argument structure and epistemic mode

Claude Code calls this script for each paper in the corpus. The script reads
the extracted text, then writes a structured JSON profile to corpus/profiles/.

This script does NOT call the Anthropic API. All analysis is performed by
Claude Code reading the text directly and writing the profile using its
file tools. This script only handles file I/O and schema validation.

Usage (called by Claude Code's Bash tool):
  python scripts/analyse_paper.py --paper "ungureanu_2013"

The script:
  1. Checks corpus/texts/{paper}.txt exists
  2. Prints the full text to stdout so Claude Code can read it
  3. Waits for Claude Code to write corpus/profiles/{paper}.json
  4. Validates the JSON against the required schema
  5. Reports pass/fail

Claude Code does the actual analysis — this script is just the scaffolding.
"""

import argparse, json, sys
from pathlib import Path

TEXTS_DIR    = Path('corpus/texts')
PROFILES_DIR = Path('corpus/profiles')
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_KEYS = [
    'paper_id', 'title', 'author', 'year', 'journal',
    'opening_move', 'theoretical_positioning', 'epistemic_mode',
    'case_type', 'normative_stake', 'move_sequence',
    'reflexive_move', 'confidence_notes'
]

EPISTEMIC_MODES = [
    'fully_normative',
    'normative_with_interpretive_case',
    'normative_with_qualitative_empirical',
    'normative_with_quantitative_empirical',
    'mixed_empirical_normative',
    'primarily_empirical_qualitative',
    'primarily_empirical_quantitative',
    'purely_interpretive_hermeneutic',
]

def validate_profile(profile: dict) -> list:
    errors = []
    for key in REQUIRED_KEYS:
        if key not in profile:
            errors.append(f'Missing required key: {key}')

    em = profile.get('epistemic_mode', {})
    if isinstance(em, dict):
        primary = em.get('primary', '')
        if primary not in EPISTEMIC_MODES:
            errors.append(
                f'epistemic_mode.primary must be one of:\n  '
                + '\n  '.join(EPISTEMIC_MODES)
                + f'\n  Got: {primary!r}'
            )

    seq = profile.get('move_sequence', [])
    if not isinstance(seq, list) or len(seq) < 2:
        errors.append('move_sequence must be a list with at least 2 items')

    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--paper', required=True,
                        help='Paper stem name (filename without .txt/.pdf)')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only validate an existing profile, do not print text')
    args = parser.parse_args()

    text_path    = TEXTS_DIR    / f'{args.paper}.txt'
    profile_path = PROFILES_DIR / f'{args.paper}.json'

    # ── Validate-only mode ─────────────────────────────────────────────────────
    if args.validate_only:
        if not profile_path.exists():
            print(f'PROFILE NOT FOUND: {profile_path}')
            sys.exit(1)
        profile = json.loads(profile_path.read_text())
        errors  = validate_profile(profile)
        if errors:
            print('VALIDATION FAILED:')
            for e in errors: print(f'  - {e}')
            sys.exit(2)
        else:
            print(f'VALIDATION PASSED: {args.paper}')
            sys.exit(0)

    # ── Normal mode: print text for Claude Code to read ───────────────────────
    if not text_path.exists():
        print(f'TEXT NOT FOUND: {text_path}')
        print(f'Run: python scripts/extract.py first')
        sys.exit(1)

    if profile_path.exists():
        print(f'PROFILE EXISTS: {profile_path}')
        print('Delete it first if you want to re-analyse this paper.')
        sys.exit(0)

    # Print text to stdout — Claude Code reads this
    text = text_path.read_text(encoding='utf-8')
    print(f'=== PAPER TEXT: {args.paper} ===')
    print(f'=== LENGTH: {len(text)} chars, ~{len(text)//4} tokens ===')
    print(f'=== PROFILE TARGET: {profile_path} ===')
    print()
    print(text)
    print()
    print(f'=== END OF PAPER TEXT ===')
    print(f'Claude Code: analyse the above text and write the profile to {profile_path}')


if __name__ == '__main__':
    main()
