# Basic implementation round 02 — results and remaining failures

2026-11-07. Baseline: published code `9c6d9db`, review checkpoint `fc1d7c5`.
Runtime changes were implemented, tested and evaluated against the same 40 public
questions and five snapshots. Both modes still use deterministic local evidence;
no API/model or external website content was added.

## Is it better?

**It fixes the reproduced defects, but the public QA score is lower.** Basic moved
from **0.5561 to 0.5310**, a decrease of **2.51 percentage points**. Research moved
from 0.5227 to 0.4977. Basic remains the higher-scoring default. Do not describe
this as an overall benchmark improvement or as submission-ready.

| Measure | Previous | Round 02 |
|---|---:|---:|
| Basic public QA, weighted partial credit | 55.61% | 53.10% |
| Research public QA | 52.27% | 49.77% |
| Basic confident answers | 24/40 | 23/40 |
| Research confident answers | 25/40 | 23/40 |
| Existing/new unit tests | 30 passed | 46 passed |
| Fixed review probes | 4/14 | 14/14 |
| Synthetic development cases, each mode | 30/30 | 30/30 |
| Reused synthetic holdout, each mode | 12/12 | 12/12 |
| Invalid quote / ineligible snapshot detections | 0 / 0 | 0 / 0 |
| Basic p95 answer latency | 0.439 s | 0.687 s |
| Research p95 answer latency | 0.507 s | 0.757 s |
| Basic ingestion | 35.26 s | 62.15 s |

Final basic maximum answer latency was 1.603s; research maximum was 0.913s.
Both p95 values meet the two-second target, but basic is slower than baseline.
An intermediate implementation exceeded the target (2.375s basic p95). Moving
link/count extraction and section grouping to evidence indexes reduced repeated
query scanning; all 40 answers remained identical after that optimization.
Ingestion does more work and is slower. These are single local runs, not a
controlled performance study; machine load may also affect the comparison.

Final submission-code SHA-256:
`2145d775ed63a5d0389be1649652bc9ad0c0eb672919a3801972c59561e9708b`.
Final artifacts: `results/review-rounds/round-02/final/{report,details}.json` and
checksum manifest. Corpus and question hashes match round 01 exactly. Private
per-item comparison: `results/review-rounds/round-02/comparison.json`.
The source-only ZIP was imported in isolation; supplied snapshots and API keys
are excluded. No CI result is claimed by these local checks.

The 14 probes are now regression checks, not independent evidence of generalization.
One checks an audience-qualification policy; several share a cause. The reused
holdout has been inspected in prior development. Exact citations are necessary,
but do not establish relevance, completeness or semantic correctness.

## What changed in public scores

Only six basic question scores changed from round 01:

| Public ID | Subject | Previous → new | Explanation |
|---|---|---|---|
| dup-034 | All credit cards and APRs | 0.8583 → 1.0 | Product-local prose adds personal card ranges while preserving business rows. |
| dup-035 | Standard Platinum Visa APR | 0 → 1.0 | Ongoing personal-card range is available; business evidence no longer stands in alone. |
| dup-040 | Credit-card rates | 0 → 1.0 | Conversational prefix normalization plus product-local prose supports the request. |
| dup-064 | General lobby hours | 0.85 → 0 | Refuses because one branch article does not establish a general schedule. |
| dup-066 | Drive-up hours without location | 0.85 → 0 | Refuses rather than generalizing a branch-local schedule. |
| dup-065 | Lobby hours without location | 1.0 → 0 | Same scope correction. |

The three hours losses are deliberate scope corrections, not proof that the
expected hours are wrong. Finding an eligible general policy or answering a
specified branch remains required. The other 34 question scores are unchanged;
some answer wording, confidence or refusal reasons changed.

## Exactly where basic still fails or loses credit

The table covers every public item with score below 1.0. A scorer miss is not
automatically a false statement. The detailed answers, selected sources and traces
remain private in `results/review-rounds/round-02/`.

