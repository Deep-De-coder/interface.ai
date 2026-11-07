"""Repeatable basic-mode review probes using invented evidence only.

Diagnostic findings intentionally do not set a failing process exit code.
Inspect each `passed` field; this is not a replacement for the test suite.
"""
from dataclasses import asdict
import json
from pathlib import Path
import sys
from types import SimpleNamespace as Obj

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from submission.solution import build


def page(path, text, title="Maple Products"):
    return Obj(url="https://example.test/" + path, title=title,
               markdown=text, fetched_at="2026-01-01")


def system(pages):
    result = build("basic")
    result.ingest(Obj(snapshot_id="invented-01", taken_on="2026-01-01", pages=pages))
    return result


def table(second):
    return ("# Maple Savings\n\n| Balance | APY |\n| --- | --- |\n"
            "| $100 | 2.00% |\n| $200 | " + second + " |")


def main():
    cases = []

    def check(identifier, instance, question, expected, predicate):
        answer, trace = instance.explain(question)
        cases.append({"id": identifier, "question": question, "expected": expected,
                      "passed": bool(predicate(answer)), "answer": asdict(answer),
                      "status": trace["status"]})

    conflicting = system([page("a", table("3.00%")), page("b", table("9.00%"))])
    check("multirow-conflict-broad", conflicting, "What is the Maple Savings APY?",
          "Refuse because a displayed tier has unresolved conflicting values.",
          lambda a: not a.confident)
    check("multirow-conflict-narrow-control", conflicting,
          "What is the Maple Savings APY at $200?", "Refuse the conflicting tier.",
          lambda a: not a.confident)

    ranged = system([page("card", "# Maple Card\n\n"
                         "Maple Card APR: 12.00%-18.00% depending on creditworthiness.")])
    check("prose-range-preservation", ranged, "What is the Maple Card APR?",
          "Preserve both range endpoints and condition, or refuse unsupported parsing.",
          lambda a: not a.confident or all(x in a.text for x in
                                          ("12.00%", "18.00%", "creditworthiness")))
    conditional = system([page("savings", "# Maple Savings\n\n"
                              "Maple Savings APY: 2.00% for balances under $500, otherwise 1.00%.")])
    check("prose-condition-preservation", conditional, "What is the Maple Savings APY?",
          "Preserve both conditional rates and boundary, or refuse unsupported parsing.",
          lambda a: not a.confident or all(x in a.text for x in
                                          ("2.00%", "1.00%", "$500", "under")))

    complete = system([page("rates", table("3.00%"))])
    check("maximum-operator", complete, "What is the highest Maple Savings APY?",
          "Answer the supported maximum, 3.00%, from a complete explicit table.",
          lambda a: a.confident and "3.00%" in a.text and "2.00%" not in a.text)
    check("exists-operator", complete, "Do any Maple Savings tiers pay 3.00% APY?",
          "Confirm an existing tier with the requested rate.",
          lambda a: a.confident and "3.00%" in a.text)

    branch = system([page("oak-opening", "# Oak Branch Opening\n\n"
                          "Our Oak branch opens this month.\n\n"
                          "**Lobby** Monday-Friday: 9 a.m.-5 p.m.", "Oak branch opening")])
    check("branch-scope-generalization", branch, "What are the general lobby hours?",
          "Give a representative schedule and offer to narrow by branch (the rubric wants a "
          "typical schedule, not a bare refusal).",
          lambda a: a.confident and "9 a.m." in a.text and "branch" in a.text.lower())
    check("branch-scope-named-control", branch, "What are the Oak branch lobby hours?",
          "Answer the named branch schedule with its published hours.",
          lambda a: a.confident and "9 a.m." in a.text and "5 p.m." in a.text)
    check("branch-scope-missing-control", branch, "What are the Pine branch lobby hours?",
          "Refuse because no Pine branch schedule is present.", lambda a: not a.confident)

    membership = system([page("membership", "# Membership\n\n"
                              "## Who is eligible to become a member?\n\n"
                              "- Residents of the local service area are eligible.\n"
                              "- You have a family member who is a member.\n"
                              "- Employees of a partner organization qualify.", "Membership")])
    check("eligibility-completeness", membership, "Who is eligible to become a member?",
          "Include all three published eligibility alternatives, or refuse completeness.",
          lambda a: not a.confident or all(x in a.text.lower() for x in
                                          ("resident", "family", "employee")))

    audience = system([page("business-cards", "# Business Credit Cards\n\n"
                            "| Card Type | APR |\n| --- | --- |\n"
                            "| Business Platinum Visa | 17% |", "Business Cards")])
    check("audience-ambiguity", audience, "What is the standard purchase APR on Platinum Visa?",
          "Clarify audience, or explicitly state only the business variant is supported; a row label alone does not establish an unqualified product match.",
          lambda a: not a.confident or ("business" in a.text.lower() and any(
              x in a.text.lower() for x in ("only", "specify", "clarify", "cannot confirm"))))
    cases[-1]["assessment"] = "Proposed ambiguity policy, not proof of a false value: the current answer explicitly labels Business."
    check("audience-personal-control", audience,
          "What is the personal Platinum Visa APR?",
          "Do not answer an explicitly personal request using the business-only source.",
          lambda a: not a.confident)

    distinct = system([page("savings-rates", "# Savings Rates\n\n## Maple Savings\n\n"
                            "| Balance | APY |\n| --- | --- |\n| $100+ | 2% |\n\n"
                            "## Cedar Savings\n\n| Balance | APY |\n| --- | --- |\n"
                            "| $100+ | 4% |", "Savings Rates")])
    conflicts = distinct.conflicts()
    cases.append({"id": "same-page-distinct-products", "operation": "conflicts()",
                  "expected": "Different named savings products on one page must not conflict.",
                  "passed": not conflicts, "conflicts": [asdict(c) for c in conflicts]})
    check("same-page-named-product-control", distinct, "What is the Maple Savings APY?",
          "Answer the named product without borrowing Cedar's rate.",
          lambda a: a.confident and "2%" in a.text and "4%" not in a.text)
    print(json.dumps({"mode": "basic", "evidence": "invented only",
                      "cases": cases, "passed": sum(c["passed"] for c in cases),
                      "total": len(cases), "diagnostic_only": True}, indent=2))


if __name__ == "__main__":
    main()
