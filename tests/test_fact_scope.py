import unittest
from dataclasses import replace
from types import SimpleNamespace as Obj

from submission.solution import build
from submission.facts import fact_scope
from submission.conflicts import resolve_entries
from submission.temporal import Applicability


def system(*texts):
    s = build("basic")
    pages = [Obj(url=f"https://example.test/page-{i}", title="Products", markdown=text,
                 fetched_at="2026-01-01") for i, text in enumerate(texts)]
    s.ingest(Obj(snapshot_id="one", taken_on="2026-01-01", pages=pages))
    return s


def table(name, rate):
    return f"## {name}\n\n| Balance | APY |\n| --- | --- |\n| $100+ | {rate} |\n"


class FactScopeTests(unittest.TestCase):
    def test_prose_preserves_range_and_conditions(self):
        s = system("# Maple Card\n\nMaple Card APR: 12.00%-18.00% depending on creditworthiness.")
        a = s.answer("What is the Maple Card APR?")
        self.assertTrue(a.confident, a.text)
        for value in ("12.00%", "18.00%", "creditworthiness"):
            self.assertIn(value, a.text)
        s = system("# Maple Savings\n\nMaple Savings APY: 2.00% for balances under $500, otherwise 1.00%.")
        a = s.answer("What is the Maple Savings APY?")
        self.assertTrue(a.confident, a.text)
        for value in ("2.00%", "1.00%", "$500", "under"):
            self.assertIn(value, a.text)

    def test_same_page_distinct_subjects_do_not_conflict(self):
        s = system("# Savings Rates\n\n" + table("Maple Savings", "2%") + "\n" + table("Cedar Savings", "4%"))
        self.assertEqual(s.conflicts(), [])
        docs = [d for d in s.indexes["one"].docs if d.headers]
        self.assertNotEqual(fact_scope(docs[0], "apy"), fact_scope(docs[1], "apy"))

    def test_named_subject_can_conflict_across_urls(self):
        s = system(table("Maple Savings", "2%"), table("Maple Savings", "4%"))
        conflicts = s.conflicts()
        self.assertEqual(len(conflicts), 1)
        self.assertIsNone(conflicts[0].resolution)

    def test_audience_is_part_of_named_row_identity(self):
        row = "\n\n| Card Type | APR |\n| --- | --- |\n| Platinum Visa | 12% |"
        s = system("# Business Credit Cards" + row, "# Personal Credit Cards" + row)
        docs = [d for d in s.indexes["one"].docs if d.headers]
        self.assertNotEqual(fact_scope(docs[0], "apr"), fact_scope(docs[1], "apr"))

    def test_resolution_uses_target_and_canonical_values(self):
        s = system(table("Maple Savings", "2%"))
        doc = next(d for d in s.indexes["one"].docs if d.headers)
        scheduled = replace(doc, validity=Applicability(start="2026-02-01"))
        self.assertIsNone(resolve_entries([("2%1", scheduled)], target="2026-01-01")[0])
        self.assertEqual(resolve_entries([("2%1", scheduled)], target="2026-02-01")[0], "2%")
        self.assertEqual(resolve_entries([("2%1", doc), ("2%", doc)])[0], "2%")


if __name__ == "__main__":
    unittest.main()
