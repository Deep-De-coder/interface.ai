# Implementation notes — 2026-11-07

Round 02 adds shared fact scope, per-output-fact resolution, full prose
range/condition preservation, product-local APR evidence, scoped schedules and
eligibility groups, bounded scalar extrema/positive witnesses, and explicit
link/count readers. Reader indexes contain derived evidence, not cached answers.
Forty-six tests pass on Python 3.11 and 3.12. The 14 reviewed diagnostic checks
pass, but the public basic QA score decreased from .5561 to .5310: three card
questions improved while three general-hours questions now refuse unsupported
branch-to-general scope extrapolation. Complex procedures, relation questions,
audience ambiguity and complete inventory coverage remain unresolved. Earlier
notes below are retained as history; they are not final performance claims.

Update: conflict enumeration now retains comparable table changes across
snapshots and across explicitly named account/card/certificate rows. Unknown
entity equivalence is kept separate by URL. Answering and conflict reporting
share latest-observation/effective-date resolution. Final confident answers
must pass source-view, exact-quotation and numerical-support checks. These are
structural checks, not a semantic correctness guarantee.

Python 3.11.9 has now been tested locally. `scripts/verify_release.py` builds and
imports an isolated source-only archive, without the supplied dataset. Historical
notes below describe the earlier first-slice milestone and its limitations.

`build()` creates a fresh in-memory system. The harness can import `solution.py`
directly; no participant-kit files are required by standalone submission code.
If the harness has already loaded `contract`, its dataclasses are used at the
boundary for compatibility with its repeat-answer checker; otherwise local
structurally compatible dataclasses are used.
Dependencies: Python standard library only. API cost: zero.

Each immutable source occurrence retains its exact URL, title, snapshot/date,
fetch timestamp, and SHA-256 content identity. Identical text shares raw storage
and parsed blocks. Snapshot identity includes page metadata and is independent
of page order. Repeating an identical ingest is harmless; changing an existing
snapshot ID, duplicate URLs, invalid dates/URLs, and backward ingestion fail
without partially publishing the new snapshot. Empty snapshots are valid.

Parsing retains headings, source-line passages, list items, table headers/cells,
and candidate surrounding context. Every excerpt references original character
offsets. Escaped newlines are interpreted with an explicit warning; raw text is
never rewritten. Percent footnote suffixes remain intact. No numeric or temporal
assertions are inferred by the parser. Malformed tables remain accessible with
warnings, rather than becoming silently accepted structured facts.

Limitations: this is a conservative Markdown parser, not full CommonMark. Context
uses a bounded neighborhood and does not prove footnote applicability. Some
conditions outside that neighborhood require later expansion from the full raw
page. Nested/HTML/code-span tables and unmarked section boundaries need further
handling if they block real questions. Warnings must be respected downstream.
Storage is in-memory and rebuilt from ingestion; persistent SQLite is deferred
until a measured need exists.

`build("basic")` uses lexical overlap; `build("research")` uses decomposed queries,
BM25, hierarchy weights, and an applicability ranking signal. The organizer can
select research via `KNOWLEDGE_MODE=research`; the default remains basic.
Both index only ingested source content. Snapshot selection, date applicability,
qualifier checks, rendering, and citation logic are shared. Expensive indexes
are built during ingestion; answers are not cached. `explain()` returns audit
traces without mutating question state. There are no model or network calls.

The reader supports a narrow slice: validated table metrics, exact qualifiers,
explicit list sections, short extractive descriptions, and two-date numeric
comparisons. It rejects detected comparable contradictions and uncertain table
structures. `conflicts()` still returns an empty list: full enumeration is step 8.
Prose amounts, complex dates and scopes, and multi-page complete lists are known
coverage gaps. Citation integrity is checked independently of semantic support;
the latter is not guaranteed. Research mode is a lightweight adaptation, not a
reproduction of MRAG, TimelyRAG, or T-RAG.

Validated on Windows with Python 3.11.9 and Python 3.12. No performance guarantee
for the grader is claimed; the latest measured results are recorded separately.
