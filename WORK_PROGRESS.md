# Live continuation record

Updated 2026-11-06. Read this file first after context compaction. User explicitly
requests continuing remaining work and documenting exactly where work stopped.

## Objective and constraints

Complete the interface.ai knowledge assignment from five supplied full-site
snapshots. Preserve first-principles implementation; do not copy another public
solution or hard-code its answers. Keep basic and research retrieval variants
and their research drafts. User authorized implementation, evaluation and Git
publication; no submission email has been authorized or sent.

Workspace: `C:/Users/esote/Downloads/interface.ai` (PowerShell).
Repository: `https://github.com/Deep-De-coder/interface.ai.git`.
Current branch: `main`. User explicitly requested publishing to main on
2026-11-06; main was fast-forwarded and pushed through code commit `9c6d9db`.
Use main for subsequent authorized incremental pushes. The prior
`codex/knowledge-system` branch remains available.
Git uses `-c safe.directory=C:/Users/esote/Downloads/interface.ai`.
Git metadata and network writes may need tool escalation. Git push WORKS with
stored credentials, despite `gh auth status` failing and connector push=false.

## Implemented

- Immutable chronological snapshot occurrences, content deduplication, exact
  original text/spans, conservative table and escaped-newline parsing.
- Explicit snapshot/date selection; effective/expiry dates; comparisons;
  historical month handling and protection against treating balances as years.
- Basic overlap and research BM25/hierarchy ranking. Basic remains default.
- Numeric table reader with tiers, model-year ranges, named entities, full
  structured candidate scan (prevents top-k from hiding newer schedules).
- Explicit APY/APR/rate prose facts, limited extractive/procedure fallback,
  routing identifiers, and cross-page card list assembly.
- Table/prose-rate conflict enumeration; known named products can compare across
  URLs, unknown entity equivalence remains URL-scoped. Shared resolution helper.
- Final source eligibility, exact quote and numerical provenance validation.
- Source-only ZIP packaging, isolated import verification, CI configuration.

## Previous verified checkpoint

29 tests pass on Python 3.11.9 and installed Python 3.12.
Final paired run before this progress file: basic QA **0.5561**, research
**0.5227**, on 40 public questions. Basic confidently answers 27/40, research
28/40; these are coverage counts, not correct-answer counts. Basic p95 .123s,
ingestion 17.19s; research p95 .234s, ingestion 16.88s. No quote-integrity or
ineligible-source failures in either run. Code SHA-256:
`5859504403d39d8606a972f319f42ef662e0fd8feb2c79d1c6c98bb3ae4994a7`.

Organizer self-test: QA .8; conflict F1 and resolution 1.0 on ONE gold conflict.
Remaining self-test fee expects a page absent from latest full snapshot. Do not
silently carry that disappeared page forward merely to satisfy scorer.

Reports: `results/comparison/public/research-first/{report,details}.json` (latest
paired run); `results/submission` is slightly earlier, before final card plural
normalization. Detailed reports contain private source text and are ignored.
`dist/submission.zip` and `dist/manifest.json` are ignored, rebuilt from allowlist.

## Immediate next work

1. Inspect latest paired details alongside public questions; classify remaining
   failures into retrieval, scope interpretation, source conflict, rendering,
   and genuinely missing evidence. Do not encode gold values in runtime code.
2. Prioritize incomplete cross-page lists, prose financial facts/conditions,
   general versus branch-specific schedules, and conflict winner semantics.
3. Expand independent synthetic mutation tests for each repaired behavior.
4. Re-evaluate only after meaningful changes; retain honest category/coverage
   results. No hidden-test score or semantic safety guarantee is established.
5. Update documentation, rebuild/verify ZIP, audit staged paths, commit and push
   progress to the same branch. Verify remote/CI if accessible.

Do NOT say all work is complete or submission-ready: public quality is still
limited, nonnumeric conflict discovery is incomplete, and unknown entity scope
can cause refusals. The user has asked to continue these remaining gaps.

## Runtime and commands

Python 3.11 embeddable runtime downloaded from official python.org into ignored
`tmp/python311`. Its isolated path setup needs explicit workspace insertion for
unittest; standalone scripts already add repository paths.

