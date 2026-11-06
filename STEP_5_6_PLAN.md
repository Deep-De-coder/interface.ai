# Revised steps 5 and 6

Drafted 2026-11-06. These numbers refer to the user's 12-step implementation
sequence, not the numbered sections or phases in DRAFT_PLAN.md. This document
supersedes the earlier descriptions of those two steps. Retained as the original
draft; implementation and the alternative treatment are documented separately
in [STEP_5_6_RESEARCH_DRAFT.md](STEP_5_6_RESEARCH_DRAFT.md).

## Research, separated by problem

Focused primary-source search through November 6, 2026; not an exhaustive claim
to the newest paper in every area. Findings below are reported research, not
experiments reproduced on our kit. Proposed adaptations are our engineering
judgment. No external repository determines the design.

| Independent problem | Relevant research and finding | Adaptation and limitation |
|---|---|---|
| Identify the question's date separately from its subject | [MRAG, EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.167/) decomposes content and temporal constraints, then ranks semantic and temporal relevance separately. | Separate date parsing from product/term parsing. Exact snapshot membership is stronger than a soft date score when the API supplies an explicit cutoff. MRAG's summaries and multi-stage ranking are not prerequisites. |
| Select applicable versions when documents overlap | [TimelyRAG, September 2026 preprint](https://arxiv.org/abs/2609.11572) adds temporal distance to retrieval ranking for evolving amendments and reports gains up to 28.6% in nDCG@10. | Useful for ambiguous version retrieval, but our five full snapshots allow exact selection. The reported retrieval gain is not QA accuracy or evidence that we need its full framework. Effective dates still require grounded interpretation. |
| Compare evidence across periods | [TEMPO, EMNLP 2026](https://aclanthology.org/2026.emnlp-main.291/) supplies decomposed retrieval steps and measures temporal coverage and precision on complex cross-period questions. | Retrieve each requested endpoint independently; verify that both periods are represented before comparing. This benchmark motivates evaluation, not a proven solution to matching our product tiers. |
| Keep stale model knowledge from overriding supplied evidence | [When Facts Change, ACL Findings 2026](https://aclanthology.org/2026.findings-acl.103/) finds that explicit mutability prompting increases temporal discussion without improving factual accuracy. | Enforce source eligibility outside generation. A fluent temporal explanation is not a correctness check. This paper studies model/context conflict, not a complete authority policy for conflicting website pages. |
| Retrieve values with their table meaning | [T-RAG, ACL Findings 2026](https://aclanthology.org/2026.findings-acl.1902/) combines hierarchical indexes, staged retrieval, and graph-aware context organization for multi-table QA. | Retrieve page/section, then row plus headers and conditions. Start with the hierarchy already parsed; add no graph service. Its benchmark is much larger and does not establish performance on our malformed markdown. |
| Decide whether to answer | [Sufficient Context, ICLR 2025](https://research.google/pubs/sufficient-context-a-new-lens-on-retrieval-augmented-generation-systems/) separates insufficient retrieval from failure to use sufficient evidence. [Better Retrievers, Worse Labels, October 29, 2026 preprint](https://arxiv.org/abs/2610.40966) shows that missing annotated gold documents can incorrectly imply missing answer evidence. | Judge the actual retrieved content, not only retrieval score or expected URL. Measure false refusal as well as unsupported answers. Sufficiency judgments themselves can be wrong; do not call this a guaranteed truth gate. |
| Provide supporting citations | [ALCE, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398/) evaluates answer correctness and citation quality separately. Retained as foundational work, not presented as new research. | Carry source spans into rendering and check support per claim. A real URL or exact quote does not alone establish entailment. |

## Step 5 — Select the evidence view and interpret applicable dates

**Deliverable:** a small deterministic time-selection module, not a temporal
database or a general knowledge graph.

1. Define `TimeRequest`: knowledge cutoff, optional described/event date,
   comparison endpoints, and uncertainty. Explicit API `as_of` controls the
   knowledge cutoff. A textual date can describe an event within that knowledge
   state; it is not automatically a contradictory cutoff. Clarify only genuinely
   incompatible requests. With no date intent, use the latest supplied snapshot.
2. Implement `select_snapshot(cutoff)`: choose the latest observation on/before
   the cutoff. Before the first observation return unavailable; between pulls
   retain the selected observation date; after the last pull expose last-known
   status rather than claiming fresh observation. Never use the machine's date
   to silently advance knowledge. Reject ambiguous duplicate-date snapshots
   unless a documented ordering exists.
3. Restrict current/historical retrieval to source occurrences in that selected
   full snapshot. Preserve deduplicated raw text but never lose occurrence IDs.
   Disappeared pages are not silently carried forward. All derived aliases,
   summaries, and cache keys must use the same eligible evidence view.
4. Represent explicit effective/expiry statements as optional, span-backed
   applicability constraints. Do not infer them from fetch time, a URL year, or
   a vehicle model year. Unknown dates remain unknown. A page announcing a
   future offer supports an announcement, not a claim that the offer is active.
   Contradictory metadata produces uncertainty rather than automatic precedence.
5. For a change question, produce two independently eligible evidence views.
   Step 6 compares matching entities/metrics/scopes. If an endpoint is missing,
   report incomplete comparison. Observing a new value does not establish the
   exact real-world change date.

**Acceptance:** tests for exact dates, gaps, before/after coverage, textual event
dates versus API cutoffs, model years, scheduled/expired offers, missing pages,
and endpoint coverage. Mutating a later snapshot must not change an earlier
answer's evidence or notes. Assertions concern the finite test suite only.

**Alternative considered:** mixing all versions and using temporal reranking.
Retain as an experiment only if explicit snapshot routing proves insufficient
for a demonstrated query type. A soft score must never override hard eligibility.

## Step 6 — Build a small, evidence-grounded answering path

**Deliverable:** a working vertical slice through existing ingestion/parsing,
Step 5 selection, retrieval, answer decisions, and contract output.

1. First audit parser warnings on the pages used by this slice. Repair row/header
   alignment or use original passages when structure is unreliable. The current
   parser's nearby context is a candidate association, not proven applicability.
2. Add a minimal request representation: entity, metric, supplied qualifiers,
   intent, and Step 5 time request. Start with explicit cases and normalization;
   do not encode site-specific values or topic-based permanent refusals.
3. Retrieve within the selected view using lexical page/section search and exact
   entity/metric matching where supported. Expand table hits to headers and
   conditions. For bounded lists, enumerate the relevant section rather than
   assuming top-k snippets are complete. Allow one bounded expansion on misses.
4. Build a compact evidence bundle: proposed claims, scope, exact excerpts,
   source occurrences, parser warnings, and missing requirements. Classify as
   supported, insufficient, ambiguous, or conflicting. For the initial conflict
   case, identify comparable alternatives and abstain from choosing a winner
   without a defensible rule. Full conflict discovery remains step 8.
5. Render numeric answers from validated cells with units/qualifiers. Render
   descriptive answers from supported excerpts initially. Generate citations
   from the evidence bundle. For changes, report both dated values only after
   confirming comparable scope. Do not claim a full list from partial evidence.
6. Compare a bounded model-assisted parser/reader on descriptive or ambiguous
   development cases if a model is available. Hold evidence constant to separate
   reader errors from retrieval errors. Keep it only if correctness/coverage
   improve within latency limits. Model availability is not a prerequisite to
   the first slice, and an unrun comparison must remain labeled untested.
7. Validate seven case types: current value, historical value, qualified tier,
   descriptive fact, bounded complete list, unresolved contradiction, and
   missing evidence. Add one cross-period change case. Use invented mutations
   plus manually adjudicated corpus examples stored locally; synthetic fixtures
   alone do not satisfy real-corpus validation. Reserve product families for
   holdout and avoid tuning on their failures.

**Acceptance:** inspectable support for every successful case; unsupported
numeric claims and future leakage absent in this fixed suite; changed supporting
data changes outputs; adding/removing essential evidence changes answerability.
Report evidence recall, supported-answer accuracy, false refusals, coverage,
list completeness, citation support, and uncached p95 latency separately. Target
p95 <=2 seconds; do not hide slower model calls in aggregate cache timings.

**Scope boundary:** this slice is not full general-purpose query understanding,
site-wide conflict mining, or a guarantee of correct semantic entailment. Those
remain later work. The key experiment is whether evidence selection and answer
construction work across the case types before adding infrastructure.
