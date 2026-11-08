"""Conservative comparable table disagreements, retaining source history."""
from collections import defaultdict
import re
try:
    from .models import Conflict
    from .decisions import citation, metric_column
    from .facts import canonical, fact_scope
except ImportError:
    from models import Conflict
    from decisions import citation, metric_column
    from facts import canonical, fact_scope


def resolve_entries(entries, target=None):
    if not entries:
        return None, "No comparable facts were supplied."
    latest = max(d.occurrence.taken_on for _, d in entries)
    target = target or latest
    current = [(canonical(v), d) for v, d in entries if d.occurrence.taken_on == latest
               and d.validity.status(target) == "applicable"]
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
                key = fact_scope(doc, metric)
                groups[key].append((canonical(doc.block.cells[col]), doc))
    def comparable(v):
        # Collapse escaping/whitespace so "$25.00* " and "$25.00\\*" are not a conflict.
        return re.sub(r"\s+", " ", re.sub(r"\\(.)", r"\1", v)).strip().lower()

    def scalar_value(v):
        # A genuine contradiction is between short scalar figures (rates/fees), not
        # multi-clause prose ("intro offer ... after that ...") or an open range.
        c = comparable(v)
        return c if len(c) <= 24 and re.search(r"\d", c) and not re.search(r"[–—]|\bto\b|intro|after", c) else None

    result = []
    for (entity, audience, channel, purpose, metric, qualifiers), entries in sorted(groups.items()):
        scalars = [(scalar_value(v), v, d) for v, d in entries if scalar_value(v)]
        values = sorted({s for s, _, _ in scalars})
        if len(values) < 2:
            continue
        resolution, reason = resolve_entries([(v, d) for _, v, d in scalars])
        unique = {}
        for norm, value, doc in scalars:
            unique.setdefault((norm, doc.occurrence.snapshot_id), doc)
        topic = metric.upper() + ": " + " / ".join(entity[1:]) + "; " + "; ".join(f"{h}={c}" for h, c in qualifiers)
        result.append(Conflict(topic, values, [citation(store, d) for d in unique.values()],
                               comparable(resolution) if resolution else resolution, reason))
    return result
