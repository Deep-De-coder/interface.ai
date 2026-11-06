# Research reference: a knowledge system that knows what is true now

Research cutoff: **2026-11-05 (America/New_York)**. Maintained as the single research reference for this repository.

## Scope and evidence standard

This review covers only the assignment's needs: five dated website snapshots, current and historical question answering, conflicting sources, table/tier interpretation, citations, and abstention under a tight answer-time budget. It compares established methods with selected 2025-2026 work. It is a focused literature search, not an exhaustive survey or a claim to have found every latest paper.

Primary sources were checked: original papers on arXiv, conference proceedings, ACL Anthology, and the researchers' publication page. The newest selected paper was submitted on October 30, 2026. Search-result crawl dates were not treated as publication dates. Papers described below as preprints have no peer-review status established by this review. No experiments from these papers were reproduced here.

**Evidence versus judgment:** descriptions of methods and reported results are attributed to the linked papers. Statements about suitability, engineering cost, and what we should adopt are our project-specific assessment. Results on different datasets, generators, and evaluation protocols are not comparable leaderboard scores and do not predict our assignment score.

External research informs the design only. The eventual system must answer credit-union questions exclusively from the supplied snapshots. This review does not copy or redistribute their content.

## Main conclusion

Start with a versioned, source-linked fact store and a structure-preserving retrieval pipeline. Resolve date, entity, metric, and tier constraints before generating an answer. Use an explicit evidence-sufficiency decision and produce citations from stored evidence. Keep text retrieval for facts that structured extraction misses.

This is a design hypothesis supported by the directions below, not an implemented or benchmarked solution. A graph database, multi-agent debate, model training, and a large agent framework are not prerequisites. We should add complexity only after a controlled local comparison shows a benefit.

## What was used before, and why research moved on

| Earlier approach | Why it helped | Failure relevant to this assignment | Newer direction |
|---|---|---|---|
| Model knowledge alone | Simple inference; broad language understanding | Cannot establish which supplied snapshot supports an answer | Retrieval with explicit provenance [1, 3] |
| Retrieve a fixed number of similar text chunks | Easy document ingestion and broad question coverage | Similarity does not enforce date, tier, or source authority | Temporal ranking and explicit query constraints [4, 5, 8] |
| Keep only the latest extracted value | Compact current-state lookup | Loses historical answers | Versioned records and temporal status [6, 7] |
| Keep every version without labeling it | Preserves information | Generator may mix current and obsolete facts | Mark history and select eligible evidence [5, 7] |
| Flatten tables into ordinary text | Reuses a text-only retrieval pipeline | Separates values from headers, units, and qualifiers | Structured table retrieval and execution [9, 10] |
| Ask the model to cite and admit uncertainty | Low implementation cost | Citations may not support claims; plausible bad evidence still induces answers | Citation evaluation and sufficiency gates [3, 11-13] |
| Concatenate disagreeing documents | Exposes competing evidence | Does not ensure correct disambiguation or resolution | Explicit conflict analysis [14] |

The failure column is our application-level interpretation; it is not a claim that every older system necessarily fails.

## Selected research: mechanism, benefit, limitation, and decision

### 1. Original RAG — NeurIPS 2020

**Source:** [Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html).

**Previous problem and improvement:** parametric-only generation made knowledge updates and provenance difficult. RAG combined a generator with a retrieved external memory, using a dense Wikipedia index in the paper.

**Pros:** establishes the retrieval-plus-generation foundation; knowledge can be supplied outside model parameters.

**Cons for us:** retrieval relevance alone does not establish the right snapshot, an authoritative source, or a correctly matched product tier. Retrieved evidence is not automatically a verified citation.

**Decision:** retain a simple retrieval baseline to measure progress, but do not treat a vector index as the complete knowledge system.

### 2. Self-RAG — October 2023 paper

