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
    result = []
    for (entity, audience, channel, purpose, metric, qualifiers), entries in sorted(groups.items()):
        values = sorted({v for v, _ in entries})
        if len(values) < 2:
            continue
        resolution, reason = resolve_entries(entries)
        unique = {}
        for value, doc in entries:
            unique.setdefault((value, doc.occurrence.snapshot_id), doc)
        topic = metric.upper() + ": " + " / ".join(entity[1:]) + "; " + "; ".join(f"{h}={c}" for h, c in qualifiers)
        result.append(Conflict(topic, values, [citation(store, d) for d in unique.values()], resolution, reason))
    return result
