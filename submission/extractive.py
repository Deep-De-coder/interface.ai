"""Bounded extractive fallback for descriptive, contact and procedure queries."""
import re
from urllib.parse import urlsplit
try:
    from .query import tokens
    from .models import Answer
    from .decisions import Decision, citation
except ImportError:
    from query import tokens
    from models import Answer
    from decisions import Decision, citation

NOISE = set("tell repeat received recognition general still today currently should use see link url provide know would like any standard become become going new options flexibility can all same keep highest many employees last year how when where who eligible information number address hours branches branch online".split())


def extract(store, index, request, view, mode):
    if request.metric:
        return None  # Unrelated numbers cannot substitute for an absent rate.
    ranked = index.search(request, mode, view.observed_on, limit=160)
    best = []
    for doc, score in ranked:
        if doc.block.kind not in ("passage", "list_item"):
            continue
        raw = store.quote(doc.occurrence, doc.block.span)
        if len(raw.split()) < 5 or len(raw) > 2500 or raw.lstrip().startswith("!["):
            continue
        brand = set(urlsplit(doc.occurrence.url).hostname.split("."))
        focus = set(request.terms) - NOISE - brand
        body = set(tokens(raw, True))
        if not focus or not focus <= body:
            continue
        if doc.validity.status(view.observed_on) != "applicable":
            continue
        if "hours" in request.terms and not re.search(r"\d.*(?:a\.?m|p\.?m|Monday|Friday)", raw, re.I):
            continue
        if "address" in request.terms and not re.search(r"\d+.*(?:street|road|lane|avenue|\b(?:st|rd|ln|ave)\.)", raw, re.I):
            continue
        if "many" in request.question and not re.search(r"\b\d+\s+(?:\w+\s+){0,2}(?:branches|employees|members)", raw, re.I):
            continue
        best.append((doc, score))
    if not best:
        return None
    doc = best[0][0]
    text = store.quote(doc.occurrence, doc.block.span)
    if view.note:
        text += " " + view.note
    return Decision("supported", "Exact descriptive excerpt with matching subject terms.",
                    Answer(text, [citation(store, doc)], True), [doc], [d for d, _ in ranked])
