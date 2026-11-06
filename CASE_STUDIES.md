# Existing solutions: exact assignment and closely related systems

Reviewed **2026-11-05 (America/New_York)**. Companion to `RESEARCH.md`: that file explains research directions; this file examines implementations, results, improvements, and failures.

## What the search established

**Yes: a public implementation of this exact assignment exists.** I verified one repository with the same five snapshot dates, three-method Python contract, and 40-question practice evaluation. It reports a strong public score, but I found neither an organizer-certified hidden score nor evidence that the full problem is solved.

I also examined two CRAG competition solutions and two temporal-memory implementations. These address relevant parts of the problem, but their scores cannot be compared directly with the assignment score.

Evidence labels used below:

- **Official result:** published by the competition organizer.
- **Author-reported result:** recorded in a project's documentation or paper; not reproduced in this review.
- **Code observation:** a behavior or rule visible in inspected source code.
- **Assessment:** our interpretation or proposed test, not a measured failure on a hidden dataset.

No external implementation was executed, installed, or copied into our solution. The one local calculation below checks our supplied evaluation's scoring arithmetic, not the external solution's performance.

## 1. Exact assignment: ram290476/credit-union-knowledge-system

**Repository:** [credit-union-knowledge-system](https://github.com/ram290476/credit-union-knowledge-system).

**Inspected revision:** `ea53b880b1a79156ddec96c437d23ce5207966ca`, dated October 24, 2026. Source links below are pinned to that revision so future edits do not change what this review describes.

### Method and what it improved

The implementation replaces the starter's latest-page keyword matching with an in-memory versioned store, markdown passage/table parsing, qualified numerical facts, rule-based question dispatch, and deterministic answers. Facts retain source URLs and snapshot identifiers. Historical lookup chooses the latest snapshot on or before `as_of`. Source-ranking rules prefer selected product/rate pages to calculators and promotional material. No runtime LLM or network service is required. These mechanisms are documented in the [README](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/README.md) and [NOTES](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/NOTES.md), with version retention visible in [store.py](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/store.py).

This is a useful demonstration that the assignment does not inherently require a vector database, LLM, or graph database. It does not establish that this particular set of rules generalizes.

### Reported results

The author's October 24 practice run reports:

| Measurement | Reported value |
|---|---:|
| Public questions | 40 |
| QA score / final score | 0.969 |
| Stale-trap hits / execution errors | 0 / 0 |
| Consistency | 1.0 |
| Answer p95 | 0.15 seconds |
| Ingestion | 7.5 seconds |
| List-completeness category | 0.75 |
| Other public categories | 1.00 |

These are **author-reported**, not independently rerun results. The README states that the conflict pillar was omitted because the public run lacked conflict gold, and the remaining weights were renormalized. Source: [practice score](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/README.md#practice-score).

The single reported zero-score question is `dup-005`: its required-token list is empty, so the default deterministic scorer assigns zero correctness unless the optional judge supplies a score. I independently checked our local kit: the item weight is 2.0, total question weight is 64.5, and `1 - 2/64.5 = 0.968992...`. Thus **0.969 is consistent with the default public scoring ceiling when every other item is perfect**. This is a scoring limitation, not evidence that the generated list was wrong or complete. The local sources are `hackathon-knowledge-kit-participant/eval/public_eval.jsonl` and `harness/scoring.py` within that kit.

A second local check found that all 20 nonempty public paraphrase groups contain only one question each. Therefore the reported public paraphrase-consistency component does not demonstrate consistency across different wordings; repeat checks test repeating the same question. We need genuinely multi-question paraphrase groups of our own.

### Where the code has limitations

The README says practice answers are not hard-coded. Inspection gives a more qualified picture: many rates are extracted, but several answer paths contain specific factual constants or expected phrases. The observations below are visible in code; the consequences are assessments, not claimed hidden-test results.

| Code observation | Why it matters | Evidence |
|---|---|---|
| Certain rate topics trigger unconditional refusal before evidence lookup | If a future or synthetic snapshot publishes the rate, the system still refuses; missingness is encoded as a topic rule | [`_asks_unpublished_rate`, lines 122-128](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/answer.py#L122-L128) |
| Routing-number selection searches for one predetermined number; recognition and assistance-program paths search for predetermined wording/values | A changed value or differently worded source can be missed despite being present | [`_dispatch`](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/answer.py#L53-L101), [`_routing`](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/answer.py#L157-L169) |
| Hours answers contain fixed schedules after finding a loosely matching page; citation excerpts can be only a label | The cited page's existence does not establish that its actual schedule supports the answer | [`_hours`, lines 261-291](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/answer.py#L261-L291) |
| The strict conflict key deliberately excludes product words | Different products with identical metric, term, tier, and flags can be grouped together | [`_group_key`](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/conflicts.py#L68) |
| Conflict groups with more than four distinct values are discarded; numeric spreads above eight are also discarded | Five real updates or a large legitimate change can disappear from the conflict report | [`_build_conflict`](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/conflicts.py#L191) |
| Conflict winners prioritize crawl date, then URL-path authority | Explicit effective periods, delayed announcements, and authority ties are not fully modeled by this rule | [`_build_conflict` and `_authority`](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/conflicts.py) |

The conflict detector also restricts comparison to a small set of numerical metrics. The public score therefore does not demonstrate general detection of contradictory prose, addresses, or branch status. Its term parser recognizes digit-based terms; worded terms deserve independent paraphrase tests. These points are visible in [conflicts.py](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/conflicts.py) and [`_matches_constraints`](https://github.com/ram290476/credit-union-knowledge-system/blob/ea53b880b1a79156ddec96c437d23ce5207966ca/knowledge/answer.py#L474-L518).

### What we should take from it

Adopt the architectural ideas of version retention, qualified facts, table-aware extraction, and cheap deterministic numeric answers. Improve generality through entity-safe conflict keys, evidence-derived output, missingness checks based on the selected snapshot, and tests that change source facts while leaving questions unchanged. Do not use a near-perfect public score as proof of hidden conflict quality or robust paraphrase handling.

## 2. CRAG competition winner: team db3

**Sources:** [technical report](https://arxiv.org/html/2410.00005v1), [organizer's final scores](https://discourse.aicrowd.com/t/final-evaluation-process-team-scores/10785), and [code location linked by the authors](https://gitlab.aicrowd.com/jiazunchen/kdd2024cup-crag-db3). The code location was not inspected or run here.

**Method:** parent-child passage retrieval, reranking, a model tuned to reduce hallucination, and structured knowledge retrieval through generated calls to a constrained API set. The change from basic RAG was better evidence selection plus targeted access to structured facts.

**Official results:** first place in all three tasks; final scores **28.4%, 42.7%, and 47.8%**. These are CRAG competition scores, not percentages of correct answers and not assignment-equivalent scores.

**Limits:** the report describes a 30-second query budget and model-switching difficulties in its inference environment. API parsing and efficiency remain improvement areas. Gains across tasks cannot isolate one technique because available evidence also changes.

**Our assessment:** retrieve narrowly but retain parent context; expose structured facts through validated operations. Their external-data path and model-training stack are not a direct fit for our snapshots-only, two-second-target setup. Success here supports structured evidence access, not copying the whole system.

## 3. CRAG runner-up: team APEX

**Sources:** [report, Tables 1-2 and section 4](https://arxiv.org/html/2409.15337v1), [implementation README](https://github.com/USTCAGI/CRAG-in-KDD-Cup2024), [official final scores](https://discourse.aicrowd.com/t/final-evaluation-process-team-scores/10785).

**Method:** domain/dynamism routing, BM25 preselection, dense retrieval, reranking, entity matching, time extraction, and selective refusal. Structured API results supplement web evidence.

**Official outcome:** second place on Tasks 2 and 3, with final scores **41.0% and 44.9%**. The report's ablation scores below use its experimental evaluation and must not be substituted for those official results.

| Author-reported comparison | Without component | Full system |
|---|---:|---:|
| Task 2 score: time extraction | 18.45% | 31.22% |
| Task 2 score: entity matching | 21.44% | 31.22% |
| Task 3 time: pre-ranking | 68.17 s | 5.96 s |

**Failures/tradeoffs:** report Task 3 accuracy is 48.21%, hallucination 16.56%, and missing answers 35.23%. The authors acknowledge refusal is a basic response to dynamic questions and manually designed API rules may not scale.

**Our assessment:** test temporal parsing and entity matching independently. Cheap preselection merits measurement. Avoid a blanket “changing fact means refuse” policy when our selected snapshot supplies evidence.

## 4. Zep / Graphiti: implemented temporal knowledge graphs

**Sources:** [Zep paper, Tables 2-3](https://arxiv.org/html/2501.13956v1) and [Graphiti implementation](https://github.com/getzep/graphiti).

**Method:** incremental source-linked facts with temporal validity, historical retention, and retrieval over a graph. This replaces repeatedly supplying the entire conversation history.

**Author-reported LongMemEval-s results with GPT-4o:** full-context score **60.2%**, Zep **71.2%**; reported latency **28.9 s → 2.58 s**; average context approximately **115,000 → 1,600 tokens**. The accuracy difference is **11.0 percentage points**, not 18.5 points.

**Where it regressed:** GPT-4o single-session-assistant questions fell **94.6% → 80.4%**. With GPT-4o-mini, knowledge-update questions fell **76.9% → 74.4%**. Aggregate gains did not improve every category.

**Our assessment:** compact temporal evidence can help, but preserve access to original passages for omitted details. These are conversation-memory results from a vendor-authored paper, not independent evidence on our tables. The reported latency is not our p95 and does not prove compliance with our speed target. Current Graphiti code should not be assumed identical to the paper's evaluated system.

## 5. TEM: version preservation with explicit historical labels

**Sources:** [October 2026 paper](https://arxiv.org/html/2610.21900v1) and [implementation overview](https://github.com/sungkites/TEM).

**Method:** retain source-linked fact versions, order them, and mark superseded records; supplement structured facts with original dialogue/event evidence.

**Author-reported improvement:** on 420 controlled state-update questions, adding labels to otherwise identical ordered facts increased key-entity hit rates by **17.14-55.95 percentage points** across four backbones.

**Where it did not generalize:** labels added little overall benefit on LoCoMo. The paper assumes explicit single-valued updates in source-session order; delayed reports and simultaneous conflicts require stronger temporal modeling.

**Reproducibility limit:** the repository explicitly says its executable code is an illustrative versioned-memory example, not the complete experiment. It lacks extraction, semantic retrieval, full benchmark scripts, and per-question outputs. The example cannot reproduce the reported tables.

For Llama-3.1-8B on LoCoMo, the README reports **27.53-29.22%** for TEM versus **37.66-39.55%** for a much larger-context reference. These ranges reflect unresolved evaluations, not confidence intervals. Thus compact evidence improved the same-budget comparison but did not beat every alternative.

**Our assessment:** test historical labels cheaply; do not adopt “latest observed means effective now” as a universal update rule.

## What the evidence says collectively

| Question | Supported conclusion | Still unproven |
|---|---|---|
| Has anyone implemented our exact task? | Yes, one matching public repository verified | Hidden score, complete conflict coverage, robustness to changed facts |
| Can simple methods score well here? | The exact-match author reports near-ceiling public performance without LLM calls | Generality of its narrow answer rules |
| Is more retrieved text always better? | The examples motivate selection and structured access | Which retrieval mix wins on our corpus |
| Does adding time information matter? | APEX and TEM report useful ablations in their settings | The size of the benefit on our assignment |
| Are temporal graphs a complete solution? | Zep improves aggregate results in its evaluation | Universal improvement; some categories regress |
| Does a repository make research reproducible? | Sometimes it supplies useful implementation material | TEM explicitly does not release the complete experiment |

These are case-specific conclusions. No common ranking is meaningful across these datasets or scores. In particular, 96.9% public assignment score, 47.8% CRAG score, and 71.2% LongMemEval score measure different things.

## Concrete improvements to test in our own solution

These are proposed tests derived from the review, not tests already run against the external repositories.

1. **Value substitution:** replace a source rate, routing identifier, schedule, or award count in a synthetic snapshot. The answer must follow the changed evidence rather than a constant.
2. **Newly published answer:** add evidence for a previously unlisted product rate. A former refusal should become a sourced answer.
3. **Five distinct versions:** introduce a legitimate change in each snapshot. History and conflict reporting must not disappear at an arbitrary count threshold.
4. **Product collision:** give unrelated products identical terms and balance tiers. Their facts must remain separate.
5. **Large changes:** change a fee substantially. Classify the relationship from product/metric/scope evidence, not numeric distance alone.
6. **Effective versus observed dates:** insert a delayed announcement and a future-effective offer. Test both current and historical questions.
7. **Source-backed hours:** alter the schedule while preserving headings. Verify the returned hours and source excerpt agree.
8. **Paraphrase and unfamiliar topics:** use worded numbers, synonyms, and source-supported topics absent from the public questions.
9. **Balanced abstention:** measure false refusals as well as unsupported answers. Higher refusal rates alone do not demonstrate improvement.
10. **Category-level reporting:** preserve current-value, historical, conflict, citation, list, and refusal results separately so aggregate gains do not hide regressions.

The practical opportunity is to keep the exact solution's inexpensive structured pipeline while addressing its visible generalization gaps, then add learned retrieval or generation where measured failures justify it.

## Search and verification record

Searches included the assignment title, participant-kit name, `interface.ai` plus snapshots/knowledge, the Dupaco/Python contract terms, and targeted searches for CRAG implementations and temporal-memory results. A mirrored wiki led to the exact match; findings were then verified through the original GitHub repository rather than relying on the mirror.

Only one exact-match repository was verified in this search. This is a search result, not a claim that no others exist. General BankGPT event pages and promotional banking-AI claims were excluded because they did not establish results on this task. No official interface.ai hidden leaderboard or reviewed-commit result was located.

For future use, keep exact-task evidence separate from analogous benchmarks. Record the code revision, dataset, metric definition, evaluation setting, and whether a result was reproduced whenever adding a new case.
