# Academic Paper Collector — Claude Code Instructions

## What this project does

A four-step pipeline that collects, filters, downloads, and summarises academic papers:

1. **Search** — queries Semantic Scholar and/or arXiv based on `search_config.yml`, saves `outputs/raw_results.json`
2. **Filter** — deduplicates, applies filters, builds a relevance profile from `examples/`, scores each paper 0–10 with a reason using Claude Haiku, saves `outputs/papers.csv`
3. **Download** — four-layer PDF pipeline: direct URL → Unpaywall → Playwright MCP → Sci-Hub. Generates `outputs/manual_downloads.csv` for failures
4. **Report** — generates `outputs/summary.md` with year distribution, top journals, most-cited papers, and borderline papers for manual review

---

## Running the pipeline

Always activate the venv first: `source .venv/bin/activate`

| Step | Command |
|------|---------|
| Search | `python scripts/search.py --source all` (or `semantic_scholar` / `arxiv`) |
| Filter | `python scripts/filter.py` |
| Download PDFs | `python scripts/download_pdfs.py [--layers 1,2,3,4] [--existing-dirs ~/path]` |
| Report | `python scripts/report.py` |

All scripts must be run from the repo root — they open `search_config.yml` and `outputs/` with relative paths.

---

## Editing search_config.yml — rules and decision logic

**Before every run, read `search_config.yml` and confirm settings with the user.**
If the user describes a new task, update `search_config.yml` accordingly using the rules below before running the pipeline. Always show the user the proposed config changes and ask for confirmation before saving.

### Field-by-field editing rules

**`topic`**
- Must be a real keyword query (5–10 words), not a journal name or empty string
- Passed directly to the Semantic Scholar search API — think of it as a search bar query
- If the user wants all papers from a journal regardless of topic, use broad subject terms that match the journal's scope (e.g. "social theory culture society" for Theory, Culture & Society)
- Never leave empty — the API will return noise or errors

**`research_brief`**
- Free-form text read by Claude (the filter-agent), not by a search engine — can be as long as needed
- Should describe: what the user is looking for, what they are NOT looking for, theoretical nuances, method preferences, population/context constraints
- If the user wants papers regardless of topic (journal-only search), set the brief to reward citation impact and theoretical significance rather than topical fit
- If the user has no specific angle, write a brief that matches the journal's general scope
- Never leave as `[]` or empty — `filter.py` will score everything as 5.0 with no reasoning

**`issns`**
- List of ISSNs for direct journal lookup — used by CrossRef and OpenAlex only
- When set, CrossRef and OpenAlex return only papers from that journal (100% accuracy)
- Use the print ISSN only — OpenAlex deduplicates internally, second ISSN is redundant
- When `issns` is set, remove `semantic_scholar` and `arxiv` from sources (they ignore it)
- Leave as `[]` for topic-based searches across all journals

**`journals`**
- Post-fetch string filter applied in `filter.py` — unreliable for most journals (see Lessons)
- Leave as `[]` when using `issns` — the ISSN filter is strictly better
- Only useful as a weak secondary filter when not using ISSN-based sources

**`count`**
- Total papers to collect after filtering
- Pagination is automatic — just set the target number

**`min_relevance`**
- Score threshold (0–10) applied after the filter-agent scores each paper
- Set to `0` when using a journal whitelist without a specific topic — the journal filter already does the selection work, and applying a relevance threshold on top would drop papers arbitrarily
- Set to `6` (default) for topic-specific searches
- Set to `7` or `8` for tight, high-precision collections

**`min_citations`**
- Hard pre-filter: papers below this count are dropped before scoring
- `5` is a reasonable default; raise to `20`+ for high-impact-only collections
- Set to `0` to disable

**`sources`**
- `semantic_scholar` — use always; best coverage for most fields
- `arxiv` — add for STEM, CS, economics, or preprint-heavy fields; remove for humanities and social science journals (Theory, Culture & Society, sociology, cultural studies, etc. do not appear on arXiv)
- `crossref` — useful for DOI enrichment but not as a primary search source

**`use_examples`**
- `true` when the user has dropped DOIs or PDFs in `examples/` and wants scoring calibrated to them
- `false` when doing a journal-only search with no specific topic, or when `examples/` is empty — avoids wasting a Sonnet API call on an empty profile

