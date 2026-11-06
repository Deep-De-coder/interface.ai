"""Paired, uncached basic/research comparison; detailed source data stays ignored."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from evaluation_cases import fixtures, PARAPHRASES
from submission.solution import build


def percentile(values, p):
    return sorted(values)[max(0, math.ceil(len(values) * p) - 1)] if values else 0


def check_sources(answer, source_texts):
    checks = []
    for src in answer.sources:
        raw = source_texts.get((src.snapshot_id, src.url))
        checks.append(raw is not None and bool(src.quote) and all(
            part in raw for part in src.quote.split("\n[…]\n")))
    return all(checks) and (bool(checks) or not answer.confident)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=["synthetic-dev", "synthetic-holdout", "public", "local"], default="synthetic-dev")
    ap.add_argument("--kit", type=Path, default=ROOT / "hackathon-knowledge-kit-participant")
    ap.add_argument("--questions", type=Path, help="Local corpus gold JSONL, required for --suite local")
    ap.add_argument("--order", choices=["basic-first", "research-first"], default="basic-first")
    args = ap.parse_args()
    score_item = None
    if args.suite.startswith("synthetic"):
        snapshots, cases = fixtures()
        split = "dev" if args.suite.endswith("dev") else "holdout"
        cases = [c for c in cases if c["split"] == split]
        if split == "dev":
            cases += [{**c, "id": c["id"] + "-paraphrase", "question": PARAPHRASES[c["family"]]}
                      for c in cases if c["category"] == "current"]
    else:
        harness = args.kit.resolve() / "harness/run_eval.py"
        spec = importlib.util.spec_from_file_location("organizer_runner", harness)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        snapshots = module.load_snapshots(args.kit.resolve() / "snapshots")
        if args.suite == "public":
            path = args.kit / "eval/public_eval.jsonl"
            score_item = module.score_item
        else:
            if not args.questions:
                ap.error("--suite local requires --questions")
            path = args.questions
        cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    source_texts = {(s.snapshot_id, p.url): p.markdown for s in snapshots for p in s.pages}
    data_hash = sha256(json.dumps([(s.snapshot_id, s.taken_on, [(p.url, sha256(p.markdown.encode()).hexdigest()) for p in s.pages]) for s in snapshots]).encode()).hexdigest()
    code_hash = sha256(b"".join(p.read_bytes() for p in sorted((ROOT / "submission").glob("*.py")))).hexdigest()
    summaries, details = {}, {}
    modes = ("basic", "research") if args.order == "basic-first" else ("research", "basic")
    for mode in modes:
        system = build(mode)
        started = time.perf_counter()
        for snap in snapshots:
            system.ingest(snap)
        ingest_s = time.perf_counter() - started
        rows = []
        for case in cases:
            started = time.perf_counter()
            answer, trace = system.explain(case["question"], case.get("as_of"))
            elapsed = time.perf_counter() - started
            if score_item:
                score = score_item(case, answer)
                correct = None  # organizer fractional credit is not exact-match correctness
            else:
                score = None
                correct = not answer.confident if case.get("should_refuse") else (
                    answer.confident and all(v.lower() in answer.text.lower() for v in case.get("must_include", []))
                    and not any(v.lower() in answer.text.lower() for v in case.get("must_not_include", []))
                    and bool(answer.sources)
                    and (not case.get("expected_snapshot") or all(s.snapshot_id == case["expected_snapshot"] for s in answer.sources))
                    and all(any(v.lower() in (s.quote or "").lower() for s in answer.sources) for v in case.get("must_include", []))
                    and (args.suite == "local" or all(any(s.url == u for s in answer.sources) for u in case.get("expected_sources", []))))
            trace_evidence = [d for decision in trace.get("decisions", []) for d in decision["retrieved"]]
            source_hit = bool(case.get("expected_sources")) and any(d["url"] in case["expected_sources"] for d in trace_evidence)
            allowed = {v["snapshot_id"] for v in trace.get("views", []) if v["snapshot_id"]}
            eligible = all(s.snapshot_id in allowed for s in answer.sources)
            should_refuse = bool(case.get("should_refuse") or case.get("category") == "should_refuse")
            rows.append({"id": case["id"], "category": case.get("category"), "answer": asdict(answer),
                         "trace": trace, "seconds": elapsed, "passed": correct, "organizer_score": score,
                         "expected_source_retrieved": source_hit, "has_expected_sources": bool(case.get("expected_sources")),
                         "source_integrity": check_sources(answer, source_texts), "eligible_sources": eligible,
                         "should_refuse": should_refuse})
        latencies = [r["seconds"] for r in rows]
        answered = [r for r in rows if r["answer"]["confident"]]
        answerable = [r for r in rows if not r["should_refuse"]]
        source_cases = [r for r in rows if r["has_expected_sources"]]
        summaries[mode] = {"cases": len(rows), "ingest_seconds": round(ingest_s, 4),
                           "p95_seconds": round(percentile(latencies, .95), 6),
                           "max_seconds": round(max(latencies, default=0), 6),
                           "answered": len(answered), "coverage": len(answered) / max(1, len(rows)),
                           "false_refusals": sum(not r["answer"]["confident"] for r in answerable),
                           "source_integrity_failures": sum(not r["source_integrity"] for r in rows),
                           "ineligible_source_failures": sum(not r["eligible_sources"] for r in rows),
                           "expected_url_recall": sum(r["expected_source_retrieved"] for r in source_cases) / max(1, len(source_cases)),
                           "passed": None if score_item else sum(r["passed"] for r in rows),
                           "answered_exact_match_accuracy": None if score_item else sum(r["passed"] for r in answered) / max(1, len(answered)),
                           "by_category": {cat: {"count": sum(r["category"] == cat for r in rows),
                                                "answered": sum(r["category"] == cat for r in answered)}
                                           for cat in sorted({r["category"] for r in rows})}}
        if score_item:
            report = module.summarize([dict(r["organizer_score"], latency_s=r["seconds"], error=None, answer=r["answer"]) for r in rows], None, [])
            summaries[mode]["organizer_qa_score"] = report["qa_score"]
        details[mode] = rows
        del system
    paired = [{"id": a["id"], "same_answer": a["answer"] == b["answer"],
               "basic_passed": a["passed"], "research_passed": b["passed"]}
              for a, b in zip(details["basic"], details["research"])]
    report = {"suite": args.suite, "python": platform.python_version(), "platform": platform.platform(),
              "order": args.order, "code_sha256": code_hash, "corpus_sha256": data_hash,
              "questions_sha256": sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
              "variants": summaries, "different_answers": sum(not p["same_answer"] for p in paired),
              "limitations": "No answer cache. Exact-match and URL recall are diagnostics, not semantic entailment. Local gold accepts supporting alternate URLs; synthetic identity checks remain strict. No calibration or significance claim."}
    out = ROOT / "results/comparison" / args.suite / args.order
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out / "details.json").write_text(json.dumps({"paired": paired, "runs": details}, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
