# Basic version: adversarial review and next implementation plan

Round 01 — 2026-11-06. Status: review and planning; fixes below are not yet implemented.
Baseline commit: `d16c338` (implementation through `9c6d9db`).
Submission code SHA-256: `3d77b4bf0c03ef94d6b0855fab865793f2208ef11f244d95cf1329112f6ffe02`.

## Purpose and review method

Improve the basic version from observable failure causes. Two agents ran in parallel:
`basic_critic` challenged correctness and scope; `basic_solver` independently
reproduced defects and proposed remedies. They exchanged findings and challenged
the proposed approach. The parent reviewed code, traces and evaluation limits.
No runtime implementation changes belong to this review round.

Use basic mode explicitly in probes. Preserve the research variant as a comparator;
shared parser/reader changes will affect both and must be checked in both modes.
The next work is reader correctness and evidence representation, not replacing the
retriever because a newer method exists. No new web-research claim is made here.

## Baseline and evidence preservation

- 30 existing tests pass. They do not cover the defects below.
- Basic public QA: 0.5561; confident answers: 24/40; p95: 0.439s.
- Research public QA: 0.5227; confident answers: 25/40; p95: 0.507s.
- Both have zero detected citation-text or snapshot-eligibility failures. These
  checks do not establish semantic support, correct scope, or completeness.
- Preserved private baseline: `results/review-rounds/round-01/report.json`,
  `details.json`, and `archive_manifest.json`. Do not overwrite these files.
- Generic reproductions: `scripts/review_basic_round1.py`. These use invented
  evidence, so they can be published without redistributing supplied snapshots.
- Executed 14 diagnostic checks: 4 passed, 10 failed assertions. These are not
  10 independent confirmed bugs: one is an explicitly labeled audience-ambiguity
  policy choice, and several exercise the same root cause. The named-branch
  positive control unexpectedly refuses, adding a coverage concern under B03.
  Raw invented-evidence output is archived as `basic_probes.json` in this round.
  Run with `python scripts/review_basic_round1.py`; it intentionally exits 0 even
  when diagnostic assertions fail. Inspect `passed`, `expected`, and `assessment`.
- Public scores are development diagnostics, not an untouched test set. A low
  score is not sufficient to label an answer false; a high score is not proof
  that the answer's scope is justified.

## Failure ledger — retain IDs across rounds

Priority P0 means a supported-looking answer can misstate the evidence; P1 means
important coverage or consistency failure. Status is open unless explicitly closed.