**`download_pdfs`**
- `true` to run the download pipeline after filtering
- The download script accepts `--layers` to control which layers run and `--existing-dirs` to skip papers already in a local library folder

### Common task → config mapping

| User's goal | Key config decisions |
|-------------|----------------------|
| All papers from a specific journal, any topic | `topic`: broad subject terms · `research_brief`: reward impact/significance · `min_relevance: 0` · `journals`: [journal name] · `use_examples: false` · remove `arxiv` if humanities |
| Topic-specific search across all journals | `topic`: precise keywords · `research_brief`: detailed theoretical + method description · `journals: []` · `min_relevance: 6` or higher |
| High-impact papers only | `min_citations: 20`+ · `min_relevance: 7`+ · sort handled automatically by download prioritisation |
| Specific theoretical framework | `topic`: short keywords · `research_brief`: full framework description with constructs, methods, exclusions · `use_examples: true` if user has examples |
| Recent papers only | `year_min`: recent year · `min_citations`: lower (recent papers have fewer citations) |
| Re-run with tighter filter | Do not delete `raw_results.json` · adjust `min_relevance` or `min_citations` · run filter step only |

---

## Subagents

Three subagents in `.claude/agents/` handle each step:

- **search-agent** (Sonnet, tools: Bash/Read/WebFetch) — runs `search.py`, reports counts and errors
- **filter-agent** (Sonnet, tools: Bash/Read/Write) — runs `filter.py`, reports score distribution
- **report-agent** (Haiku, tools: Bash/Read/Write) — runs `report.py`, prints key stats inline

---

## Orchestration protocol

1. Read `search_config.yml` aloud so the user can confirm settings before starting
2. If the user describes a new task, propose config edits first — do not run the pipeline on stale settings
3. Run pipeline in order: search → filter → download (if `download_pdfs: true`) → report
4. After search: if results < 70% of `count` target, ask the user about broadening `topic`, relaxing `year_min`, or lowering `min_citations`
5. After filter: show score distribution (9–10 / 7–9 / 5–7 buckets) and how many were dropped by journal filter vs relevance filter
6. Never run filter before search has written `raw_results.json`
7. After download: report how many were downloaded per layer and how many are in `outputs/manual_downloads.csv`

---

## Download pipeline details

`download_pdfs.py` runs four layers in sequence per paper, stopping at the first success:

| Layer | Method | Notes |
|-------|--------|-------|
| 1 | Direct URL from metadata | Fast, works for arXiv and open-access papers |
| 2 | Unpaywall API | Finds legal open-access versions (author manuscripts, repositories) |
| 3 | Playwright MCP | Browser automation through institutional login — queued to `outputs/playwright_queue.jsonl` |
| 4 | Sci-Hub | Last resort — DOIs never logged |

After all layers: failures written to `outputs/manual_downloads.csv`, sorted by citations + relevance score (most valuable first), with pre-filled URLs for each paper.

**To process the Playwright queue:** tell Claude Code "Process the Playwright download queue" after the main download run completes.

**To skip papers already in a local library:**
`python scripts/download_pdfs.py --existing-dirs ~/Documents/Papers`

**Papers are downloaded in order:** most cited first → highest relevance score → newest year. If a run is interrupted, the most valuable papers are already saved.

---

## User commands → actions

| User says | Action |
|-----------|--------|
| "Collect papers" | Confirm/update config → full pipeline (steps 1–4) |
| "Just search" | Confirm/update config → step 1 only |
| "Re-filter" | Steps 2–4, reusing existing `raw_results.json` — do NOT delete it |
| "Re-filter with tighter settings" | Update `min_relevance` or `min_citations` in config → steps 2–4 |
| "Add examples and re-filter" | Remind user to drop files in `examples/` → steps 2–4 |
| "Download papers" / "Get PDFs" | Run download step only on existing `papers.csv` |
| "Process the Playwright queue" | Use Playwright MCP to work through `outputs/playwright_queue.jsonl` |
| "Show me the summary" | Print contents of `outputs/summary.md` |
| "How many PDFs downloaded?" | Count files in `outputs/pdfs/` |
| "I want papers from [journal]" | Update config (topic → broad terms, min_relevance → 0, use_examples → false, remove arxiv if humanities) → confirm → run pipeline |
| "I want papers about [topic]" | Update config (topic → precise keywords, research_brief → full description) → confirm → run pipeline |
| "Change the topic to X" | Update `topic` and `research_brief` in config → confirm with user → ask if they want fresh results (delete raw_results.json) or re-filter only |

