# Current implementation status

Updated 2026-11-06. Earlier draft/comparison documents are retained as historical
records; they are not claims about this revision's score.

Implemented components: contract entry point, synthetic/local evaluation,
immutable ingestion, evidence parser, snapshot/date interpretation, both retrieval
variants, structured tier/model-year matching, bounded extractive/procedural
fallback, table conflict enumeration, shared date resolution, exact-source and
numeric validation, repeatable evaluation, source-only packaging and CI config.

Limitations remain material: complex prose and procedural questions, cross-page
lists, general branch schedules, ambiguous entity equivalence, and nonnumeric
conflict discovery are not comprehensively supported. Unknown comparisons remain
unresolved. A score improvement alone does not establish assignment readiness.
No trained-model experiment has been claimed; the two local retrieval variants
are the evaluated enhancement experiment.

Runtime verification: 29 tests pass on Python 3.11.9 and the installed Python 3.12.
An isolated source archive imports and answers an unknown question conservatively.
The archive excludes snapshots, local gold, reports containing source text, API
keys, and downloaded runtimes. Detailed reports are local under `results/`.

Final paired Python 3.11 public QA scores: basic 0.5561, research 0.5227.
Basic answers 27/40 questions confidently, research 28/40; these counts do not
mean all answers are correct. Basic p95 is 0.123 seconds and ingestion 17.19
seconds; research p95 is 0.234 seconds and ingestion 16.88 seconds. Both runs
show zero quote-integrity or ineligible-source failures. Basic remains default.
The previous organizer run had zero errors and repeat consistency 1.0.
These are public development results, not hidden-test results or semantic
correctness guarantees. Complex lists, prose and conflict questions remain weak.

Organizer self-test: QA 0.8 and conflict F1/resolution 1.0 on its single gold
conflict. The remaining fee question expects an earlier page that disappears
from the later full snapshot; this implementation refuses rather than silently
carrying forward the deleted page. This tiny self-test is not broad validation.

Final code hash: `5859504403d39d8606a972f319f42ef662e0fd8feb2c79d1c6c98bb3ae4994a7`.
Package: ignored `dist/submission.zip`, rebuilt and imported in isolation.

Publication blocker: the connected GitHub account has pull permission but not
push permission on Deep-De-coder/interface.ai; GitHub CLI reports an invalid
token. Restore a write-authorized connection before pushing. No email was sent.
