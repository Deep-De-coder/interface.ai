"""Small synthetic answering diagnostic, separate from organizer scores."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from evaluation_cases import fixtures, PARAPHRASES
from submission.solution import build


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    ap.add_argument("--mode", choices=["basic", "research"], default="basic")
    args = ap.parse_args()
    snapshots, cases = fixtures()
    system = build(args.mode)
    for snapshot in snapshots:
        system.ingest(snapshot)
    results = []
    for c in cases:
        if c["split"] != args.split:
            continue
        variants = [c["question"]]
        if args.split == "dev" and c["category"] == "current":
            variants.append(PARAPHRASES[c["family"]])
        for question in variants:
            ans = system.answer(question, c["as_of"])
            correct = (not ans.confident) if c["should_refuse"] else (
                ans.confident and all(v.lower() in ans.text.lower() for v in c["must_include"])
                and all(any(s.url == url and s.snapshot_id == c["expected_snapshot"] for s in ans.sources)
                        for url in c["expected_sources"]))
            results.append({"id": c["id"], "passed": bool(correct)})
    print(json.dumps({"split": args.split, "cases_with_paraphrases": len(results),
                      "passed": sum(r["passed"] for r in results),
                      "note": "Simple diagnostic, not semantic grading; refusal-only passes are not useful QA."}, indent=2))


if __name__ == "__main__":
    main()