**Source:** [Asai et al., Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://arxiv.org/abs/2310.11511).

**Previous problem and improvement:** fixed retrieval can introduce irrelevant passages. Self-RAG trains a model to control retrieval and critique evidence and generation using reflection tokens.

**Pros:** treats retrieval relevance and answer support as decisions rather than assuming all retrieved passages help.

**Cons for us:** reproducing the method involves a trained model and specialized inference behavior. Self-critique is not an independent truth oracle; it does not supply our temporal rules.

**Decision:** borrow the separate retrieve/check/answer stages. Defer training and repeated critique loops unless simpler checks fail within our latency budget.

### 3. ALCE — EMNLP 2023

**Source:** [Gao et al., Enabling Large Language Models to Generate Text with Citations](https://aclanthology.org/2023.emnlp-main.398/).

**Previous problem and improvement:** fluent answers and attached references were hard to evaluate reproducibly. ALCE evaluates answer correctness, fluency, and citation quality separately.

**Pros:** distinguishes having a citation from having evidence that actually supports a claim; useful evaluation design for our source requirements.

**Cons for us:** entailment-style citation checks can still miss date, unit, and tier mismatches unless those qualifiers are included in the claim and evidence. The benchmark is not this website corpus.

**Decision:** retain URL, snapshot ID, exact supporting text, and location during ingestion. Check factual claims against that evidence, not merely whether the URL exists.

### 4. MRAG — Findings of EMNLP, November 2025

**Source:** [MRAG: A Modular Retrieval Framework for Time-Sensitive Question Answering](https://aclanthology.org/2025.findings-emnlp.167/).

**Previous problem and improvement:** generic retrievers struggle when relevance depends on temporal reasoning. MRAG separates question content from temporal constraints, retrieves and summarizes evidence, and scores semantic and temporal relevance separately. It introduces TempRAGEval.

**Pros:** modular and training-free; directly relevant to historical questions and independently testable retrieval stages.

**Cons for us:** summaries may omit qualifiers; query processing and summarization introduce cost and possible errors. A time-aware ranking score alone is insufficient to enforce snapshots-only historical access.

**Decision:** parse temporal intent explicitly. Apply the eligible-snapshot constraint first, then rank evidence within the allowed material.

### 5. TimelyRAG — September 10, 2026 preprint

**Source:** [TimelyRAG: Semantic-Temporal Hybrid Retrieval for Time-Critical Question Answering in Overlapping-Evolving Documents](https://arxiv.org/html/2609.11572v1).

**Previous problem and improvement:** successive versions can be almost identical in wording but apply at different times. TimelyRAG reranks a candidate pool using semantic relevance and temporal compatibility, distinguishing insertion time from event time and using fallbacks when temporal evidence is incomplete.

**Pros:** can sit above different retrievers; addresses version ambiguity without requiring retriever retraining.

**Cons:** cannot recover evidence absent from the initial candidate pool. The paper notes difficulties with temporal extraction and complex temporal logic; TimelyQABench is synthetic and regulation-focused.

**Decision:** adopt separate observed and effective dates and test temporal reranking. Our snapshot eligibility rule remains a hard constraint. A recently crawled page is not necessarily a recently effective fact.

### 6. Zep / Graphiti — January 20, 2025 preprint

**Source:** [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/html/2501.13956v1).

**Previous problem and improvement:** static retrieval does not maintain changing relationships. Zep describes source-linked facts with event-validity and system-ingestion timelines, including invalidation of superseded facts.

**Pros:** useful separation of when a fact holds from when it enters the system; provenance supports tracing facts back to evidence.

**Cons for us:** the paper's evaluations concern conversation memory. Extraction and entity resolution can introduce errors; graph infrastructure adds operational complexity. These results do not establish superiority on website rate tables.

**Decision:** borrow the temporal/provenance schema. Initially implement it with ordinary records or SQLite rather than committing to a graph service.

### 7. TEM — October 15, 2026 preprint

**Source:** [TEM: Temporal State Tracking Memory for Large Language Model Agents](https://arxiv.org/html/2610.21900v1).

**Previous problem and improvement:** overwriting loses old facts, while retaining unlabeled versions leaves the generator to infer their status. TEM preserves source-linked versions and explicitly marks historical records.

**Pros:** an ablation holds facts and their order constant, providing evidence that historical labels can help beyond merely preserving history.

**Cons:** its controlled update task assumes explicit single-valued updates in source-session order. The authors identify delayed reports and within-session contradictions as limitations. Historical labels made little overall difference on LoCoMo; effects were task-dependent. Key-entity hits are weaker than full factual correctness.

**Decision:** retain versions and label their status. Do not infer business-effective time solely from crawl order, and do not copy TEM's update rule unchanged.

### 8. KITE — October 30, 2026 preprint

**Source:** [KITE: Retrieval as a Decision Procedure for Long-Term Conversational Memory](https://arxiv.org/html/2610.41521v1).

**Previous problem and improvement:** similarity ranking does not guarantee satisfaction of a question's conditions. KITE organizes memories under a controlled topic vocabulary and compiles queries into inspectable plans with fixed execution and ranking, supplemented by sparse lexical retrieval.

**Pros:** explicit filters and operations make retrieval failures inspectable; a useful direction for matching product, term, metric, and date.

**Cons for us:** very recent, evaluated on conversational memory rather than our corpus. Index construction and query compilation can be wrong. Fixed plan execution does not make the entire system deterministic or correct.

**Decision:** test a small typed query representation and validated filters. Do not reproduce the full memory framework or assume embeddings are unnecessary for all our questions.

### 9. TableRAG — EMNLP, November 2025

**Source:** [Yu et al., TableRAG: A Retrieval Augmented Generation Framework for Heterogeneous Document Reasoning](https://aclanthology.org/2025.emnlp-main.710/).

**Previous problem and improvement:** flattening and chunking tables disrupts structure. This TableRAG combines text retrieval with SQL operations and iterative decomposition for text-and-table reasoning. The exact title distinguishes it from other similarly named projects.

**Pros:** preserves relationships between columns and supports precise filtering and manipulation; directly relevant to rate and balance tiers.

**Cons for us:** an iterative text-to-SQL loop adds latency and error surfaces. Many assignment questions need a straightforward row lookup rather than multi-hop reasoning.

**Decision:** parse markdown tables into typed rows while retaining headers, footnotes, nearby headings, and raw evidence. Prefer validated parameterized lookups over unrestricted generated SQL.

### 10. T-RAG — Findings of ACL, July 2026

**Source:** [RAG over Tables: Hierarchical Memory Index, Multi-Stage Retrieval, and Benchmarking](https://aclanthology.org/2026.findings-acl.1902/).

**Previous problem and improvement:** table corpora need both table selection and organization of related evidence. T-RAG proposes a hierarchical memory index, multiple retrieval stages, and graph-aware context organization, evaluated on MultiTableQA.

**Pros:** motivates retrieving the relevant table and then the relevant rows while preserving context; relevant to complete product lists.

**Cons for us:** multi-table graph construction may be unnecessary for a small single-organization corpus. Its reported gains are benchmark-specific, not a guarantee for our tables.

**Decision:** use the simpler page/table/row hierarchy first. Add cross-table relationships only when observed failures require them.

### 11. Sufficient Context — ICLR 2025

**Sources:** [researchers' publication page](https://research.google/pubs/sufficient-context-a-new-lens-on-retrieval-augmented-generation-systems/) and [conference paper](https://proceedings.iclr.cc/paper_files/paper/2025/file/33dffa2e3d2ab74a783d1a8c292f66d9-Paper-Conference.pdf).

**Previous problem and improvement:** a wrong RAG answer does not reveal whether retrieval failed or the generator mishandled adequate evidence. This work classifies context sufficiency and analyzes those cases separately.

**Pros:** gives us a practical diagnostic: missing evidence requires better retrieval; sufficient evidence with a wrong answer requires better selection or generation.

**Cons for us:** sufficiency judgments can themselves be wrong. A passage can appear answerable yet be obsolete or refer to the wrong tier.

**Decision:** require evidence to match the entity, requested metric, qualifiers, and temporal target before declaring it sufficient. Measure unsupported answers and unnecessary refusals separately.

### 12. GRACE — January 8, 2026 preprint

**Source:** [GRACE: Reinforcement Learning for Grounded Response and Abstention under Contextual Evidence](https://arxiv.org/html/2601.04525v1), especially section 3.2.

**Previous problem and improvement:** grounding and handling insufficient evidence were often optimized separately. GRACE trains evidence assessment and response behavior using staged rewards and structured outputs.

**Pros:** makes evidence availability and supporting sentences explicit training targets.

**Cons and critical mismatch:** despite “abstention” in its title, the described insufficient-evidence branch permits a best-effort answer from parametric knowledge with a disclaimer. That behavior conflicts with our assignment's snapshots-only answers. Training also adds substantial work beyond our immediate need.

**Decision:** borrow explicit evidence assessment only. Do not adopt the internal-knowledge fallback, and do not assume a paper's use of “abstention” means strict refusal.

### 13. GRAB-RAG study — August 23, 2026 preprint

**Source:** [Prompt-Based Abstention Fails Under Misleading Context: A Controlled Study of Small Frozen RAG Models](https://arxiv.org/html/2608.22228v1).

**Previous problem and improvement:** missing and misleading evidence are often treated alike. The study compares abstention policies under supportive, degraded, absent, and deliberately misleading contexts using three small frozen models and two QA benchmarks.

**Finding:** explicit abstention prompting still produced answers on 41.6% of misleading questions in its reported setting. Stronger verifier policies reduced that behavior but also rejected many answerable questions.

**Pros:** directly motivates tests for convincing stale evidence, not just empty retrieval.

**Cons:** synthetic misinformation and small-model results do not quantify our system's risk. More refusal is not automatically better.

**Decision:** use evidence checks beyond a prompt instruction and tune against both wrong-answer rate and answer coverage. Resolve demonstrably stale evidence before deciding to refuse.

### 14. MADAM-RAG / RAMDocs — April 17, 2025; revised August 12, 2025

**Source:** [Retrieval-Augmented Generation with Conflicting Evidence](https://arxiv.org/html/2504.13079v2). The reviewed source is the arXiv version.

**Previous problem and improvement:** conflict evaluations often isolate one kind of disagreement. RAMDocs combines ambiguity, misinformation, and noise; MADAM-RAG uses multiple debating agents and an aggregator to separate plausible answers and reject misleading evidence.

**Pros:** treats disambiguation and conflict resolution as explicit work. Useful motivation for keeping competitors and explanations in a conflict report.

**Cons for us:** multiple rounds and agents increase calls and likely latency; agreement does not independently establish source authority. Benchmark ambiguity is not identical to product tiers or historical updates.

**Decision:** use deterministic conflict grouping and an explicit authority policy first. Consider an optional offline adjudication step only for genuinely unresolved cases; avoid debate on every answer.

## Proposed application to this repository

The following are our engineering recommendations, not claims that one cited paper implements this exact combination.

| Component | Initial approach | Benefit | Cost or failure to test |
|---|---|---|---|
| Evidence storage | Immutable page versions; URL, snapshot ID, headings, exact text, and content hash | Reproducible citations and diffs | Duplicated boilerplate and stale pages need handling |
| Fact representation | Entity/product, metric, value/unit, term, balance/model-year tier, audience, observed date, optional effective interval, evidence reference | Makes qualifiers explicit | Extraction omissions and incorrect entity merges |
| Historical selection | Latest available snapshot on or before requested date; preserve explicit within-page effective dates separately | Prevents future-snapshot leakage | Ambiguous dates and dates before the first snapshot |
| Retrieval | Exact structured lookup plus lexical text retrieval; evaluate dense retrieval if paraphrase misses justify it | Precise facts with broader descriptive coverage | Structured-only blind spots; lexical paraphrase failures |
| Table retrieval | Page/table/row hierarchy with inherited headers and footnotes | Preserves units and tier identity | Irregular tables and detached footnotes |
| Conflict resolution | Compare facts only after matching entity, metric, qualifiers, and overlapping applicability | Avoids labeling different products as contradictions | Missing qualifiers can create false conflicts |
| Source authority | Documented, topic-sensitive rules; authoritative current schedules over illustrative examples or expired offers where evidence supports this | Auditable winners | No universal “newest URL wins” or source-type ranking fits every fact |
| Answer generation | Deterministic rendering for structured values; bounded generation for descriptive answers | Consistency and low latency | Templates can be inflexible; generated prose still needs checking |
| Abstention | Distinguish missing evidence, unresolved conflict, and missing user qualifier | Honest and actionable responses | Overly strict gates reduce useful coverage |
| Citations | Carry evidence through selection into the answer; validate values and qualifiers against it | Reduces unsupported references | Correct URL alone does not prove claim support |

### Temporal and conflict rules worth making explicit

- A snapshot date tells us when content was observed. It is not automatically the effective date of every claim on the page.
- For historical website-state questions, do not let a later snapshot answer an earlier date, even if that later page describes an earlier event.
- A full snapshot's missing page is missing evidence in that observation, not proof that a product ceased to exist. Retain history without silently carrying removed pages into current evidence.
- A changed value between snapshots is a historical update. It becomes an unresolved contradiction only when competing claims have the same scope and overlapping applicability. The assignment may also want resolved cross-snapshot changes in `conflicts()`; label their type clearly.
- A rate and APY, or two distinct balance tiers, are not competing values for the same fact.
- Duplicate copies of a stale claim should not gain authority by majority vote.
- Preserve rejected alternatives for `conflicts()` and audit records. The member-facing answer should not indiscriminately repeat stale numbers.
- Relative phrases such as “last year” need an explicit reference policy; do not silently substitute the execution machine's date.

## Small experiments to run before choosing more infrastructure

Use supplied evaluations for development, but keep a separate local validation set derived from source evidence. Do not put expected evaluation answers into the solution's retrieval index or runtime rules.

| Comparison | Question it answers | Measurements |
|---|---|---|
| Plain retrieval vs snapshot-filtered retrieval | Does temporal eligibility prevent wrong-version evidence? | Historical accuracy, future leakage, evidence recall |
| Flattened chunks vs rows with inherited context | Does preserving structure fix tier confusion? | Tier/metric accuracy, missing qualifiers, list completeness |
| Unlabeled history vs explicit status labels | Do labels help when multiple versions are present? | Current/historical answer accuracy, stale-value contamination |
| Recency-only vs topic-sensitive authority policy | Can the system resolve stale calculators and offers? | Winner accuracy, conflict precision/recall, unsupported resolutions |
| Prompt-only refusal vs evidence gate | Are we distinguishing missing and misleading evidence? | Unsupported-answer rate, correct-answer coverage, false refusals |
| Lexical vs lexical+dense retrieval | Do embeddings improve paraphrase coverage enough to justify cost? | Recall of correct evidence, per-category accuracy, p95 latency |
| Structured rendering vs generated wording | Where is generation actually useful? | Correctness, citation support, repeated/paraphrased consistency |

Also test source-order shuffling, duplicated stale pages, irrelevant numerical distractors, absent tables, equal-authority disagreement, and dates between snapshots. Use controlled variants to expose mechanisms, not simply improve one aggregate public score.

Record ingestion time, answer p95, API cost, and refusal coverage alongside accuracy. Public evaluation without the real conflict gold set cannot certify conflict quality. Our custom tests supplement the organizer's scorer; they do not replace it.

## Adoption priorities and deferred work

**Adopt first:** version retention; separate observed/effective dates; qualifier-preserving tables; source-linked facts; explicit historical eligibility; conflict records; evidence checks; deterministic numeric rendering.

**Evaluate next:** temporal reranking, dense retrieval for paraphrases, a compact query parser, and a lightweight verifier for descriptive claims.

**Defer:** full graph services, multi-agent debate per question, reinforcement learning/fine-tuning, unrestricted text-to-SQL, and broad web-search agents. Their extra capabilities are not yet justified by this corpus and latency target.

**Unresolved until local experiments:** extraction coverage, rules for ambiguous effective dates, authority ties, the best retrieval mix, how much generation is needed, and calibration of the refusal threshold.

## Reuse and maintenance

Read this file before proposing architecture changes. Update this same file when new research changes a decision: record the research date, primary source, version/status, reason for relevance, and whether our own experiment confirmed the benefit. Keep paper findings separate from local results. Do not turn this note into a general AI reading list.
