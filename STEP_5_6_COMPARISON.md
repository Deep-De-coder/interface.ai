# Steps 5–6 implementation and comparison

Evaluated 2026-11-06 on Windows with Python 3.12.4. The implemented source version
is identified in each report by SHA-256, independently of an uncommitted Git tree.
All detailed evidence/answer traces remain in ignored `results/`; local corpus
gold remains in ignored `local_eval/`. No supplied snapshots were published.

## What can be compared

| Component | Basic (default) | Research adaptation |
|---|---|---|
| Snapshot eligibility | Hard cutoff and source membership | Same |
| Content query | Normalized tokens | Calendar dates removed after time interpretation |
| Retrieval | Token overlap | BM25 plus heading/product identity weights |
| Time in ranking | No ranking bonus | Small explicit applicability bonus within eligible view |
| Evidence expansion | 40 candidates, up to 160 on insufficiency | Same |
| Reader and citation checks | Shared conservative reader | Same |

The two modes are real selectable implementations, not copies of another
submission. The research mode adapts selected ideas; it does not reproduce the
papers' trained semantic components or reported benchmark results. Both
research-backed drafts are retained: [original](STEP_5_6_PLAN.md) and
[alternative](STEP_5_6_RESEARCH_DRAFT.md).

## Validation and interpretation

Final submission-code SHA-256:
`6deba3d6d7da2cdf0dcf0751177ff902e6d9b463a81563bb4c9afaf00689e101`.

| Final public comparison (40 questions) | Basic | Research |
|---|---:|---:|
| Organizer QA score | 0.1163 | 0.1163 |
| Questions answered confidently | 1 | 1 |
| Refusals on labeled answerable questions | 36 | 36 |
| Reference-URL retrieval recall | 0.75 | 0.75 |
| Ineligible-source / quote-integrity failures observed | 0 / 0 | 0 / 0 |
| Uncached p95 query seconds | 0.139 | 0.381 |
| Ingestion seconds | 39.16 | 60.45 |

These single-run wall-clock times are machine/load-dependent, not statistically
controlled speed comparisons. Both fit the assignment's runtime limits here.
The score includes refusal credit; **only one public answer is confidently
provided**, so this is not adequate coverage for the final assignment. Two
outputs differ across variants, without an aggregate quality gain. The apparent
retrieval recall is URL-level, not recall of every necessary supporting span.

The final unmodified organizer harness run of the default basic mode completed
all 40 questions with zero errors, repeat consistency 1.0, QA/final score 0.1163,
p95 0.15 seconds, and ingestion 35.2 seconds. The separate paired runner above
uses finer-grained timings and does not combine QA with consistency pillars.

25 automated tests pass, including current/historical/tier answers, complete
bounded lists, descriptive evidence, missing facts becoming answerable, source
changes, detected conflicts, scheduled/expired offers, invalid/ambiguous dates,
exact citations, and future-snapshot isolation. The eight first-slice case types
are covered by synthetic integration tests. All source files pass Python 3.11
syntax parsing; execution on Python 3.11 is still unverified.

The development fixtures have 24 questions plus six paraphrases. Both modes pass
30/30. The twelve held-out synthetic questions initially scored 11/12 in each
mode: a monetary amount could trigger the incomplete-year guard. After fixing
that general parser bug, both score 12/12. The inspected failure is now a
regression case; the post-fix number is not an untouched holdout result. These
families share templates, so even the initial holdout is a limited generality
check. New independently authored holdout cases are needed before broader claims.

Eight independently checked local corpus cases exercise table values/tiers,
prose fees, membership instructions, and dates before corpus coverage. Expected
URLs are references, not an exhaustive list of valid evidence. The initial URL
matching diagnostic undercounted answers supported on alternate pages. Local
checks now require expected content, quote support, and snapshot identity, while
recording reference-URL retrieval separately. This is still a lightweight
diagnostic, not an automatic semantic-entailment guarantee.

Both modes pass 6/8 of these local checks: five supported numeric answers and
one correct pre-coverage refusal. The prose-fee and membership-procedure cases
remain false refusals. Reference URLs are retrieved for every answerable local
case, showing that retrieval alone does not resolve the reader's coverage gap.
Final local p95 was 0.151 seconds for basic and 0.352 seconds for research; no
quote-integrity or source-eligibility failures were observed in these runs.

Public evaluation uses the unmodified organizer QA scorer. It does not evaluate
our full conflict coverage, and a fractional token score is not the percentage
of questions correctly answered. Many public questions remain outside this
first slice: prose fees, complex scope matching, full-site lists, procedural
answers, and conflict winner selection. Do not interpret fast refusals as a
successful general QA system.

## Reproduction

```powershell
python -m unittest discover -s tests -v
python scripts/compare_variants.py --suite synthetic-dev
python scripts/compare_variants.py --suite synthetic-holdout
python scripts/compare_variants.py --suite public --order research-first
python scripts/compare_variants.py --suite local --questions local_eval/step_5_6_dev.jsonl --order research-first
python scripts/evaluate.py submission
```

For the final corpus comparisons, use `results/comparison/public/research-first/`
and `results/comparison/local/research-first/`. Earlier basic-first corpus runs
are exploratory revisions and must not be mixed with the final code hash.
Each directory contains `report.json` and `details.json` with paired answers and
retrieval traces. Public output is a development diagnostic; later tuning must
use fresh holdout data. Local gold is intentionally not shipped in a public clone.

`build("basic")` and `build("research")` select modes directly. The organizer's
zero-argument entry point also respects `KNOWLEDGE_MODE`. No model keys or network
access are required. The harness's already-loaded contract types are reused so
its repeat-answer check handles the same text consistently.

## Decision

Keep basic as the default until the alternative demonstrates a quality benefit.
The main observed limitation is shared reader/query coverage. Improve that
before interpreting retriever complexity as progress. Site-wide conflict
enumeration remains step 8; richer interpretation and validation remain steps
7 and 9. This milestone implements the first slice, not the final submission.