| ID | Priority / evidence | What goes wrong | Cause and proposed correction | Closure check |
|---|---|---|---|---|
| B01 | P0 / synthetic reproduction | A broad table answer includes a disputed later row while the same narrow row query refuses. | `decisions.py` resolves only the chosen row's comparable scope, then renders other rows from its table. Resolve every output fact before rendering; never return to unvalidated raw rows. | Two sources agree on tier A but disagree on tier B: both broad and narrow B requests expose/refuse the unresolved conflict. Row order must not matter. |
| B02 | P0 / synthetic reproduction | A prose APR range becomes a single lower bound; balance conditions can disappear. | `retrieval.py` captures a numeric prefix and discards the suffix when creating a logical row. Preserve range, units and attached conditions; unsupported expressions remain prose or refuse. | Invented ranges, conditional balances, fee waivers and introductory durations retain their meaning; no bare lower-bound answer. |
| B03 | P0 / synthetic reproduction and public trace | Hours from one branch news article answer a general-hours question. | `extractive.py` removes scope words; neither matching nor validation proves organization-wide applicability. Track branch and evidence scope; require explicit general policy for a general claim. | A single branch cannot establish universal hours. Named-branch questions still work; two branches with different hours cannot yield an unqualified schedule. |
| B04 | P0 / synthetic reproduction and public trace | An unqualified product query selects only a business-card rate; the label survives, but intended audience and completeness are unestablished. | Audience filters apply only when the question explicitly says personal/business; matching product tokens is treated as identity. Preserve audience and rate purpose; report labeled alternatives or ambiguity without silently choosing one. | Personal/business name collisions, purchase/transfer APRs, and unknown audience produce correctly labeled results or refusal. Never assume an absent audience means personal. |
| B05 | P0 / synthetic reproduction | Different products on the same URL become a false conflict when their balance labels match. | `conflicts.py` uses URL, metric and displayed qualifiers but omits product/section identity for unnamed rows. Use a shared fact-scope representation for answers and conflicts. | Maple and Cedar accounts with identical balance tiers remain separate, while genuine competing Maple values still conflict. |
| B06 | P1 / synthetic reproduction and public trace | A multi-route eligibility question returns one family-member bullet as the full answer. | Query intent and fallback select a single matching item; list boundaries and alternatives are not represented. Retrieve the containing eligibility rule group, preserving OR/AND and exclusions. | Three alternative eligibility routes are all represented, with correct logical relation; unrelated neighboring list items are excluded. |
| B07 | P1 / synthetic reproduction | Highest-rate and existence questions refuse despite suitable structured evidence. | Operators such as highest/any become entity tokens or are discarded instead of becoming operations. Parse max/min/exists/count explicitly and apply to resolved, comparable facts only. | Maximum across tiers is correct; ties retained; absence cannot establish 'no' without complete scope; APR and APY are never mixed. |
| B08 | P1 / code and public trace; needs targeted reproduction | Recognition/description answers can be broad or incomplete even with relevant words. | Lexical presence and a single extracted block do not prove that the requested relationship is answered. Add bounded relation-specific readers before making confident claims. | Recognition answer identifies award/recognizing body/time where supported; generic institutional boilerplate is insufficient. Do not treat a missing scorer keyword alone as a factual error. |
| B09 | P1 / known coverage limitation | Valid procedural paraphrases can be rejected by the recent action/object guard. | Exact token inclusion is conservative but is not semantic matching. Add small tested action/object equivalences, negation handling and adjacent-step support, preserving safeguards against unrelated actions and testimonials. | Negative password-vs-contact test stays closed while equivalent profile/contact update instructions are supported. |
| B10 | P1 / code-review hypothesis | Answer resolution and conflict reporting can disagree about time and equivalent values. | `resolve_entries` uses observation date and string values; callers use different normalization/scope paths. Pass an explicit target and share canonical values/scope, keeping observation and applicability separate. | Same facts at the same target resolve consistently; future scheduled values, expired values and cosmetic numeric differences are tested. |

## Scoring observations that must not become hard-coded fixes

Public item `dup-005` has an empty expected-token scoring limitation; its zero
score is not evidence that the displayed certificate values are wrong. Separately,
selecting only a business special-certificate table leaves broad coverage unproven. Item
`dup-087` includes relevant recognition in its cited passage, although it misses
the expected detail: classify as incomplete or unresolved after semantic review,
not automatically fabricated. General-hours items can earn substantial credit
while using branch-specific evidence. Optimize supported meaning, not keywords.

## Implementation sequence and gates

1. **Freeze evidence and encode reproductions.** Preserve this baseline, run the
   diagnostic script, and convert each selected defect into a focused regression
   test when implementing its fix. Add positive controls and order/name/value
   mutations so a blanket refusal cannot pass. Record intended behavior first.
2. **Stop direct numeric misstatements first.** Fix prefix-only prose extraction:
   preserve ranges and attached conditions or refuse unsupported forms. Resolve
   every output row, not just the first chosen row; never render unchecked rows
   from a selected table. Add positive scalar and nonconflicting multirow controls.
   Close B01/B02 with small local corrections before a broad refactor.
3. **Introduce a minimal shared fact scope.** Record product, audience, metric,
   rate purpose, tier/term, branch, source role, observation and applicability.
   Missing qualifiers remain unknown, never wildcards. Keep raw spans alongside
   normalized values. A URL alone merges distinct products; a raw heading path
   alone splits products when headings change. Use explicit identity/alias evidence
   and preserve unresolved equivalence. Do not build a general knowledge graph.
