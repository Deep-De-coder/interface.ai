import unittest
from evaluation_cases import fixtures, PARAPHRASES
from submission.solution import build


class FixtureTests(unittest.TestCase):
    def test_split_and_source_gold(self):
        snapshots, cases = fixtures()
        self.assertEqual(sum(c["split"] == "dev" for c in cases), 24)
        self.assertEqual(sum(c["split"] == "holdout" for c in cases), 12)
        dev = {c["family"] for c in cases if c["split"] == "dev"}
        holdout = {c["family"] for c in cases if c["split"] == "holdout"}
        self.assertFalse(dev & holdout)
        self.assertEqual(set(PARAPHRASES), dev)
        pages = {(s.snapshot_id, p.url): p.markdown for s in snapshots for p in s.pages}
        for c in cases:
            if c["should_refuse"]:
                continue
            raw = pages[c["expected_snapshot"], c["expected_sources"][0]]
            for expected in c["must_include"]:
                self.assertIn(expected, raw)

    def test_synthetic_ingestion(self):
        snapshots, _ = fixtures()
        system = build()
        for snapshot in snapshots:
            system.ingest(snapshot)
        self.assertEqual(system.evidence.stats()["occurrences"], 18)
