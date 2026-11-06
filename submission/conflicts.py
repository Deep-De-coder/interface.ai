"""Conservative comparable table disagreements, retaining source history."""
from collections import defaultdict
import re
try:
    from .models import Conflict
    from .decisions import citation, metric_column
except ImportError:
    from models import Conflict
    from decisions import citation, metric_column


def canonical(value):
    value = value.lower().replace(",", "").replace("–", "-")
    value = re.sub(r"(%)(?:\d+|\[\d+\])", r"\1", value)
    return re.sub(r"\s+", " ", value).strip()


def resolve_entries(entries):
    latest = max(d.occurrence.taken_on for _, d in entries)
    current = [(v, d) for v, d in entries if d.occurrence.taken_on == latest
               and d.validity.status(latest) == "applicable"]
    values = {v for v, _ in current}
    if len(values) == 1:
        return next(iter(values)), "Latest applicable observation for matching entity, metric and qualifiers."
    if current and all(d.validity.start for _, d in current):
        effective = max(d.validity.start for _, d in current)
        values = {v for v, d in current if d.validity.start == effective}
        if len(values) == 1:
            return next(iter(values)), "Newer explicit effective date among comparable applicable sources."
    return None, "Competing or temporally uncertain values; no justified winner."


def enumerate_conflicts(store, indexes):
    groups = defaultdict(list)
    for index in indexes.values():
        for doc in index.docs:
            if not doc.headers or any(w != "escaped_newlines_interpreted" for w in doc.block.warnings):
                continue
            for metric in ("apy", "apr", "rate", "fee"):
                if metric == "rate" and not any("rate" in h.lower() and "percentage" not in h.lower() and "apr" not in h.lower() for h in doc.headers):
                    continue
                col = metric_column(metric, doc.headers)
                if col is None or col >= len(doc.block.cells):
                    continue
                qualifiers = tuple((canonical(h), canonical(c)) for h, c in zip(doc.headers, doc.block.cells)
                                   if not re.search(r"apy|apr|yield|rate|fee|payment|points", h, re.I))
                # Preserve page identity: cross-URL entity equivalence is not
                # assumed just because two numeric tiers happen to match.
                named = any(re.search(r"account type|card type|certificate", h, re.I) for h, _ in qualifiers)
                key = ("named-product" if named else doc.occurrence.url, metric, qualifiers)
                groups[key].append((canonical(doc.block.cells[col]), doc))
    result = []
    for (url, metric, qualifiers), entries in sorted(groups.items()):
        values = sorted({v for v, _ in entries})
        if len(values) < 2:
            continue
        resolution, reason = resolve_entries(entries)
        unique = {}
        for value, doc in entries:
            unique.setdefault((value, doc.occurrence.snapshot_id), doc)
        topic = metric.upper() + ": " + "; ".join(f"{h}={c}" for h, c in qualifiers)
        result.append(Conflict(topic, values, [citation(store, d) for d in unique.values()], resolution, reason))
    return result