4. **Unify answer and conflict resolution.** Resolve each output fact with the
   same scope, canonical value and explicit target used by conflict reporting.
   Render only resolved facts. A requested complete list with unresolved entries
   must refuse or disclose incompleteness. Close B05, test the B10 hypothesis,
   and rerun B01/B02 to ensure the refactor preserves their protections.
5. **Enforce scope and support complete rule groups.** Distinguish general from
   branch-local claims; retain audience and purchase/introductory purpose. Build
   section-bounded list/rule groups with alternatives and requirements. Close
   B03/B04/B06 without defaulting to personal products or merging adjacent lists.
6. **Add bounded query operations and procedural coverage.** Implement max/min,
   existence and count over resolved facts with explicit completeness checks.
   Separate a request for a link from a numerical rate request. Add relation and
   procedural readers only with positive/negative fixtures. Address B07–B09;
   keep ambiguous relative dates explicit rather than inventing calendar meaning.
7. **Run the critic/solver round again and publish measured changes.** For each
   logical fix, run targeted regressions, then the existing suite. At a coherent
   milestone, run the public basic evaluation and paired research comparison,
   inspect changed answers, verify the source-only package and update this ledger.
   Push real milestones to main using short names such as `Resolve every output
   fact` or `Preserve rate conditions`. No artificial delays or rewritten history.

## How to record failures and failed fixes

Keep this file as the public, append-only decision record. Keep private source
quotes, raw answers and full traces under ignored `results/review-rounds/round-NN/`.
At each new round, use a new directory and record the code commit/hash, mode,
Python version, corpus/question hashes and run order. Never overwrite a prior
round or commit supplied website excerpts. Generic test fixtures are publishable.

For every failure or attempted fix append a row using this schema:

| Round / date | Failure ID | Reproduction or question ID | Expected vs observed | Cause: confirmed or hypothesis | Attempt / commit | Verification and regressions | Decision / next action |
|---|---|---|---|---|---|---|---|
| 01 / 2026-11-06 | B01–B07 | Generic diagnostic probes and private baseline | See ledger above | Reproduced symptoms; cause supported by code review | No implementation change | Existing 30 tests pass despite gaps | Open; implement in sequence above |
| 01 / 2026-11-06 | B03 | branch-scope-named-control | Named Oak question refuses despite its schedule being present | Coverage symptom reproduced; exact matching cause needs isolation | No fix attempted | General scope fails; absent Pine correctly refuses | Add named-branch support while fixing generalization |
| 01 / 2026-11-06 | B04 | audience-ambiguity / audience-personal-control | Unqualified question returns labeled business rate; explicit personal correctly refuses | Ambiguity policy concern, not a fabricated value | No fix attempted | Record separately from proven wrong-value cases | Decide answer qualification/completeness policy before implementing |

A failed attempt stays in the log: state what it tried, which counterexample
still fails, and whether the change was retained, revised or reverted. A new
score alone cannot close an issue. Close only after its reproduction passes,
positive controls remain supported, and affected public answers are inspected.
Reopen the same ID on recurrence instead of creating a disconnected new issue.

Record per round: confident semantic errors, incomplete answers, false refusals,
unresolved conflicts, per-family results, public QA, citation checks and latency.
Manually reviewed semantic labels must include a brief rationale; do not label
all zero-score answers errors. No metric is allowed to hide a newly introduced
confident error. A temporary score reduction can be accepted for a demonstrated
scope correction, but must be recorded and reviewed explicitly.

## Completion boundary

This is a revised plan, not a claim that the problems are fixed or the assignment
is ready. Start the next implementation round with the direct B01/B02 corrections,
then the minimal shared scope and B05. Reassess complexity after each gate; preserve the simple basic
retriever until evidence shows retrieval itself is the remaining bottleneck.
