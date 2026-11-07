import unittest
from types import SimpleNamespace as Obj
from submission.solution import build


def make(mode, texts):
    s = build(mode)
    s.ingest(Obj(snapshot_id="one", taken_on="2026-01-01", pages=[
        Obj(url=f"https://example.test/{i}", title="Products", markdown=t,
            fetched_at="2026-01-01") for i, t in enumerate(texts)]))
    return s


def table(value, reverse=False):
    rows = ["| $100 | 2.00% |", f"| $200 | {value} |"]
    return "# Maple Savings\n\n| Balance | APY |\n| --- | --- |\n" + "\n".join(rows[::-1] if reverse else rows)


class NumericOperationsTests(unittest.TestCase):
    def test_every_output_row_resolved_independent_of_order(self):
        for mode in ("basic", "research"):
            for reverse in (False, True):
                s = make(mode, [table("3.00%", reverse), table("7.00%", not reverse)])
                self.assertFalse(s.answer("What is the Maple Savings APY?").confident)
                self.assertFalse(s.answer("What is the Maple Savings APY at $200?").confident)
                self.assertTrue(s.answer("What is the Maple Savings APY at $100?").confident)

    def test_extremes_and_positive_witness(self):
        for mode in ("basic", "research"):
            s = make(mode, [table("3.00%")])
            for operator, wanted, absent in (("highest", "3.00%", "2.00%"), ("lowest", "2.00%", "3.00%")):
                a = s.answer(f"What is the {operator} Maple Savings APY?")
                self.assertTrue(a.confident, a.text)
                self.assertIn(wanted, a.text)
                self.assertNotIn(absent, a.text)
            self.assertTrue(s.answer("Do any Maple Savings tiers pay 3.00% APY?").confident)
            self.assertFalse(s.answer("Do any Maple Savings tiers pay 8.00% APY?").confident)

    def test_extreme_does_not_reduce_conditional_value(self):
        s = make("basic", ["# Maple Savings\n\nMaple Savings APY: 2.00% under $500, otherwise 1.00%."])
        self.assertFalse(s.answer("What is the highest Maple Savings APY?").confident)

    def test_prose_card_range_and_intro_are_distinct(self):
        raw = "# Credit Cards\n\n## Cedar Visa\n\n- Ongoing rate: 11.00%–17.00% APR depending on credit.\n- Intro APR: 1.00% on balance transfers for six months."
        for mode in ("basic", "research"):
            a = make(mode, [raw]).answer("What is the standard purchase APR on Cedar Visa?")
            self.assertTrue(a.confident, a.text)
            self.assertIn("11.00%", a.text)
            self.assertIn("17.00%", a.text)
            self.assertIn("depending on credit", a.text)
            self.assertNotIn("six months", a.text)

    def test_card_table_not_suppressed_by_transfer_footnote(self):
        raw = "# Business Credit Cards\n\n| Card Type | APR |\n| --- | --- |\n| Business Cedar Card | 14.00% |\n\nBalance transfer promotions have separate conditions."
        a = make("basic", [raw]).answer("What credit cards do you offer and what are their APRs?")
        self.assertTrue(a.confident, a.text)
        self.assertIn("14.00%", a.text)
