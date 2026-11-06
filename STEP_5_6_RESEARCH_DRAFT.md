# Steps 5 and 6: research comparison draft

Research checked 2026-11-06. Kept separately from the original
[snapshot-first draft](STEP_5_6_PLAN.md). Both are implemented as selectable
retrieval modes sharing ingestion, parsing, time eligibility, and evidence checks.
This is a project-specific adaptation, not a reproduction of paper results.

## Hypothesis and alternatives

**A — basic (default):** explicit snapshot routing, lexical token overlap over
source blocks and their required context, deterministic table reader, extractive
prose, and conservative refusal. This is the simple reference implementation.

**B — research:** the same admissible snapshot view, with decomposed date/content
queries, BM25 retrieval, additional weights for page/heading/product matches,
and a small ranking preference for explicit applicable-date evidence. The reader
and citation checks stay identical so differences can be attributed to candidate
selection. BM25 is sparse lexical retrieval, not a learned semantic retriever.

Both use generic lexical normalization, table/list context expansion, a bounded
candidate set (40, expanded once to 160 on insufficient evidence), and explicit
date applicability checks. Neither mixes future
observations into a historical view, lets ranking resolve a contradiction, or
uses source popularity as authority. The research date bonus does not choose a
truth winner; competing comparable values still produce uncertainty.

## Independent research contributions

- **Question/time separation:** [MRAG, EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.167/)
  decomposes content and temporal constraints. B removes explicit calendar dates
  from content ranking after recording their meaning. Its LLM summarization and
  learned semantic components are not implemented here.
- **Version-sensitive ranking:** [TimelyRAG, September 2026 preprint](https://arxiv.org/abs/2609.11572)
  motivates considering temporal compatibility alongside content relevance.
  B applies only a modest applicability signal inside a hard-filtered snapshot.
  This is not TimelyRAG's temporal-distance algorithm or a test of its reported
  nDCG gains. For our full snapshots, cross-version soft ranking is unnecessary.
- **Structured context:** [T-RAG, ACL Findings 2026](https://aclanthology.org/2026.findings-acl.1902/)
  motivates retaining table hierarchy. Both readers require headers, row scope,
  and source context; B additionally weights hierarchical identity in retrieval.
  Neither implements its graph-aware multi-table reasoning framework.
- **Endpoint coverage:** [TEMPO, EMNLP 2026](https://aclanthology.org/2026.emnlp-main.291/)
  motivates retrieving each requested period independently. Both variants require
  matching endpoint scopes before rendering a change answer.
- **Refusal assessment:** [Better Retrievers, Worse Labels, October 29, 2026 preprint](https://arxiv.org/abs/2610.40966)
  warns that absence of an annotated gold document is not absence of supporting
  evidence. Our comparison records URL recall separately from answer checks;
  it is not used as the runtime refusal rule. Quote integrity is also separate
  from semantic entailment.

No paper establishes that B will outperform A on this assignment. No external
models, embeddings, training, API calls, or model judges have been run. A trained
semantic retrieval/reader experiment remains a separate future treatment.

The implementation deliberately keeps A as the default until paired results
justify changing it. The differing ranking formulas are implementation
hypotheses, not parameters validated by the cited papers for this corpus.

## Step 5 implementation shared by A and B

`temporal.py` interprets explicit ISO, US numeric, and full-month calendar dates;
separates API cutoff from described dates; selects the latest preceding snapshot;
reports pre-coverage, gaps, post-coverage, and duplicate-date ambiguity. It checks
source-backed effective/expiry statements without inventing missing dates.
Comparison endpoints are independently selected. A future scheduled value is
labeled as a published schedule, not a confirmed later observation.

## Step 6 implementation and limits

`retrieval.py` builds per-snapshot indexes at ingestion; `decisions.py` performs
qualifier matching and conservative table/prose/list reading; `solution.py`
exposes `answer()` and `explain()`. Traces retain selected and retrieved source
positions and reasons. The query vocabulary is generic, with no fixed bank
answer values. Initial scope covers validated numeric table cells, bounded list
sections, simple descriptive passages, and two-date numeric comparisons.

The reader is deliberately limited: arbitrary prose fees, complex temporal
language, cross-page full lists, scope inference, and site-wide conflict discovery
are not complete. Structural warnings block numeric answers. Context attachment
and prose entailment still require semantic review. `conflicts()` enumeration
remains step 8; per-question detected contradictions already cause uncertainty.

## Comparison protocol

Run `python scripts/compare_variants.py --suite synthetic-dev`, then use
`--suite public`, `--suite synthetic-holdout`, or
`--suite local --questions local_eval/step_5_6_dev.jsonl`.
Use `--order research-first` to examine process-warmup/order effects. Public data
and local gold remain excluded from Git. The local gold's eight examples were
checked against source text; they are development checks, not a broad holdout.

Each run records code/corpus/question hashes, interpreter/platform, ingestion
time, uncached query latency, answer coverage, false refusals against labels,
exact-match diagnostics where available, expected-URL retrieval recall, quote
integrity, source eligibility, paired outputs, and traces. The public suite uses
the unchanged organizer QA scorer. Single-run timings and small templated sets
do not establish statistical significance or generality. Inspect semantic
correctness and refusal failures before selecting a default.
