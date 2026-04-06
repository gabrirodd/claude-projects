"""
extract.py — extract clean text from PDFs in corpus/papers/
Writes one .txt file per paper to corpus/texts/

Usage:
  python scripts/extract.py

Requires: pdfplumber (pip install pdfplumber)
"""

import pdfplumber
from pathlib import Path

INDIR  = Path('corpus/papers')
OUTDIR = Path('corpus/texts')
OUTDIR.mkdir(parents=True, exist_ok=True)

pdfs = sorted(INDIR.glob('*.pdf'))
if not pdfs:
    print(f'No PDFs found in {INDIR}/')
    raise SystemExit(1)

print(f'Extracting {len(pdfs)} PDFs...')
for pdf_path in pdfs:
    out = OUTDIR / (pdf_path.stem + '.txt')
    if out.exists():
        print(f'  skip (exists): {pdf_path.name}')
        continue
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text(layout=True) or ''
                # Mark page boundaries so Claude can reference page numbers
                pages.append(f'[PAGE {i+1}]\n{text}')
            full = '\n\n'.join(pages)
        out.write_text(full, encoding='utf-8')
        print(f'  ok: {pdf_path.name} ({len(pdf.pages)} pages)')
    except Exception as e:
        print(f'  ERROR {pdf_path.name}: {e}')

print(f'\nDone. Texts in corpus/texts/')
