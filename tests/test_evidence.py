import unittest
from types import SimpleNamespace as Obj
from submission.solution import build
from submission.parsing import parse


def page(text, url="https://example.test/rates"):
    return Obj(url=url, title="Rates", markdown=text, fetched_at="2026-01-01T00:00:00Z")


def snap(sid="one", taken="2026-01-01", pages=None):
    return Obj(snapshot_id=sid, taken_on=taken, pages=pages or [])


class EvidenceTests(unittest.TestCase):
    def test_preserves_history_and_deduplicates_content(self):
        s = build().evidence
        s.ingest(snap(pages=[page("old")]))
        s.ingest(snap("two", "2026-02-01", [page("new"), page("old", "https://example.test/archive")]))
        self.assertEqual(s.stats()["unique_contents"], 2)
        self.assertEqual(s.stats()["occurrences"], 3)
        self.assertEqual(s.raw(s.occurrences("one")[0]), "old")

    def test_idempotence_and_immutable_snapshot(self):
        s = build().evidence
        a, b = page("a"), page("b", "https://example.test/b")
        s.ingest(snap(pages=[a, b]))
        original = s.stats()
        s.ingest(snap(pages=[b, a]))
        self.assertEqual(original, s.stats())
        with self.assertRaises(ValueError):
            s.ingest(snap(pages=[page("changed")]))
        self.assertEqual(original, s.stats())

    def test_failed_ingest_is_atomic(self):
        s = build().evidence
        with self.assertRaises(ValueError):
            s.ingest(snap(pages=[page("good"), page("bad", "relative")]))
        self.assertEqual(s.stats()["snapshots"], 0)
        self.assertEqual(s.stats()["unique_contents"], 0)

    def test_duplicate_urls_and_out_of_order_rejected(self):
        s = build().evidence
        with self.assertRaises(ValueError):
            s.ingest(snap(pages=[page("a"), page("b")]))
        s.ingest(snap("new", "2026-03-01"))
        with self.assertRaises(ValueError):
            s.ingest(snap("old", "2026-01-01"))

    def test_disappearance_does_not_delete_history(self):
        s = build().evidence
        s.ingest(snap(pages=[page("old")]))
        s.ingest(snap("two", "2026-02-01"))
        self.assertEqual(len(s.occurrences("two")), 0)
        self.assertEqual(len(s.occurrences("one")), 1)

    def test_table_headers_qualifiers_and_footnotes_preserved(self):
        raw = "# Savings\n\nMembers only\n\n| Tier | APY1 |\n| --- | --- |\n| $100+ | 2.25%1 |\n\n1 Fees reduce earnings.\n"
        row = next(b for b in parse(raw) if b.kind == "table_row")
        self.assertEqual(row.cells, ("$100+", "2.25%1"))
        self.assertEqual(row.headings, ("Savings",))
        self.assertEqual(raw[row.header.start:row.header.end], "| Tier | APY1 |")
        context = [raw[s.start:s.end] for s in row.context]
        self.assertIn("Members only", context)
        self.assertIn("1 Fees reduce earnings.", context)

    def test_malformed_rows_remain_auditable(self):
        raw = "| A | B |\n| --- | --- |\n| one |\n"
        row = next(b for b in parse(raw) if b.kind == "table_row")
        self.assertIn("row_width_mismatch", row.warnings)
        self.assertEqual(raw[row.span.start:row.span.end], "| one |")

    def test_escaped_newlines_and_pipes_keep_raw_offsets(self):
        raw = r"# Rates\n| Product | Rate |\n| --- | --- |\n| A\|B | 3.1% |"
        row = next(b for b in parse(raw) if b.kind == "table_row")
        self.assertEqual(len(row.cells), 2)
        self.assertIn("escaped_newlines_interpreted", row.warnings)
        self.assertEqual(raw[row.span.start:row.span.end], r"| A\|B | 3.1% |")

    def test_crlf_unicode_and_empty_input(self):
        self.assertEqual(parse(""), ())
        raw = "# Café\r\n\r\n- €25 minimum\r\n"
        b = parse(raw)[1]
        self.assertEqual(raw[b.span.start:b.span.end], "- €25 minimum")

    def test_mutating_rate_changes_evidence_without_changing_parser(self):
        raw = "| Tier | APY |\n| --- | --- |\n| $200+ | 1.25% |"
        a = next(b for b in parse(raw) if b.kind == "table_row")
        b = next(b for b in parse(raw.replace("1.25%", "7.50%")) if b.kind == "table_row")
        self.assertEqual(a.cells[0], b.cells[0])
        self.assertEqual(b.cells[1], "7.50%")


if __name__ == "__main__":
    unittest.main()
