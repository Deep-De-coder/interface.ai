import unittest
from types import SimpleNamespace as Obj
from submission.solution import build
from submission.temporal import interpret, select_view
from submission.parsing import cells


def page(text, path="rates", title="Maple Savings"):
    return Obj(url="https://example.test/" + path, title=title, markdown=text, fetched_at="2026-01-01")


def snapshot(sid, taken, pages):
    return Obj(snapshot_id=sid, taken_on=taken, pages=pages)


def content(rate="2.10%", extra=""):
    return ("# Maple Savings\n\n| Balance | APY |\n| --- | --- |\n"
            f"| $100 – $999.99 | {rate} |\n| $1000+ | 3.40% |\n\n{extra}\n"
            "## Access\n\n- Online banking\n- Branch withdrawals\n\n"
            "## Eligibility\n\nMaple Savings is available to individual members living in the service area.\n")


class AnswerTests(unittest.TestCase):
    def systems(self, first=None, second=None):
        for mode in ("basic", "research"):
            system = build(mode)
            system.ingest(snapshot("old", "2026-01-01", first or [page(content())]))
            if second is not None:
                system.ingest(snapshot("new", "2026-03-01", second))
            yield system

    def test_current_historical_tier_and_exact_citation(self):
        for s in self.systems(second=[page(content("2.90%"))]):
            current = s.answer("What APY applies to Maple Savings at $200?")
            self.assertTrue(current.confident, current.text)
            self.assertIn("2.90%", current.text)
            self.assertNotIn("3.40%", current.text)
            historical = s.answer("What APY applies to Maple Savings at $200?", "2026-02-01")
            self.assertTrue(historical.confident)
            self.assertIn("2.10%", historical.text)
            self.assertEqual(historical.sources[0].snapshot_id, "old")
            raw = content()
            for excerpt in historical.sources[0].quote.split("\n[…]\n"):
                self.assertIn(excerpt, raw)

    def test_future_mutation_cannot_change_historical_result(self):
        for s in self.systems():
            q = "What APY applies to Maple Savings at $200?"
            before = s.answer(q, "2026-01-01")
            s.ingest(snapshot("future", "2026-04-01", [page(content("9.99%"))]))
            self.assertEqual(before, s.answer(q, "2026-01-01"))

    def test_list_descriptive_and_missing(self):
        for s in self.systems():
            answer = s.answer("List the access methods for Maple Savings.")
            self.assertTrue(answer.confident, answer.text)
            self.assertIn("Online banking", answer.text)
            self.assertIn("Branch withdrawals", answer.text)
            answer = s.answer("Describe eligibility for Maple Savings.")
            self.assertTrue(answer.confident, answer.text)
            self.assertIn("individual members", answer.text)
            self.assertFalse(s.answer("What is the wire transfer fee for Maple Savings?").confident)

    def test_change_requires_matching_endpoints(self):
        for s in self.systems(second=[page(content("2.90%"))]):
            answer = s.answer("Compare the APY for Maple Savings at $200 between 2026-01-01 and 2026-03-01.")
            self.assertTrue(answer.confident, answer.text)
            self.assertIn("2.10%", answer.text)
            self.assertIn("2.90%", answer.text)
            self.assertEqual({src.snapshot_id for src in answer.sources}, {"old", "new"})

    def test_conflicting_values_do_not_get_a_score_based_winner(self):
        for s in self.systems(first=[page(content()), page(content("6.20%"), "other")]):
            answer, trace = s.explain("What APY applies to Maple Savings at $200?")
            self.assertFalse(answer.confident)
            self.assertEqual(trace["status"], "conflicting")
            self.assertEqual(len(answer.sources), 2)

    def test_explicit_dates_and_malformed_rows_fail_closed(self):
        variants = [content(extra="Effective 2026-02-01."),
                    content(extra="Expires 2025-12-31."),
                    content(extra="Effective 2025-01-01. Effective 2025-02-01."),
                    content().replace("$100 – $999.99 | 2.10%", "$100 – $999.99 | extra | 2.10%")]
        for raw in variants:
            for s in self.systems(first=[page(raw)]):
                self.assertFalse(s.answer("What APY applies to Maple Savings at $200?").confident, raw)

    def test_disappeared_page_not_carried_forward(self):
        for s in self.systems(second=[]):
            self.assertFalse(s.answer("What APY applies to Maple Savings at $200?").confident)

    def test_missing_becomes_answerable(self):
        raw = "# Maple Savings\n\n| Service | Fee |\n| --- | --- |\n| Wire transfer | $12 |"
        for s in self.systems():
            q = "What is the wire transfer fee for Maple Savings?"
            self.assertFalse(s.answer(q).confident)
            s.ingest(snapshot("new", "2026-03-01", [page(raw)]))
            self.assertTrue(s.answer(q).confident, s.answer(q).text)
            self.assertIn("$12", s.answer(q).text)

    def test_date_boundaries_and_ambiguity(self):
        for s in self.systems():
            self.assertIsNotNone(select_view(s.evidence, "2025-12-31").error)
            self.assertIn("Last observed", select_view(s.evidence, "2027-01-01").note)
            s.ingest(snapshot("duplicate_date", "2026-01-01", [page(content())]))
            self.assertIsNotNone(select_view(s.evidence).error)
        self.assertIsNone(interpret("APR on a 2025 model-year vehicle?").cutoff)
        self.assertEqual(interpret("What event is scheduled on 2026-05-01?", "2026-01-01").event_date, "2026-05-01")
        self.assertIsNotNone(interpret("Rates as of 2026-02-01", "2026-01-01").error)
        self.assertIsNotNone(interpret("Rates", "not-a-date").error)
        self.assertIsNotNone(interpret("What was the APY in 2025?").error)
        self.assertIsNone(interpret("What was the APY at $2000?", "2026-01-15").error)
        self.assertIsNone(interpret("What was the APY at $2000?").error)

    def test_empty_table_cells_are_preserved(self):
        self.assertEqual(cells("| | APY | |"), ("", "APY", ""))

    def test_scheduled_offer_is_not_current_and_is_labeled_when_requested(self):
        for s in self.systems(first=[page(content(extra="Effective 2026-02-01."))]):
            self.assertFalse(s.answer("What APY applies to Maple Savings at $200?").confident)
            a = s.answer("What APY is scheduled for Maple Savings at $200 on 2026-02-01?")
            self.assertTrue(a.confident, a.text)
            self.assertIn("implementation is unconfirmed", a.text)

    def test_fee_service_and_description_must_match(self):
        raw = "# Maple Savings\n\n| Service | Fee |\n| --- | --- |\n| Overdraft | $12 |\n\nMaple Savings sponsors an annual art competition for local artists."
        for s in self.systems(first=[page(raw)]):
            self.assertFalse(s.answer("What is the wire transfer fee for Maple Savings?").confident)
            self.assertFalse(s.answer("Describe eligibility for Maple Savings.").confident)

    def test_ambiguous_rate_and_procedure_are_not_related_passage_answers(self):
        raw = "# Maple Savings\n\n| Balance | Dividend Rate | APY |\n| --- | --- | --- |\n| $100+ | 2.10% | 2.12% |\n\nMaple Savings lets members manage balances online and in branches."
        for s in self.systems(first=[page(raw)]):
            answer = s.answer("What is the rate for Maple Savings at $200?")
            self.assertTrue(answer.confident)
            self.assertIn("2.10%", answer.text)
            self.assertIn("2.12%", answer.text)
            self.assertFalse(s.answer("How can I open Maple Savings online?").confident)


if __name__ == "__main__":
    unittest.main()
