# Draft implementation plan

Update 2026-11-06: [STEP_5_6_PLAN.md](STEP_5_6_PLAN.md) supersedes the descriptions of steps 5 and 6 in the user-facing 12-step sequence, with a focused research review and simpler snapshot-first design. Its step numbers are separate from this document's section and phase numbers.

Status: proposal, not implemented. Revised 2026-11-06 after a direct adversarial review of [RESEARCH.md](RESEARCH.md), [CASE_STUDIES.md](CASE_STUDIES.md), and the supplied contract/corpus. Two parallel review agents were attempted but stopped at a usage limit; this revision does not claim a completed independent agent review.

## First-principles revision

The assignment, not another repository, defines the design. A snapshot is an observation, a claim needs its scope, a citation needs supporting text, and disagreement requires comparing like with like. Therefore retain observations, retrieve evidence under a date constraint, compare applicable claims, and render only the supported result. Storage technology, extraction strategy, and model choice remain replaceable implementation hypotheses. Prior solutions supply failure examples only; their code, constants, architecture, and scores are not our blueprint.

| Objection to the previous draft | Revision and experiment |
|---|---|
| Too much infrastructure before demonstrating useful answers | Begin with source occurrences, passage/row records, and compact decision traces. Add persistent relation records and full normalization offset maps only when a real case requires them. Original excerpts and source identity are mandatory from day one. |
| Structured extraction may become another brittle hand-coded answer engine | Test numeric, descriptive, list, and missing-evidence cases in the first slice. Inspect whether errors come from retrieval, interpretation, or rendering before choosing rules or a model. |
| A provenance check cannot prove semantic correctness | Deterministically check source membership, quoted text, typed values, units, and dates. Audit semantic entailment separately; matching a number somewhere in a page is insufficient. |
| Multiple temporal fields may create invented precision | Snapshot membership is mandatory. Effective/expiry dates are optional evidence-backed fields. Unknown stays unknown; disagreeing date evidence remains explicit. |
| 100–150 hand-labeled questions delay feedback | Start with 24 development cases and 12 frozen holdout cases, grouped by fact/product family, plus small synthetic mutations. Grow only where observed errors justify coverage. |
| Delaying all model experiments biases the solution toward rules | In the first slice, compare extractive output with a bounded model path on descriptive/ambiguous cases if a model is available. Otherwise record that comparison as untested. Adopt it only for measured benefit. |
| Rich conflict reporting could bury real contradictions in ordinary changes | Keep historical changes and simultaneous contradictions separately labeled internally and evaluate their precision separately. Export meaningful comparable cross-snapshot disagreements as required by the contract, with the distinction in the reason. |

The first slice must answer a current value, its historical version, a qualified tier, a descriptive question, a complete bounded list, an unresolved contradiction, and a missing-evidence question. Change the supporting data and repeat. This establishes whether the decision process follows evidence before broad extraction work begins.