---

## Hook

`hooks/validate_output.js` is a PostToolUse hook that fires on every Write. If the write targets `outputs/papers.csv`, it checks for required columns (`title`, `authors`, `year`, `doi`, `relevance_score`, `score_reason`) and warns on >5 duplicate titles.

**If the hook exits with code 2, fix the CSV issue before proceeding.**

---

## Key constraints

- Never invent paper metadata — all data must come from API responses
- `filter.py` uses `claude-haiku-4-5` for per-paper scoring and `claude-sonnet-4-6` for profile building
- To fetch fresh results, delete `outputs/raw_results.json` before re-running search — otherwise search appends to existing results
- Example papers added to `examples/` between runs are picked up automatically on the next filter step — no restart needed
- `min_relevance: 0` disables relevance filtering entirely — use when journal whitelist is the primary filter
- Never set `topic` to a journal name, empty string, or `[]` — always use real keyword queries

---

## Self-improvement rule

**After every run, update this file** with anything learned about API behaviour, config decisions, or yield estimates that future runs should know. The goal is that each run leaves this project slightly smarter than it found it.

Specifically: after any run that produced surprising results (too few papers, wrong journals, scoring anomalies), add a note to the "Lessons from past runs" section below before closing the session.

---

## Lessons from past runs

### Semantic Scholar venue field is unreliable — use CrossRef + OpenAlex for journal-specific searches
*Discovered: Theory, Culture & Society collection, April 2025*

**Semantic Scholar** returns the `venue` field inconsistently for humanities/social science journals:
- Often **empty** (`""`) even for papers clearly from a named journal
- Sometimes HTML-escaped (`"Theory, Culture &amp; Society"`) — `filter.py` applies `html.unescape()` but empty venues still slip through
- Out of 200 raw results fetched, expect only ~2–5 to match a specific humanities journal by venue name

**Do not use Semantic Scholar as the source for journal-specific collections.**

**CrossRef + OpenAlex are the correct sources.** Both support ISSN-based filtering and return 100% accurate journal membership:
- CrossRef: `/journals/{issn}/works` endpoint — guaranteed to be from that journal
- OpenAlex: `filter=primary_location.source.issn:{issn}` — 1,156 TCS papers found instantly

**How to configure a journal-specific search:**
1. Find the journal's print ISSN (e.g. TCS = `0263-2764`)
2. Add `issns: ["0263-2764"]` to `search_config.yml`
3. Set `sources: [crossref, openalex]` — remove `semantic_scholar` and `arxiv`
4. Set `journals: []` — the ISSN filter replaces it
5. Keep `min_relevance: 6` — scoring still useful to rank by theoretical quality

**Worked example (TCS, April 2025):**
- `issns: ["0263-2764", "1460-3616"]`, `count: 50`, `sources: [crossref, openalex]`
- CrossRef returned 50 papers, OpenAlex 100; after dedup: 100 unique papers, all from TCS
- Filter scored 100 papers → exactly 50 passed `min_relevance: 6`
- Top papers: Habermas on public sphere, biopolitics, Anthropocene social theory, actor-network theory
- Zero papers from other journals — 100% accuracy

**OpenAlex ISSN filter note:** use only the first (print) ISSN — OpenAlex deduplicates by journal internally so both ISSNs return the same papers. Using `|` OR syntax in the filter param causes a 400 error; use a single ISSN value instead.

### Theory, Culture & Society PDFs are fully paywalled — no automated download possible
*Discovered: April 2025*

TCS is published exclusively by SAGE Journals with no open-access mandate. Layers 1 and 2 (direct URL + Unpaywall) return 0 PDFs for all 50 papers. Unpaywall has no open-access versions for this journal.

**For TCS and similar SAGE humanities journals:** skip layers 1–2, run `--layers 1,2` only to generate `outputs/manual_downloads.csv`, then download manually through institutional access. The CSV is pre-sorted by citations + relevance score and includes publisher page, Unpaywall, Open Access Button, Google Scholar, and ResearchGate links per paper.