"""Independently authored synthetic gold, never imported by submission code.

Six development families and three held-out families, four cases each. These
invented fixtures are publishable; they complement, not replace, corpus gold.
"""
from types import SimpleNamespace as Obj

FAMILIES = (
    ("Alder", "1.20", "1.45", "100", "dev"),
    ("Birch", "2.10", "2.35", "250", "dev"),
    ("Cedar", "3.00", "3.25", "500", "dev"),
    ("Dogwood", "1.80", "2.05", "750", "dev"),
    ("Elm", "2.60", "2.85", "1000", "dev"),
    ("Fir", "3.40", "3.65", "1500", "dev"),
    ("Ginkgo", "1.35", "1.60", "2000", "holdout"),
    ("Hazel", "2.45", "2.70", "3000", "holdout"),
    ("Iris", "3.55", "3.80", "4000", "holdout"),
)


def fixtures():
    cases, snapshots = [], []
    for sid, taken, index in (("synthetic_old", "2026-01-01", 1), ("synthetic_new", "2026-03-01", 2)):
        pages = []
        for family in FAMILIES:
            name, old, new, minimum, split = family
            url = f"https://example.test/{name.lower()}"
            raw = (f"# {name} Savings\n\nFor individual members only.\n\n"
                   f"| Balance | APY |\n| --- | --- |\n| ${minimum}+ | {family[index]}% |\n\n"
                   "Fees may reduce earnings.\n\n"
                   "## Access\n\n- Online banking\n- Branch withdrawals\n")
            pages.append(Obj(url=url, title=f"{name} Savings", markdown=raw, fetched_at=taken))
            if index == 2:
                definitions = [
                    ("current", f"What APY applies to {name} Savings at ${minimum} or more?", None, [new + "%"], False),
                    ("historical", f"What was the APY for {name} Savings at ${minimum} or more?", "2026-01-15", [old + "%"], False),
                    ("list", f"List the access methods published for {name} Savings.", None, ["Online banking", "Branch withdrawals"], False),
                    ("missing", f"What is the wire transfer fee for {name} Savings?", None, [], True),
                ]
                for kind, question, as_of, expected, refuse in definitions:
                    cases.append(dict(id=f"{name.lower()}-{kind}", family=name, split=split,
                                      category=kind, question=question, as_of=as_of,
                                      must_include=expected, should_refuse=refuse,
                                      expected_sources=[] if refuse else [url],
                                      expected_snapshot="synthetic_old" if kind == "historical" else sid))
        snapshots.append(Obj(snapshot_id=sid, taken_on=taken, pages=pages))
    return snapshots, cases


PARAPHRASES = {
    name: f"For a balance of at least ${minimum}, give the latest annual percentage yield on {name} Savings."
    for name, old, new, minimum, split in FAMILIES if split == "dev"
}
