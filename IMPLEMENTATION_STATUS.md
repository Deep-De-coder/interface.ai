# Current implementation status

Updated 2026-11-07. Current measured results and exact remaining failures are in
[ROUND_02_RESULTS.md](ROUND_02_RESULTS.md). Earlier comparison documents describe
historical revisions, not current performance.

The standard-library implementation supports immutable snapshot ingestion,
date selection, basic/research retrieval, table and bounded prose facts,
shared product/audience/purpose scope, per-output-fact conflict resolution,
exact citations, refusal, bounded lists/rules, location-scoped schedules,
scalar extrema/positive existence, and explicit count/link readers.

Public QA: basic **0.5310**, research **0.4977** (40 questions). Prior scores were
0.5561 and 0.5227. Both now answer 23/40 confidently, not necessarily correctly.
Three card questions improved; three general-hours questions now refuse an
unsupported branch-to-general inference. Other question scores are unchanged.
Basic remains the default; this is not an overall benchmark improvement.

Basic p95 .687s, maximum 1.603s, ingestion 62.15s. Research p95 .757s, maximum .913s,
ingestion 62.19s. Both satisfy the local p95 target. Zero detected quote-integrity
or source-eligibility failures; this is not proof of semantic entailment.

46 tests pass on Python 3.11.9 and installed Python 3.12. Review probes 14/14,
synthetic dev 30/30 and reused holdout 12/12 in both modes. All are development
or regression results. The allowlisted source-only package imports in isolation.
No hidden-test result, full conflict-gold performance or CI result is claimed.

Final code hash: 2145d775ed63a5d0389be1649652bc9ad0c0eb672919a3801972c59561e9708b.
Private reports: results/review-rounds/round-02/final/. Public code and notes
exclude supplied source snapshots, detailed evidence reports and credentials.

Not submission-ready: unresolved membership/product scope, count reporting
periods, closure/recognition relations, general schedules, broad product inventory
and several procedures. BASIC_REVIEW_PLAN.md tracks fixes and failed attempts;
WORK_PROGRESS.md is the continuation record. Publication branch is main.
