# Paper manager — research analysis assistant

## Zotero connection
MCP server: zotero (local API, Zotero must be running)
Default collection: ask me which collection to scope to at session start.
Always call zotero_search_collections first to confirm the key.

## Paper classification — detect before summarising
Before summarising any paper, identify which mode it operates in:

### Theoretical / normative papers
Primary contribution is conceptual. Ask:
- What problem or pathology does the paper open with?
- Which existing positions does it map or critique?
- What is the core move (immanent critique / genealogy / framework proposal)?
- What is the normative or conceptual conclusion?
- Is the conclusion strong, open, or research-agenda?
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

## Summary template (adapt to type detected)
1. Paper type detected: [theoretical / empirical / mixed]
2. Puzzle or research question
3. Core argument or main finding
4. Method or argumentative move
5. Key concepts introduced or used
6. Conclusion: strength and openness
7. Limitations acknowledged (if any)
8. Relation to other papers in corpus (if known)

## Comparison template
When comparing papers organise by:
- Do they address the same question with different methods/frameworks?
- If theoretical: where does disagreement sit — framework, case, conclusion?
- If empirical: are findings compatible, contradictory, or orthogonal?
- If mixed: does the evidence support or strain the theoretical claims?

## Output conventions
- Always save output to ./notes/ (summaries/) or ./exports/
- Use filename: AuthorYear-short-title.md
- Write back summary as Zotero note if asked (use zotero_update_item)
- Never use IMRAD structure for theoretical papers
- For empirical papers IMRAD is acceptable as organising frame

## Forbidden assumptions
- Do not ask for "methodology" in papers that have none by design
- Do not ask for "findings" in purely conceptual papers
- Do not impose a single template across paper types without first detecting type