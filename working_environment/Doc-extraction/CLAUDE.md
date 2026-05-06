# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

# Doc-extraction — literal information extraction from academic documents

## Purpose
Extract relevant information from academic papers and books stored as PDFs in `/Users/Gabri/Desktop/FilPol/NRx_Tlon/Material-semiótico/pdfs` into a per-document `.md` file that can be read **before** the source as a faithful map of its arguments, concepts, and ideas.

The output is **not a summary**. It is a literal extraction that mirrors the document's own structure and wording. The user reads it to know what is in the document before opening the document itself.

---

## Core extraction principles (non-negotiable)

### 1. Do not interpret
- Do not paraphrase to "explain" what the author means.
- Do not add framing, glosses, or evaluative remarks ("the author argues compellingly that…", "this is interesting because…").
- Do not infer connections between sections that the author did not draw.
- Do not classify the paper into argumentative types or schemas.
- If something is unclear in the source, leave it as the source presents it. Do not resolve ambiguity.

### 2. Be faithful to the original wording
- Use the author's vocabulary. Keep coined terms, technical phrases, and key formulations verbatim.
- Only rearrange wording when needed to remove redundancy or excessive detail (examples piled on examples, repeated restatements). The remaining text must still be the author's phrasing, lightly compressed — not a rewrite.
- When in doubt between a literal phrase and a smoother paraphrase: choose literal.
- Quotation marks are not required for every borrowed phrase, but the registers, terms, and emphases must remain those of the source.

### 3. Respect the document's language
- Write the extraction in the **same language as the source**. A Spanish paper produces a Spanish `.md`. A French chapter produces a French `.md`. An English book produces an English `.md`.
- Do not translate quoted terms or section titles. Keep them in the original.

### 4. Mirror the document's structure
- Organise the `.md` by the document's own chapters, sections, or parts. Use the source's section titles as headings (translated only if the source provides a translation).
- Do **not** impose external templates (no IMRAD, no "puzzle/argument/conclusion" schema, no abstract-style intro).
- If the document has no explicit sections (e.g. a short essay), follow its internal divisions (introduction, development, conclusion as the author marks them) or its paragraph-level argument flow.
- Skip chapters/sections that are accessory or irrelevant to the document's content (e.g. acknowledgements, author bios, boilerplate front matter, exhaustive footnote-only sections). Do not skip a chapter merely because it is short or descriptive.

### 5. No bullet points
- Write in continuous prose. Each section of the extraction is one or more paragraphs.
- Do not convert arguments into bulleted lists. Bullets fragment reasoning and lose the connective tissue between ideas.
- Numbered lists are acceptable **only** when the source itself presents an enumerated list (e.g. "the author identifies four conditions: 1)…, 2)…"). Even then, prefer prose if the source uses prose.

### 6. Length follows content, not a target
- Do not aim for a fixed length. A dense 40-page chapter produces a long extraction; a 6-page article produces a short one.
- Do not shorten to be "concise" if doing so drops a distinct argument, concept, or move present in the source.
- Do not pad. If a section adds nothing beyond what an earlier section already said, note that briefly and move on.
- A longer document with more chapters and arguments yields a longer `.md`. This is correct, not a problem to fix.

---

## What to extract from each section

For every retained chapter/section, capture:

- **The claims the author makes in that section.** State them in the author's terms.
- **The concepts introduced or used.** When a concept is defined or coined in the section, give the definition as the author gives it.
- **The moves the author makes** (a critique of X, a distinction between Y and Z, an example used to support W) — described concretely, not labelled abstractly.
- **Names, references, and traditions invoked** when they carry argumentative weight (i.e. the author is engaging with them, not just citing in passing).
- **Empirical material** (cases, data, sites, sources) when present, in the detail the author gives.

Do **not** capture:

- Citations used purely as decoration ("as many have noted…").
- Repeated restatements of the same point across sections — extract once, note continuation if needed.
- Footnote tangents unless they carry a substantive argument.

---

## Workflow

### PDF source directory
All PDFs are in `/Users/Gabri/Desktop/FilPol/NRx_Tlon/Material-semiótico/pdfs`.

### At session start
1. List the available PDFs (`ls /Users/Gabri/Desktop/FilPol/NRx_Tlon/Material-semiótico/pdfs`).
2. Ask whether to process one file, several specified files, or all files in the directory.

### For each document
1. Derive author, year, title, and language from the filename and/or the document's own front matter.
2. Extract the full text with `pdftotext`:
   ```
   pdftotext -layout "/path/to/file.pdf" -
   ```
3. **For files larger than ~30 MB**, split first with `qpdf` or `pdftk`, then extract each chunk:
   ```
   # split into 50-page chunks
   qpdf --split-pages=50 input.pdf /tmp/chunk-%d.pdf
   # extract text from each chunk
   for f in /tmp/chunk-*.pdf; do pdftotext -layout "$f" -; done
   ```
   Process chunks sequentially and combine the extracted text before writing the extraction.
4. Identify the document's structure (table of contents, section headings, chapter breaks). If the document has a TOC, use it as the spine of the extraction.
5. Decide which sections to retain and which are accessory. When in doubt, retain.
6. Write the extraction following the principles above.
7. Save to `extractions/AuthorYear-short-title.md` (see Output conventions).

### Verification before finishing
- Re-check that no section uses bullet-point lists where the source uses prose.
- Re-check that the language matches the source.
- Re-check that no interpretive framing has slipped in ("this shows that…", "importantly…").
- Re-check that section headings come from the source, not invented.

---

## Output conventions

- Save extractions to `extractions/AuthorYear-short-title.md`.
  - `AuthorYear` = first author's surname + 4-digit year (e.g. `Foucault1975`).
  - `short-title` = 3–6 lowercase hyphenated words from the original title, in the original language.
  - Example: `Foucault1975-surveiller-et-punir.md`, `Haraway1985-cyborg-manifesto.md`.
- If the same author has multiple works in the same year, append a letter: `Author2020a`, `Author2020b`.
- Top of file: a minimal header with title, author(s), year, and source language. Nothing else (no abstract, no tags, no "type"). Then the extraction begins, organised by the document's own sections.

### File header format
```
# {Original title}

**Author(s):** {as listed in the source}
**Year:** {year}
**Language:** {source language}

---

## {First section title from the source}

{prose extraction}

## {Second section title from the source}

{prose extraction}
```

---

## What this project is NOT

- Not a summariser. The output is longer and more literal than a summary.
- Not a typology classifier. Do not assign argumentative types or move sequences.
- Not a critical review. No evaluation of the document's quality, originality, or correctness.
- Not a translation. Source language is preserved.
- Not a note-taking system with the user's own annotations — those are added by the user later, separately.

## Repository layout
- `extractions/` — output destination, one `.md` per document.
- `/Users/Gabri/Desktop/FilPol/NRx_Tlon/Material-semiótico/pdfs` — source PDFs (external, not in this repo).
- `.claude/settings.json` — tool permissions.
