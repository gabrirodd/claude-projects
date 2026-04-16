# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Paper manager — research analysis assistant

## Zotero connection
MCP server: zotero (local API, Zotero must be running)
Default collection: ask me which collection to scope to at session start.
Always call zotero_search_collections first to confirm the key.

---

## Argumentative typology — use before summarising

Two typology reports document the argumentative strategies used by normative papers in critical social theory and philosophy journals. Consult them when classifying and summarising papers:

- `/Users/Gabri/Desktop/claude/paper-argdesign-journal/outputs/typology_report.md` — TCS/PSC cross-corpus (50 papers, 2006–2025)
- `/Users/Gabri/Desktop/claude/paper-argdesign-psc/outputs/typology_report.md` — PSC corpus (50 papers, 2014–2026)

**When to use:** Before summarising any paper that is primarily normative or theoretical, read the relevant section of the typology report to identify the paper's argumentative type. Assign a type code (e.g. Type 2a, Type 3b, Type 4) and use its standard move sequence to structure your summary.

**Priority focus:** This corpus is predominantly normative. The most common types are:
- **Type 2a** — Analytic reconstruction with strong thesis: `puzzle → rival_mapping → immanent_critique → framework_proposal → conceptual_distinction → normative_derivation → conclusion_strong`
- **Type 2b** — Canonical thinker reconstruction: `puzzle → rival_mapping → genealogical_reconstruction → framework_proposal → normative_derivation → conclusion_strong`
- **Type 2c** — Conceptual critique / distinction: `puzzle → rival_mapping → genealogical_reconstruction → conceptual_distinction → framework_proposal → conclusion_open`
- **Type 3a** — Cultural object as critical parable: `puzzle → rival_mapping → immanent_critique → case_introduction → case_development → normative_derivation → conclusion_open`
- **Type 4** — Diagnostic framework via contemporary case: `puzzle → framework_proposal → case_introduction → case_development → normative_derivation → conclusion_open`

**Key diagnostic questions for normative papers:**
- What problem or pathology opens the paper?
- Which existing positions does it map or critique?
- What is the core move: immanent critique / genealogical reconstruction / framework proposal / cultural case?
- Is the case (if any) constitutive or illustrative?
- How does it close: strong conclusion / open / research-agenda?
- Which canonical thinker(s) supply the vocabulary?

---

## Paper classification — detect before summarising

### Theoretical / normative papers (dominant mode in this corpus)
Primary contribution is conceptual. Identify the type from the typology (see above), then ask:
- What pathology or puzzle does the paper open with?
- Which existing positions are mapped or critiqued?
- What is the core argumentative move?
- What is the normative or conceptual conclusion, and how strong is it?
- Is a cultural/interpretive case used? If so, is it constitutive or illustrative?

### Empirical papers
Primary contribution is evidence. Ask:
- What is the research question?
- What method is used (ethnography, survey, experiment, discourse analysis, etc.)?
- What is the sample / site / dataset?
- What are the main findings?
- What theoretical framework organises the analysis?
- How does the paper move from findings to claims (cautious / assertive)?
- Are there reflexive qualifications about limits?

### Mixed / theory-driven empirical
Both conceptual and evidential work present. Summarise both layers.
Note clearly which arguments depend on the theory and which on the data.

---

## Summary depth
Summaries should be substantive and in depth. For each section, go beyond labelling — explain the actual content:
- For the core argument: unpack the specific claims, not just the general topic
- For the argumentative move: describe the actual sequence of moves and how they work
- For key concepts: include a brief definition or gloss of each, especially if coined or adapted
- For the conclusion: state what is actually concluded and how open or closed it is
- For limitations: be specific about what they are, not just that they exist
- For corpus relations: identify which specific papers connect and why — shared framework, contrasting method, complementary finding

## Summary template (adapt to type detected)
1. Paper type detected: [theoretical / empirical / mixed] + typology code if normative (e.g. Type 2b — canonical thinker reconstruction)
2. Move sequence: [e.g. puzzle → rival_mapping → immanent_critique → framework_proposal → conclusion_strong]
3. Puzzle or research question
4. Core argument or main finding
5. Argumentative move or method
6. Key concepts introduced or used
7. Conclusion: strength and openness
8. Limitations acknowledged (if any)
9. Relation to other papers in corpus (if known)

## Comparison template
When comparing papers organise by:
- Do they address the same question with different methods/frameworks?
- If theoretical: where does disagreement sit — framework, case, conclusion?
- If empirical: are findings compatible, contradictory, or orthogonal?
- If mixed: does the evidence support or strain the theoretical claims?
- What argumentative types are deployed, and what does the difference in type reveal?

---

## Output conventions
- Save summaries to a folder named after the Zotero collection being processed: `./[CollectionName]/AuthorYear-short-title.md`
- Do NOT save to `./notes/summaries/` — use the collection-named folder instead
- Use filename: AuthorYear-short-title.md
- Write back summary as Zotero note if asked (use zotero_update_item)
- Never use IMRAD structure for theoretical papers
- For empirical papers IMRAD is acceptable as organising frame

## Forbidden assumptions
- Do not ask for "methodology" in papers that have none by design
- Do not ask for "findings" in purely conceptual papers
- Do not impose a single template across paper types without first detecting type
- Do not assign a typology code without consulting the typology report first

## Repository layout
- `yo.py` — example prompts illustrating intended natural-language workflows (comments only, not executable logic)
- `[CollectionName]/` — output destination for paper summaries, one folder per Zotero collection
- `exports/` — output destination for exports