Research spot-check on 2026-11-06: [Sufficient Context (Google Research, 2025)](https://research.google/pubs/sufficient-context-a-new-lens-on-retrieval-augmented-generation-systems/) distinguishes missing context from failure to use available context. That supports separating retrieval and answer errors; it does not establish a reliable automatic truth gate for our corpus. No new literature result is claimed by this revision.

## 1. Objective and design decision

Build an evidence-grounded knowledge system that selects the applicable facts for a question, explains source disagreements, and answers only what its evidence supports. Its distinguishing feature should be a consistent decision process shared by `answer()` and `conflicts()`, with enough provenance to inspect every decision.

Start with Python 3.11, structured records, an embedded SQLite store, and lexical retrieval. Keep raw passages alongside extracted facts. Implement an API-free baseline first; evaluate embeddings or a bounded model-assisted path when measured failures justify them. These are design choices, not claims that a particular technology is universally best.

The public 0.969 result described in CASE_STUDIES.md is a useful reference, not proof of generality. The public conflict pillar is absent, the paraphrase groups are singletons, and one item has a deterministic scoring ceiling. Our acceptance criteria must cover those gaps.

## 2. What to replace, and why

| Fragile approach | Failure | Proposed replacement | Remaining risk |
|---|---|---|---|
| One current value per topic | Destroys history and hides disagreements | Immutable observations plus versioned assertions | Incorrect grouping of assertions |
| Treat latest crawl as effective date | Old offers appear current; future offers activate early | Separate observation, publication, effective, and expiry dates | Missing or ambiguous dates remain unknown |
| Compare bare numbers | APR/APY, products, audiences, and tiers collide | Typed claims with explicit entity, metric, unit, scope, and qualifiers | Entity extraction can still be wrong |
| Merge overlapping tiers into one group | Partial overlap becomes false equivalence | Compare applicability on the actual interval intersection | Complex qualification rules may require clarification |
| Pick newest or majority source | Newer weak sources and repeated boilerplate dominate | Topic-sensitive precedence with explicit reasons and unresolved ties | Authority can be genuinely ambiguous |
| Flatten tables into arbitrary chunks | Values lose headers and footnotes | Preserve page/section/table/row/cell relationships | Irregular markdown needs a fallback |
| Topic-specific constants and refusals | New values are ignored; new evidence cannot reverse a refusal | Extract values and determine answerability from selected evidence | Parsing or retrieval misses can cause false refusal |
| Retrieve top-k and answer immediately | The best match may be stale; lists can be incomplete | Eligibility filters, exact fact lookup, text retrieval, and bounded evidence expansion | Relevant sources may still be missed |
| Ask an LLM to verify itself | The same mistake can survive both steps | Structural checks, evidence-bound values, and separate semantic checks where needed | Prose entailment is not formally guaranteed |
| Attach a plausible URL afterward | Citation exists but does not support the claim | Carry evidence references through the whole pipeline | Evidence-span extraction must be correct |
| Optimize one aggregate score | False refusals and category regressions stay hidden | Category metrics, mutation tests, genuine paraphrases, and a frozen holdout | Small test sets still leave uncertainty |

## 3. Architecture

Ingestion: snapshot -> immutable source occurrences -> parsed structures -> typed assertions -> temporal indexes and conflict relations.

Answering: question -> validated request -> eligible snapshot/evidence -> candidate retrieval -> comparison/resolution -> answerability decision -> rendering -> evidence validation -> contract output.

Keep the following records separate:

- **Source occurrence:** original URL, snapshot ID/date, fetched timestamp, raw content hash, raw text. Identical content can share storage while preserving every occurrence.
- **Evidence span:** source occurrence, raw offsets, section/table identity, relevant header/row/footnote spans, and parser version.
- **Assertion:** entity/product, attribute, typed value/unit, audience, term, balance/model-year bounds, conditions, temporal fields, extraction status, and evidence IDs.
- **Relation:** duplicate, compatible, different scope, historical change, supersession, contradiction, or uncertain comparability; include the evidence and rule behind the relation.
- **Decision:** interpreted request, eligible evidence, accepted and rejected candidates, chosen claims or unresolved alternatives, and reason codes.

Use exact decimal representations for rates and money; routing identifiers and postal codes are strings. Preserve range boundaries and units. Do not derive APR from APY or vice versa without a supported calculation and all required assumptions.

A logical network of assertion/evidence relationships is sufficient initially. A graph server is optional infrastructure, not a requirement for representing relationships.

### A. Ingest without losing the original evidence

Validate snapshot IDs/dates and source identities. Treat each supplied snapshot as the full observed site at that pull. A disappeared page remains historical evidence; do not automatically carry it forward as current evidence or interpret disappearance as product closure.

Store raw text before normalization. Normalize whitespace, escaped line breaks, and footnote markers only through transformations that retain a mapping to original spans. Preserve significant URL parameters and path case; use conservative URL aliases rather than stripping everything after a question mark.

The local audit found 3,294 page occurrences. The latest snapshot contains 72 pages with pipe-table syntax and eight with literal escaped newline sequences. These are heuristic counts, not verified counts of valid tables or parsing errors. They justify testing input normalization and table handling directly.

Deduplicate unchanged content and repeated boilerplate for processing, but retain all source occurrences. Copy counts must not increase evidence authority. Reprocessing must be idempotent and cache keys must include content, parser/schema, and relevant model versions.

### B. Preserve structure and uncertainty during extraction

Parse tables with their heading hierarchy, column meanings, row labels, and associated conditions. Handle repeated headers, tier boundaries, footnote digits beside percentages, ranges, introductory offers, and personal/business variants.

Use generic extractors for entity relationships, contact identifiers, schedules, addresses, events, counts, eligibility, and fees. Avoid rules that encode a particular site's answer. Domain vocabulary and unit rules are acceptable; fixed financial values or missing-answer lists are not.

Validate candidate facts before indexing them as reliable: number/unit compatibility, row/header alignment, evidence-span existence, and qualifier completeness. Keep ambiguous facts and raw passages retrievable with their uncertainty, rather than silently discarding them or inventing missing qualifiers.

Model-assisted extraction, if later added, proposes assertions with exact source spans. It cannot create unsupported values or erase conflicting observations. An absence of extracted facts does not establish absence of information in the page.

### C. Make temporal semantics explicit

Maintain two concepts: **knowledge cutoff** (which snapshot observations may be used) and **fact applicability** (what period an assertion describes). Historical website-state answers cannot use evidence first observed after their cutoff.

Policy to implement and document:

1. `as_of` selects the latest observed snapshot on or before the requested date. Before the first snapshot, report insufficient historical evidence.
2. If `as_of` is absent, interpret explicit historical intent in the question. A year describing a vehicle or a loan term is not automatically a historical date.
3. If neither supplies a historical target, use the latest snapshot as the current knowledge state. Never use the machine's date to silently advance website knowledge.
4. If the API date and a clearly conflicting textual date disagree, return a clarification rather than silently selecting one. Broad references such as a month can be compatible with a specific date within it.
5. Queries beyond the last snapshot can report what the last observation states, including scheduled events, but cannot confirm unobserved later changes. Dates between pulls use the preceding observation and expose that limitation when material.
6. A question about what changed compares eligible endpoints. Preserve both source dates; do not use a global latest winner for every historical answer.

Explicit effective dates are evidence, not automatic truth. Missing end dates stay unknown. A later page version establishes a newly observed value; it does not establish the exact real-world instant of change unless the source says so. Preserve inconsistencies between crawl metadata and stated dates for review.

Entity aliases, summaries, conflict notes, and caches must obey the same cutoff as retrieved facts. Filtering only the final list of URLs would still allow future information to leak through these derived artifacts.

### D. Interpret the question before choosing facts

Create a typed request containing intent, entity candidates, metric, qualifiers, temporal target, output scope, and unresolved ambiguity. Intents include a single value, list, comparison, change history, descriptive explanation, and availability.

Normalize worded/digit terms, common synonyms, currency amounts, and units. Derive entity aliases from eligible source material; never merge entities solely because their names look similar. Distinguish model year, calendar date, loan term, and balance.

Missing qualifiers do not always require a follow-up question. For a general rate/list request, return the supported labeled tiers. Ask for clarification when materially different interpretations cannot be represented accurately in a concise answer. The harness cannot conduct a follow-up dialogue, so avoid unnecessary clarification-only answers.

A bounded model parser can be evaluated later. It must return a validated request over known fields, not arbitrary SQL or invented evidence IDs. On parse uncertainty, retain alternate interpretations or use text retrieval; do not apply a mistaken hard filter with high confidence.

### E. Retrieve enough eligible evidence

Use structured lookup for exact entities/metrics/qualifiers and lexical search over passages for descriptive questions and extraction gaps. A table row hit expands to its necessary headers and conditions. A list request expands across relevant product sections rather than returning the nearest few rows.

Apply snapshot eligibility before content ranking. Hard-filter only explicit, trustworthy constraints. Unknown qualifiers are not matches, but should remain candidates for inspection rather than disappearing without explanation.

On insufficient evidence, allow one bounded expansion: alternate aliases, adjacent sections, and other eligible pages about the same product. Preserve exact evidence for final checks. Only then classify the result as unsupported within the searched snapshot; do not claim that the bank never offers it.

Evaluate dense retrieval and reranking on actual paraphrase misses. Keep them only if they improve evidence recall or answer correctness under the latency budget. Retriever confidence must not become answer confidence by itself.

### F. Resolve disagreements with a shared policy

Compare claims only after checking entity, attribute, unit, audience, conditions, and applicability. Unknown product identity is not permission to collapse claims. For overlapping tiers, reason about their intersection without transitively merging the entire ranges.

Use a precedence relation rather than a single opaque authority score. Relevant signals include direct product applicability, explicit effective/expiry evidence, official schedule status, illustrative-example status, and dated announcement context. URL patterns may assist classification but cannot alone decide truth.

Keep ties unresolved when evidence does not justify a winner. Deduplicate copied claims; do not use document count as a truth vote. Allow any number of legitimate historical values. Large numeric changes are worth inspecting, not an automatic reason to suppress a conflict.

Internally distinguish legitimate historical updates from simultaneous contradictions. Because the contract requests disagreements across and within snapshots, `conflicts()` should include meaningful resolved cross-snapshot changes as well as within-snapshot conflicts, describing the distinction in its reason. Different tiers and mere duplicates are not conflicts. Cover nonnumeric disagreements where assertions are sufficiently grounded; track unsupported comparison types as a known coverage limit.

Precompute reusable comparison groups during ingestion. `answer()` resolves the relevant group at its own cutoff. `conflicts()` uses the same machinery over retained history. An answer's conflict note must reference its entity and scope, not just match a numerical value from an unrelated conflict.

### G. Render only supported claims

The internal decision should distinguish supported, ambiguous, unresolved-conflict, and insufficient-evidence outcomes. Map these conservatively to the contract's text, sources, confidence flag, and optional conflict note. The boolean flag expresses the decision; it is not a calibrated probability.

Render structured values deterministically, including the qualifiers needed to interpret them. Use exact or carefully assembled source excerpts for descriptive answers first. Evaluate bounded prose generation only where extractive output is inadequate. Every generated factual clause must map to accepted evidence; all numbers, entities, temporal qualifiers, and list members require explicit checks.

Citations come from selected evidence records. Preserve raw excerpts, necessary headers, and footnotes; if multiple spans are joined, mark omissions rather than presenting a synthesized sentence as a verbatim quote. Multi-source answers require support for each claim, not one convenient URL.

Keep obsolete alternative numbers in `conflicts()` and the internal audit record. For ordinary current-value questions, the answer text states the selected result and can explain the reason without repeating stale numbers. For genuine change questions, return both supported values with their dates. Do not truncate a list or condition to meet a text-length limit while claiming completeness.

If a final check fails, remove the unsupported clause, regenerate once from the accepted evidence if that path is enabled, or return a precise insufficiency response. Snapshot text is data, never an instruction to the model or tools.

## 4. Practical innovation to demonstrate

These are engineering hypotheses to test, not claims of new academic inventions.

1. **Evidence-linked decisions:** an answer has a compact internal record of its claims, source spans, applicable date, scope, and resolution rule. A reviewer can inspect why it was selected and what could change it. This validates provenance and consistency, not absolute truth of the website.
2. **Reversible answerability:** adding valid evidence turns a refusal into an answer; removing essential evidence turns an answer into a refusal or clearly partial response. This prevents permanent topic-based refusal rules.
3. **Change-based regression tests:** tests alter facts, dates, and source authority while preserving question meaning. They measure whether the implementation follows evidence rather than memorized public examples.
4. **One resolution engine for all outputs:** current answers, historical answers, changes, and conflict reports use the same comparison logic. This makes disagreement between system features testable.
5. **Adaptive effort:** precise lookups take a short deterministic path; ambiguous questions receive bounded retrieval expansion or optional model assistance. Both paths pass the same evidence checks.

The differentiator is reliable behavior under changed data, accompanied by measurable evidence. Adding more agents or services is not itself a success criterion.

## 5. Evaluation design and acceptance gates

Use three separate suites: the unchanged organizer evaluation, a local corpus-derived development/holdout set, and synthetic counterfactual fixtures. Keep expected answers out of runtime indexing and extraction rules.

Initial target: 24 manually checked development cases and 12 frozen holdout cases spanning current values, tiers, historical dates, changes, descriptive facts, bounded lists, contradictions, and insufficient evidence. Add genuine paraphrases to at least six development families. Keep all variants of a fact/product family in the same split. Expand coverage in response to failures rather than requiring a large annotation project upfront. If a held-out failure is used for development, retire it from the holdout and replace it. These small samples diagnose behavior; they cannot support precise generalization estimates.

Essential counterfactual tests:

- Change a source value or schedule; the answer changes accordingly.
- Add a previously missing fact; refusal reverses.
- Remove the sole supporting span; unsupported certainty disappears.
- Add duplicate stale pages or shuffle page order; the winner does not change.
- Add a sixth value or a large legitimate change; the disagreement remains reportable.
- Give two products identical tiers; neither contaminates the other.
- Move an effective date across the question date; applicability changes correctly.
- Change a future snapshot; earlier answers, aliases, notes, and citations remain unchanged.
- Keep all published rows but ask for a complete list; every applicable entry is accounted for.
- Corrupt table structure or detach a footnote; the system detects uncertainty rather than inventing a clean value.

Measure evidence recall, fact extraction errors, entity/tier mistakes, temporal leakage, answer correctness, claim support, list completeness, conflict precision/recall/winner accuracy, false refusals, answer coverage, and consistency. For conflict tests, maintain small manually adjudicated groups independent of the implementation's grouping algorithm.

**Release gates:** all contract tests and explicit invariants pass; zero observed future leakage, unsupported numerical output, or unsupported citations in the fixed adversarial suite; all provided public questions execute; custom category results and unresolved failures are disclosed. These are finite-suite observations, not guarantees for all possible inputs.

**Performance targets:** p95 answer latency at or below two seconds on a documented reference machine, all answers below 60 seconds, and ingestion below 30 minutes. Record cold/uncached as well as repeated calls so caching does not hide poor first-answer behavior. Use a short internal deadline for any optional expensive path, with a grounded fallback. Separate one-time model setup cost from measured ingestion and answer cost and document all three.

Aim toward the default public scoring ceiling without changing the scorer. No promised hidden-test percentage is justified. If a valid grounded answer disagrees with a public expected answer, log and investigate the discrepancy rather than hard-coding the reference.

## 6. Implementation sequence

| Phase | Deliverable | Exit condition |
|---|---|---|
| 0. Contract and evaluation | Importable submission skeleton, unchanged starter benchmark, small independent gold set, temporal policy | Contract runs; risky cases are testable before their implementation |
| 1. First end-to-end slice | Minimal source/passages store, selected table structures, snapshot selection, retrieval, rendering, and small conflict comparison | Seven case types above work end to end; changed evidence changes the output; every claim has inspectable support |
| 2. Structured answers | Typed query parsing, entity/tier matching, snapshot selection, exact numeric rendering and sources | A vertical slice answers current and historical questions across multiple product families |
| 3. Shared conflict engine | Comparability, temporal relations, precedence, unresolved cases, `conflicts()` | Hand-adjudicated groups and mutation tests pass without arbitrary value-count caps |
| 4. Broaden coverage | Extend the early descriptive path, schedules/events/eligibility, complete lists, principled refusal | Broader local questions have verified evidence; no fixed factual answer constants |
| 5. Measured enhancements | Ablations for dense retrieval, reranking, model parsing/extraction or prose generation | Retain only improvements that survive held-out checks and performance limits |
| 6. Submission hardening | Reproducible setup, NOTES, pinned dependencies if any, artifacts audit, final evaluation report | Clean Python 3.11 checkout works with separately supplied kit and required resources |

Each phase should yield reviewable changes and an evaluation report. Build a small end-to-end slice early; avoid constructing the whole storage/extraction system before confirming it can answer correctly. No calendar estimate is asserted until the first slice reveals parsing and coverage costs.

## 7. Initial code boundaries and operating constraints

Start under `submission/` with `solution.py` (contract and orchestration), `evidence.py` (sources, parsing, lookup), and `decisions.py` (scope, time, comparison, rendering). Split responsibilities into additional modules only as implementation complexity warrants. The architecture's record types describe logical responsibilities, not nine mandatory services or modules. `tests/` holds invented fixtures and assertions. An evaluation script outside the submission runs the organizer harness plus local suites.

Use the fixed `build()` / `ingest()` / `answer()` / `conflicts()` boundary. Own return types must remain compatible with the harness, particularly its conflict scorer; test the actual boundary rather than relying on annotations. Repeated questions should not mutate knowledge state.

Do not require a globally installed database, background service, hidden local file, or runtime access to the public evaluation answers. Indexes must be rebuildable from `ingest` inputs. If optional models become dependencies, pin and document their provisioning, licenses, resources, and fallback behavior; a missing key must not silently alter the advertised evaluation mode.

Keep snapshots, extracted site text, embeddings, derived databases, caches, and answer logs containing supplied content local. Before future pushes, extend ignore rules to generated artifacts and inspect the staged file list. Publish synthetic tests and aggregate results. A fresh clone requires the separately supplied participant kit; do not claim the private data arrives with the repository.

## 8. Risks that remain open

- Correct extraction and entity matching are likely the largest sources of error; provenance can expose errors but cannot automatically fix them.
- Some authoritative pages can genuinely disagree without enough evidence to resolve them. Honest unresolved output is necessary.
- A rule-based parser may plateau on unseen phrasing and descriptive facts. A model-assisted alternative should be evaluated, not assumed unnecessary.
- Model-assisted paths introduce cost, latency, reproducibility, and verification challenges. Offline assistance still has to finish within ingestion constraints.
- An overly strict verifier can make an apparently safe system useless through false refusal. Track coverage and quality together.
- Corpus-specific source classification may overfit URL layouts. Test renamed URLs and changed headings with the same evidence semantics.
- Numeric public scoring is an incomplete proxy for reasoning, citation quality, and conflict coverage. Preserve independent tests and reviewer-facing traces.

The first implementation milestone should settle the evidence schema, temporal policy, and a working current/historical answer path before any optional infrastructure is selected.