| Public IDs | Observed result | Cause / next action |
|---|---|---|
| dup-009, dup-016, dup-017 | 0.85 each; expected numeric tokens matched | Reference-URL mismatch costs the source component. Citations are exact and eligible; check source authority/scope rather than forcing the preferred URL. |
| dup-064, dup-065, dup-066 | Refusal; score 0 | No evidence establishing the requested general location scope. Need a general policy or location clarification; do not restore branch-to-general extrapolation. |
| dup-104 | Refusal; score 0 | Cannot establish whether all branches share hours from the scoped reader. Needs comparison of location-specific schedules with coverage limits. |
| dup-073 | Refusal; score 0 | Multiple explicit branch-count statements are present. No reliable reporting-period/source-authority resolution yet; counting all locator entries would mix branches and ATMs. |
| dup-075 | Refusal; score 0 | Named branch closure/current-state evidence is not connected to the question. Month-only time and closure-event relationships remain incomplete. |
| dup-076 | Refusal; score 0 | Cannot connect a closed branch's members to the stated alternative full-service locations. This is a relation-reading gap. |
| dup-087 | Confident excerpt; score 0 | Recognition evidence is topical but omits the required latest/fifth-recognition detail. Need relation and reporting-period selection; not automatically fabricated recognition. |
| dup-008 | Confident link; score 0 | Finds an explicitly labeled business certificate-rate link instead of the expected personal destination. Link-label relevance alone does not resolve audience. |
| dup-049 | Confident positive witnesses; score 0 | Finds matching rates on other savings-related account tiers, while the gold expects a different savings scope/value. Broad 'any savings' versus intended Share Savings scope is unresolved; do not hard-code the gold value or silently narrow the question. |
| dup-005 | Confident certificate table; score 0 | Known empty-token scorer limitation, plus separate incomplete broad coverage: a selected business-special table is not a complete certificate inventory. |
| dup-081 | Refusal; score 0 | Different eligibility groups are treated as competing. Needs membership-versus-product scope and rule equivalence; single-bullet fallback is intentionally disabled. |
| dup-060 | Refusal; score 0 | Contact-update instructions are not supported by the bounded action/object reader. Wrong password advice remains blocked. |
| dup-046 | Refusal; score 0 | Highest APY requires complete comparable scalar tiers; conditional/uncertain candidates block the operation. Need better tier applicability and completeness analysis, not arbitrary max over retrieved numbers. |
| dup-088 | Refusal; score 0 | 'Last year' is rejected as an ambiguous date. Need an explicitly documented snapshot-relative reporting-period policy, separate from article publication periods. |
| dup-101 | Refusal; score 0 | Student/university/flexibility intent is not mapped to supported product evidence. Entity/intent vocabulary is too literal. |
| dup-094 | Refusal; score 0 | Procedure reader cannot assemble device/wallet compatibility and add-card instructions into the requested answer. |
| dup-082 | Refusal; score 0 | Joining online requires linking action guidance to the application destination; this relation is not assembled by the current reader. |

The three expected-refusal questions remain correctly refused. No hidden-test or
full-conflict-gold performance has been established.

## Changes and failed attempts retained

- Every emitted structured scope passes the same conflict resolver; later table
  rows no longer bypass resolution. Shared identity separates different products
  on one page and preserves explicit audience, purpose, metric and qualifiers.
- Numeric prose preserves ranges and conditions as full expressions. Unsupported
  complex expressions are not reduced to scalars for aggregate operations.
- Scoped hours and whole eligibility sections replace isolated lexical excerpts.
- Positive existence witnesses, bounded extrema, explicit counts, labeled links,
  action aliases and negation guards were added without external dependencies.
- A procedure normalization initially reintroduced password advice; a preserved
  contact-record object fixed it. Neighboring introductory context initially
  suppressed ongoing rates; prose context was isolated. Shared transfer footnotes
  then suppressed business rows; purpose checks now use the row itself. Strict
  locator labeling lost a valid URL; operation words were separated from subjects.
  Each has a regression check and is retained in `BASIC_REVIEW_PLAN.md`.

## Next round

1. Resolve source scope and reporting periods for membership rules, branch counts,
   closure events and recognition. Keep these as separate bounded readers.
2. Add explicit audience handling to links and broader savings/certificate queries.
3. Support complete schedule comparisons and remaining action-to-destination
   procedures, with positive controls and adversarial scope tests.
4. Re-run the same baseline comparison and review all changed confident answers.
   Preserve both scorer outcomes and semantic adjudications; do not chase keyword
   scores by restoring the demonstrated unsafe generalizations.
