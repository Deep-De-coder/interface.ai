"""Run unchanged organizer evaluation or audit local evidence without exporting it."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from submission.solution import build


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["baseline", "submission", "audit"])
    ap.add_argument("--kit", type=Path, default=ROOT / "hackathon-knowledge-kit-participant")
    args = ap.parse_args()
    kit = args.kit.resolve()
    harness = kit / "harness" / "run_eval.py"
    if not harness.exists():
        ap.error("Supply the separately obtained participant kit with --kit")
    if args.mode != "audit":
        folder = kit / "starter" if args.mode == "baseline" else ROOT / "submission"
        subprocess.run([sys.executable, str(harness), "--submission", str(folder),
                        "--snapshots", str(kit / "snapshots"), "--eval", str(kit / "eval/public_eval.jsonl"),
                        "--out", str(ROOT / "results" / args.mode)], check=True)
        return
    spec = importlib.util.spec_from_file_location("organizer_runner", harness)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshots = module.load_snapshots(kit / "snapshots")
    system = build()
    start = time.perf_counter()
    for snapshot in snapshots:
        system.ingest(snapshot)
    elapsed = time.perf_counter() - start
    kinds, warnings = Counter(), Counter()
    checked = 0
    for snapshot in snapshots:
        for occurrence in system.evidence.occurrences(snapshot.snapshot_id):
            raw = system.evidence.raw(occurrence)
            for block in system.evidence.blocks(occurrence):
                kinds[block.kind] += 1
                warnings.update(block.warnings)
                spans = [block.span, *block.context] + ([block.header] if block.header else [])
                for span in spans:
                    assert system.evidence.quote(occurrence, span) == raw[span.start:span.end]
                    assert span.end > span.start
                    checked += 1
    result = {**system.evidence.stats(), "ingest_seconds": round(elapsed, 3),
              "occurrence_block_counts": dict(kinds), "warning_counts": dict(warnings),
              "validated_spans": checked, "python": sys.version.split()[0],
              "note": "Span integrity only; semantic associations are not validated by this audit."}
    out = ROOT / "results/audit.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
