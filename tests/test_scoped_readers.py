import unittest
from types import SimpleNamespace as Obj
from submission.solution import build
from submission.query import interpret
from submission.temporal import select_view
from submission.readers import read_scoped, procedure_evidence


class ScopedReaderTests(unittest.TestCase):
    def read(self, text, question, title="Oak Branch", path="oak"):
        system = build("basic")
        page = Obj(url="https://example.test/" + path, title=title, markdown=text, fetched_at="2026-01-01")
        system.ingest(Obj(snapshot_id="s", taken_on="2026-01-01", pages=[page]))
        view = select_view(system.evidence)
        return read_scoped(system.evidence, system.indexes["s"], interpret(question), view, view.observed_on)

    def test_branch_scope_and_complete_week(self):
        raw = ("# Oak Branch\n\n**Lobby** Monday-Thursday: 9 a.m.-5 p.m.\n"
               "Friday: 9 a.m.-6 p.m.\nSaturday: closed\n\n"
               "**Drive-up** Monday-Friday: 8 a.m.-7 p.m.")
        self.assertFalse(self.read(raw, "What are the general lobby hours?").answer.confident)
        self.assertFalse(self.read(raw, "What are Pine branch lobby hours?").answer.confident)
        result = self.read(raw, "What are Oak branch lobby hours?")
        self.assertTrue(result.answer.confident, result.answer.text)
        self.assertIn("Friday: 9 a.m.-6 p.m.", result.answer.text)
        self.assertIn("Saturday: closed", result.answer.text)
        self.assertNotIn("Drive-up", result.answer.text)

    def test_explicit_general_scope(self):
        result = self.read("# Hours for all branches\n\n**Lobby** Monday-Friday: 9 a.m.-5 p.m.",
                           "What are the general lobby hours?", title="Branch hours")
        self.assertTrue(result.answer.confident)

    def test_eligibility_preserves_rule_operator_and_alternatives(self):
        raw = ("# Membership\n\n## Eligible if any of these apply\n\n"
               "You must meet at least one of these conditions.\n"
               "- Live in the service area.\n- Have a family member who is a member.\n"
               "- Work for a partner organization.\n\n## Contact\n\nCall for assistance.")
        answer = self.read(raw, "Who is eligible to become a member?", title="Membership").answer
        self.assertTrue(answer.confident, answer.text)
        for phrase in ("any of these", "at least one", "Live", "family member", "partner organization"):
            self.assertIn(phrase, answer.text)
        self.assertNotIn("Call for assistance", answer.text)
        self.assertEqual(len(answer.sources), 4)

    def test_eligibility_does_not_cross_product_scope(self):
        raw = "# Maple Savings\n\n## Eligibility\n\nOnly local residents can open this account."
        self.assertFalse(self.read(raw, "Describe eligibility for Cedar Savings.", title="Maple Savings").answer.confident)

    def test_procedure_negation_object_and_normalization(self):
        query = interpret("How can I update my contact information?")
        self.assertTrue(procedure_evidence(query, "Change your contact details through the profile settings."))
        self.assertFalse(procedure_evidence(query, "You cannot update your contact information online."))
        self.assertFalse(procedure_evidence(query, "Contact support immediately and update your passwords."))
        self.assertFalse(procedure_evidence(query, "> I update my contact information often."))

    def test_explicit_count_and_link(self):
        count = self.read("# About\n\nOur credit union operates 23 branches across the region.",
                          "How many branches do you have?", title="About")
        self.assertTrue(count.answer.confident, count.answer.text)
        self.assertIn("23 branches", count.answer.text)
        link = self.read("# Savings\n\n[Certificate rates](https://example.test/rates)",
                         "What link should I use to see CD certificate rates?", title="Savings")
        self.assertTrue(link.answer.confident, link.answer.text)
        self.assertIn("https://example.test/rates", link.answer.text)
        locator = self.read("# Contact\n\nFind a [branch or ATM](https://example.test/contact#locator) nearby.",
                            "What is the URL for the branch and ATM locator?", title="Contact")
        self.assertTrue(locator.answer.confident, locator.answer.text)


if __name__ == "__main__":
    unittest.main()
