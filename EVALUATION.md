# Evaluation record — 2026-11-06

This file preserves the steps 1–4 baseline record. For the implemented steps 5–6
and paired variant evaluation, see [STEP_5_6_COMPARISON.md](STEP_5_6_COMPARISON.md).

## Reproducible checks

Commands are in README.md. The organizer kit and scoring tools were not modified.
All supplied content, derived evidence, and detailed organizer answer logs stay
in ignored local directories. Only invented fixtures and aggregate metrics are
intended for publication.

| Check | Observed result |
|---|---|
| Unit/integration tests | 12 passed |
| Full corpus ingestion | 5 snapshots; 3,294 source occurrences |
| Unique raw content | 2,826 documents |
| Parsed blocks, unique content | 252,295 |
| Source spans checked across occurrences | 342,069 |
| Full ingestion timing, audit run | 3.561 seconds |
| Organizer starter baseline | 40 questions, 0 errors, QA/final 0.093, p95 0.54 seconds |
| New submission contract smoke run | 40 questions, 0 errors, ingestion 2.7 seconds |
| Synthetic development diagnostic | 6/30 including paraphrases; only refusal cases pass |

The new submission also scores 0.093, entirely through refusal questions. This
does not indicate improvement or equivalent answer quality. Answering is pending.
The public run omits the conflict pillar, and its paraphrase groups are singletons.
Neither its consistency score nor the aggregate score establishes generality.

## Fixture scope

`tests/evaluation_cases.py` contains 24 synthetic development cases and 12 frozen
synthetic holdout cases, separated by product family, plus six development
paraphrases. Expected values are independently specified in invented source
documents. Fixtures cover current/historical rates, bounded complete lists, and
missing evidence. Tests additionally cover source mutation, malformed rows,
escaped text, disappeared pages, content deduplication, and atomic ingestion.
Submission code never imports evaluation fixtures. Holdout answering has not
been run; fixture integrity has been checked.

These are controlled initial fixtures, not the manually adjudicated corpus gold
proposed in the draft. Corpus-derived descriptive, contradiction, eligibility,
and difficult tier cases still need annotation before broad QA claims. The
existing 40 public questions provide the current real-corpus QA benchmark.

## Parser audit and limits

Across source occurrences: 1,043 table headers and 6,586 table rows were retained.
Warnings: 1,113 row-width mismatches, 66 header-width mismatches, 1,227 unparsed
pipe structures, and 4,747 blocks from escaped-newline documents. These overlap
and count occurrences, not distinct broken pages. Raw evidence is retained for
all of them. Warnings are a review queue, not an assertion that the website is
wrong or that all remaining rows are semantically correct.

The span audit checks bounds and exact source slicing. It cannot establish that
a cell is associated with the correct product, that nearby footnotes apply, or
that a citation entails an eventual answer. Those require the next-stage tests.

Environment: Windows, Python 3.12.4. Python 3.11 runtime verification remains open.