```powershell
./tmp/python311/python.exe -c "import sys,unittest; sys.path.insert(0,r'C:\Users\esote\Downloads\interface.ai'); r=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('tests')); sys.exit(not r.wasSuccessful())"
./tmp/python311/python.exe scripts/compare_variants.py --suite public --order research-first
./tmp/python311/python.exe scripts/evaluate.py submission
./tmp/python311/python.exe scripts/verify_release.py
```

Dataset: ignored `hackathon-knowledge-kit-participant/`; contract in
`harness/contract.py`. Five snapshots, 3,294 occurrences, newest 2026-09-28.
Default now = newest snapshot, not wall clock. API as_of selects preceding pull.
Python >=3.11; no dependencies or API keys. No model experiments run.

Ignore rules exclude kit ZIP/PDF/snapshots, results, local_eval, tmp, dist,
databases, caches and secrets. Never commit supplied website text or API keys.
Research files and earlier plan/results are historical artifacts; preserve them.

## Evaluation caveats and known implementation risks

- Public scorer has 40 questions, singleton paraphrase groups, no full conflicts
  gold; one empty-token item has a deterministic score ceiling.
- Synthetic holdout was inspected to fix dollar/year confusion; its post-fix
  12/12 is a regression result, not untouched holdout evidence.
- Local corpus gold has eight checked development examples; alternate source
  URLs may correctly support answers. URL recall is not evidence sufficiency.
- Scope normalization is conservative and incomplete. Comparing whole displayed
  qualifier tuples can miss equivalent products/tables with different headers.
- Prose fallback is lexical/extractive, not an entailment model. Numeric checks
  do not establish semantic relevance; inspect confident errors carefully.
- Broad rate/list outputs may omit conditions or relevant alternative products.
- Temporal metadata ambiguity must not be hidden by ranking preferences.

## Latest checkpoint: procedural evidence guard

Progress documentation pushed as 86bfe90. Full prior implementation was already
published as bab82b8; do not recreate or backdate step commits. User requests
short professional commits and incremental pushes as real milestones complete.

Added shared action/object matching for procedural reader and extractive fallback,
plus a negative/positive snapshot mutation test. Reject blockquote testimonials.
30 tests pass on Python 3.11.9 and 3.12; isolated release verification passes.
Latest paired public scores remain basic .5561 / research .5227, confidence
coverage falls to 24/40 and 25/40. Source integrity and eligibility failures: zero.
Basic p95 .439s / ingestion 35.26s; research p95 .507s / ingestion 25.23s.
Code hash: 3d77b4bf0c03ef94d6b0855fab865793f2208ef11f244d95cf1329112f6ffe02.
Reports at the same ignored public/research-first paths now describe this change.

Next: repair missing personal card rows and entity audience ambiguity; inspect
branch-specific hours being used for general hours. Procedural lexical matching
is conservative and may reject valid paraphrases; do not claim semantic proof.
Remaining scope/list/prose/conflict gaps above still apply.

## Latest checkpoint: basic adversarial review, round 01

User requested parallel critic/solver agents and a new plan with persistent
failure records. Agents `basic_critic` and `basic_solver` audited basic mode,
exchanged critiques, and reproduced defects using invented evidence. No runtime
fixes were made during this planning round. Read `BASIC_REVIEW_PLAN.md` next:
it supersedes the immediate next-work ordering above and defines stable B01–B10
failure IDs, acceptance gates, failed-attempt logging and private evidence rules.

Baseline commit is d16c338 on main. Original evaluation files were copied to
ignored `results/review-rounds/round-01/` with a checksum manifest. Preserve them.
`scripts/review_basic_round1.py` provides reusable basic-only diagnostics;
inspect per-case passed fields, since diagnostic findings intentionally exit 0.
Existing 30 tests pass despite these newly demonstrated gaps.
Completed diagnostics: 14 checks, 4 passed and 10 failed assertions, including
one explicitly labeled audience-policy concern rather than a proven false value.
Archived output: `results/review-rounds/round-01/basic_probes.json`. Named-branch
positive control also refuses; record this coverage issue under B03.

Next implementation: first preserve prose ranges/conditions and resolve every
rendered table row (B01/B02), then establish shared evidence-backed fact scope
and consistent answer/conflict resolution (B05). After that address branch and
audience scope, list completeness, and query operations. No blanket refusal or
public score increase alone closes an issue. Append new attempts/results to the
new plan and archive detailed outputs in a fresh round directory.
