# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Paper writer — integrated writing environment

## File structure
- paper.md          → main manuscript (edit directly)
- sections/         → individual section files if working modularly
- references.bib    → exported live from Zotero (do not edit manually)
- chicago.csl       → citation style (or apa.csl, mla.csl — specify)
- output/           → Pandoc-generated .docx and .pdf

## Citation conventions
- All citations use Better BibTeX keys: [@AuthorYear] or [@Author2023a]
- Never invent citation keys — only use keys confirmed in references.bib
- Before inserting a new citation, check references.bib first
- If a key is missing, flag it: [MISSING: Author Year] and note to add in Zotero

## Editing rules
- When editing paper.md, always read the target section first before writing
- Make surgical edits — do not rewrite sections unless explicitly asked
- Preserve my voice: do not homogenise phrasing or impose academic boilerplate
- When adding a paragraph, specify exactly where it goes (after which sentence)
- Track all changes in ./changes-log.md with format: `YYYY-MM-DD | section | what changed`
- sections/ is for modular drafting only — the canonical source is always paper.md

## Pandoc export command
Run this to produce Word output:
pandoc paper.md \
  --bibliography=references.bib \
  --csl=chicago.csl \
  --reference-doc=template.docx \
  -o output/paper.docx

For PDF:
pandoc paper.md \
  --bibliography=references.bib \
  --csl=chicago.csl \
  --pdf-engine=xelatex \
  -o output/paper.pdf

## Citation integrity check
Before any export, extract all citation keys from paper.md and verify each exists in references.bib:

```bash
grep -oP '(?<=\[@)[^\]]+' paper.md | sort -u
```

Cross-reference with keys in references.bib. Flag any missing as `[MISSING: key]`.

## Importing from paper-manager
Notes from paper-manager live at /Users/Gabri/Desktop/claude/working_environment/paper-manager/notes/
When drafting a section, I may ask you to pull summaries from there.
Do not copy them verbatim — synthesise and integrate with citation keys.

## What I never want
- No unsolicited restructuring of my argument
- No adding hedging language I didn't ask for
- No changing citation keys
- No rewriting my conclusions