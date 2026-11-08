# Evidence-grounded snapshot knowledge system

A deterministic question-answering system that answers questions about a credit-union
website **as of now**, using only dated full-site snapshots — with exact citations,
conflict resolution, and honest refusals. **Python standard library only: no LLM, no
API, no embeddings, no database, no network.** Same input → same output.

## Submit / run

The hand-in is the [`submission/`](submission/) folder. It exposes the organizer
contract (`harness/contract.py`):

```python
from submission.solution import build
ks = build()                       # defaults to the 'basic' arm
for snap in snapshots:             # oldest -> newest
    ks.ingest(snap)
ks.answer(question, as_of=None)     # -> Answer(text, sources, confident, conflict_note)
ks.conflicts()                     # -> list[Conflict]
```

Score it with the participant kit's harness (kept local, not in this repo):

```bash
python harness/run_eval.py --submission submission --eval eval/public_eval.jsonl
```

Tests and release checks (no kit required):

```bash
python -m unittest discover -s tests -v
python scripts/verify_release.py          # builds a source-only zip, imports it in isolation
python scripts/package_submission.py      # writes dist/submission.zip (allowlisted source only)
```

Python 3.11+. No API keys, downloads, or services. `build("research")` selects the
alternate retriever; `KNOWLEDGE_MODE=research` does the same for the organizer's
zero-argument `build()`.

## Approach

1. **Immutable evidence** — each snapshot page is stored with URL, title, date, fetch
   time and SHA-256; identical text is deduplicated. Parsing keeps headings, prose,
   list items and table cells with exact character offsets; malformed tables keep
   warnings rather than becoming silent facts.
2. **Truth-at-a-time** — "now" is the latest snapshot's date; `as_of` selects the
   snapshot on or before that date. Historical answers don't change when newer
   snapshots are added.
3. **Interpret → retrieve → read → resolve → validate** — the question's intent, time
   and scope drive a lexical (default) or BM25 retriever; bounded readers answer
   table values, extrema, bounded lists, hours, eligibility, counts, links and
   procedures; a full-scan fallback surfaces the answer when it ranks below the
   lexical top-k; conflicts resolve to the value applicable at the target date.
4. **Honesty gate** — a confident answer must cite real sources, every cited quote
   must appear verbatim in its source, and every number in the answer must be backed
   by a cited quote; otherwise the system abstains.

## Layout

| Path | Contents |
|---|---|
| `submission/` | the hand-in: `solution.py` (`build()`), readers, evidence store, parsing, validation, `NOTES.md`, `requirements.txt` |
| `tests/` | unit/regression tests over invented fixtures (no supplied data) |
| `scripts/` | evaluation, variant comparison, packaging and release verification |

The participant kit, website snapshots, API keys and detailed run artifacts are
**not** redistributed here (see `.gitignore`); obtain the authorized kit separately
to reproduce the public evaluation.
