# Evidence-grounded snapshot knowledge system

Implementation includes a conservative end-to-end answering
path with date selection, table values, bounded lists, citations, and refusals.
Two retrieval modes are available: `basic` (default) and `research`. Conflict
enumeration, exact-quote/numeric validation, and source-only packaging are now
implemented. Query coverage remains limited; see the current evaluation before
treating this as submission-ready.

Python 3.11+; standard library only. No API keys, downloads, or database services.
The participant kit must be supplied separately and is excluded from Git.

```powershell
python -m unittest discover -s tests -v
python scripts/evaluate.py baseline
python scripts/evaluate.py audit
python scripts/evaluate.py submission
python scripts/evaluate_synthetic.py
python scripts/compare_variants.py --suite synthetic-dev
python scripts/compare_variants.py --suite public
python scripts/verify_release.py
```

Use `--kit PATH` for a participant kit outside the default local directory.
Organizer reports and detailed paired traces are written under ignored `results/`.
Use `build("basic")` or `build("research")` from Python. The organizer's zero-argument
`build()` defaults to basic; set `KNOWLEDGE_MODE=research` to select the other arm.
For a direct synthetic run, use `--mode research`. Neither arm needs a model/API.

The two retained drafts are [snapshot-first](STEP_5_6_PLAN.md) and
[research comparison](STEP_5_6_RESEARCH_DRAFT.md). See
[STEP_5_6_COMPARISON.md](STEP_5_6_COMPARISON.md) for results and limitations.

Submit the `submission/` folder to the organizer harness. See
[submission/NOTES.md](submission/NOTES.md) for implementation boundaries and
[EVALUATION.md](EVALUATION.md) for measured results and limitations.
