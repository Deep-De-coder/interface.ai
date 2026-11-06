import unittest
from submission.solution import build
from submission.models import Answer, Source
from submission.validation import validate
from test_answering import page, snapshot, content


class ConflictValidationTests(unittest.TestCase):
    def test_card_list_spans_multiple_source_pages(self):
        s = build()
        a = "# Credit Cards\n\n| Card Type | APR |\n| --- | --- |\n| Cedar Card | 11.25% |"
        b = "# Business Credit Cards\n\n| Card Type | APR |\n| --- | --- |\n| Business Oak Card | 14.75% |"
        s.ingest(snapshot("one", "2026-01-01", [page(a, "cards", "Credit Cards"), page(b, "business", "Business Credit Cards")]))
        answer = s.answer("What credit cards do you offer and what are their APRs?")
        self.assertTrue(answer.confident, answer.text)
        self.assertIn("Cedar Card", answer.text)
        self.assertIn("Business Oak Card", answer.text)
        self.assertEqual(len(answer.sources), 2)

    def test_history_and_sources(self):
        s = build()
        s.ingest(snapshot("old", "2026-01-01", [page(content())]))
        s.ingest(snapshot("new", "2026-03-01", [page(content("8.75%"))]))
        conflicts = s.conflicts()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].resolution, "8.75%")
        self.assertEqual({x.snapshot_id for x in conflicts[0].sources}, {"old", "new"})
        self.assertEqual(s.conflicts(), conflicts)

    def test_unrelated_products_not_merged(self):
        s = build()
        s.ingest(snapshot("one", "2026-01-01", [page(content()), page(content("9.25%"), "another", "Other Savings")]))
        self.assertEqual(s.conflicts(), [])

    def test_numeric_fabrication_and_false_quote_rejected(self):
        s = build()
        s.ingest(snapshot("one", "2026-01-01", [page(content())]))
        src = Source("https://example.test/rates", "one", "| $100 – $999.99 | 2.10% |")
        self.assertIsNone(validate(Answer("APY: 2.10%", [src], True), s.evidence, {"one"}))
        self.assertIsNotNone(validate(Answer("APY: 9.99%", [src], True), s.evidence, {"one"}))
        src.quote = "invented text"
        self.assertIsNotNone(validate(Answer("Unsupported", [src], True), s.evidence, {"one"}))
