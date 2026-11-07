"""Shared conservative reader. Retrieval scores are not answer confidence."""
from dataclasses import dataclass, field
from decimal import Decimal
import re

try:
    from .models import Answer, Source
    from .query import tokens, procedure_supported
    from .temporal import DATE
except ImportError:
    from models import Answer, Source
    from query import tokens, procedure_supported
    from temporal import DATE

GENERIC = set("apy apr rate fee interest dividend balance tier minimum amount saving savings account certificate loan term month year model auto historical access method option transfer wire current latest difference change changed between compare did effective percent percentage yield annual special pay pays earn earning offer offered required requirement deposit online banking withdrawal how eligible eligibility join member individual business personal product policy description explain scheduled announced".split())


@dataclass
class Decision:
    status: str
    reason: str
    answer: Answer
    selected: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    scope: tuple = ()


def refusal(reason, status="insufficient", sources=None):
    return Decision(status, reason, Answer("I don't know. " + reason, sources or [], False))


def citation(store, doc):
    spans = [doc.block.span, *doc.context_spans]
    if doc.block.header:
        spans.append(doc.block.header)
    # Separate exact excerpts, with explicit omissions. No manufactured quotes.
    spans = sorted(set(spans), key=lambda s: s.start)
    quote = "\n[…]\n".join(store.quote(doc.occurrence, s) for s in spans)
    return Source(doc.occurrence.url, doc.occurrence.snapshot_id, quote)


def number(value):
    return Decimal(value.replace(",", ""))


def range_contains(text, value):
    """Inclusive displayed financial ranges; unknown formats do not match."""
    text = text.replace(",", "")
    bounds = re.findall(r"\d+(?:\.\d+)?", text)
    if not bounds:
        return False
    low = number(bounds[0])
    if len(bounds) >= 2 and re.search(r"[–—-]|\bto\b", text):
        return low <= value <= number(bounds[1])
    if "+" in text or re.search(r"\b(?:or more|and over|at least)\b", text, re.I):
        return value >= low
    if re.search(r"\b(?:up to|under|less than)\b", text, re.I):
        return value <= low if "up to" in text.lower() else value < low
    return value == low


def row_matches(request, doc):
    cells = doc.block.cells
    if request.metric in ("apr", "rate") and re.search(r"card|visa", doc.identity, re.I):
        requested_promo = re.search(r"intro|transfer|promotion|cash advance", request.question, re.I)
        if not requested_promo and re.search(r"intro|transferred balances|balance transfer|cash advance", " ".join(cells), re.I):
            return False
    if request.metric == "fee":
        service = set(request.terms) & {"wire", "transfer", "overdraft", "withdrawal", "maintenance"}
        if not service <= set(tokens(" ".join(cells), True)):
            return False
    if request.amount is not None:
        columns = [c for h, c in zip(doc.headers, cells) if re.search(r"balance|tier|loan amount", h, re.I)]
        if not columns or not any(range_contains(c, request.amount) for c in columns):
            return False
    if request.term_months is not None:
        label = " ".join(c for h, c in zip(doc.headers, cells) if re.search(r"term|month|year|certificate|product|program|type", h, re.I))
        pairs = re.findall(r"(\d+)\s*[- ]*\s*(month|year)", label, re.I)
        if not pairs or not any(int(n) * (12 if unit.lower() == "year" else 1) == request.term_months for n, unit in pairs):
            return False
    if request.model_year is not None:
        columns = [c for h, c in zip(doc.headers, cells) if re.search(r"model|vehicle year", h, re.I) or "model year" in c.lower()]
        columns = [re.sub(r"(20\d{2})-(\d{2})\b", lambda m: m[1] + "-20" + m[2], c) for c in columns]
        if not columns or not any(range_contains(c, Decimal(request.model_year)) for c in columns):
            return False
    return True


def metric_column(metric, headers):
    for i, h in enumerate(headers):
        h = h.lower()
        if metric == "apy" and ("apy" in h or "annual percentage yield" in h):
            return i
        if metric == "apr" and ("apr" in h or "annual percentage rate" in h):
            return i
        if metric == "fee" and re.search(r"fee|charge|cost", h):
            return i
        if metric == "rate" and "rate" in h and "apr" not in h and "annual percentage" not in h:
            return i
    if metric == "rate":
        return metric_column("apy", headers) if metric_column("apy", headers) is not None else metric_column("apr", headers)
    return None


def entity_terms(request):
    q = re.sub(DATE, "", request.question, flags=re.I)
    q = re.sub(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b", "", q, flags=re.I)
    q = re.sub(r"\d+(?:\.\d+)?\s*%", "", q)
    return {t for t in tokens(q, True) if t not in GENERIC and not t.isdigit() and t not in {"right", "standard", "purchase", "provide", "repeat", "earn", "between", "highest", "maximum", "lowest", "any", "tiers"}}


def entity_matches(request, doc, anchors):
    identity = set(tokens(doc.identity, True))
    from urllib.parse import urlsplit
    brand = set(urlsplit(doc.occurrence.url).hostname.split("."))
    anchors = anchors - brand
    if anchors and not anchors <= identity:
        return False
    # Audience qualifier is asymmetric: an explicit business request cannot use
    # personal rows. Broad requests can return labeled scopes later.
    if "business" in request.terms and "business" not in identity:
        return False
    if "personal" in request.terms and "business" in identity:
        return False
    if {"personal", "loan"} <= set(request.terms) and "personal" not in identity:
        return False
    return True


def decide(store, index, request, view, mode, event_date=None, limit=40):
    target = event_date or min(view.requested_on, view.observed_on)
    ranked = index.search(request, mode, target, limit=limit)
    anchors = entity_terms(request)
    # Domain nouns are also required when no named entity is present.
    if not anchors:
        anchors = set(request.terms) & {"mortgage", "auto", "certificate", "saving", "savings", "checking", "credit", "wire", "transfer"}
    usable = [(d, s) for d, s in ranked if entity_matches(request, d, anchors)]
    if request.metric:
        # Structured facts are cheap to enumerate. Top-k passage ranking must
        # not hide a newer applicable schedule or a competing table value.
        seen = {d.key for d, _ in usable}
        for doc in index.docs:
            if doc.headers and doc.key not in seen and entity_matches(request, doc, anchors):
                if metric_column(request.metric, doc.headers) is not None:
                    usable.append((doc, 0.0))
    if not request.metric and not usable:
        from urllib.parse import urlsplit
        for d, score in ranked:
            required = anchors - set(urlsplit(d.occurrence.url).hostname.split("."))
            content = set(tokens(d.text + " " + d.identity, True))
            if required and required <= content:
                usable.append((d, score))
    def finish(result):
        result.candidates = [d for d, _ in ranked]
        if result.answer.confident and view.note:
            result.answer.text += " " + view.note
        return result
    try:
        from .readers import read_scoped
    except ImportError:
        from readers import read_scoped
    scoped = read_scoped(store, index, request, view, target)
    if scoped is not None:
        return finish(scoped)
    if not usable:
        return finish(refusal("I could not find sufficient evidence for that subject in the selected snapshot."))
    if {"routing", "number"} <= set(request.terms):
        matches = [d for d, _ in usable if re.search(r"routing\s+number.{0,12}\b\d{9}\b", d.text, re.I)]
        values = {re.search(r"\b\d{9}\b", d.text)[0] for d in matches}
        if len(values) == 1:
            doc = matches[0]
            return finish(Decision("supported", "Explicit routing identifier in source.",
                                  Answer(store.quote(doc.occurrence, doc.block.span), [citation(store, doc)], True), [doc]))
        return finish(refusal("The routing identifier is missing or conflicting."))
    if request.intent == "procedure":
        from urllib.parse import urlsplit
        for doc, _ in usable:
            if doc.block.kind not in ("passage", "list_item"):
                continue
            body = store.quote(doc.occurrence, doc.block.span)
            brand = (urlsplit(doc.occurrence.url).hostname or "").split(".")
            if procedure_supported(request, body, brand) and doc.validity.status(target) == "applicable" and len(body.split()) >= 8:
                return finish(Decision("supported", "Published procedural excerpt.",
                                      Answer(body, [citation(store, doc)], True), [doc]))
        return finish(refusal("The retrieved evidence does not establish that procedure."))
    if request.metric:
        try:
            from .facts import fact_scope, canonical
            from .conflicts import resolve_entries
        except ImportError:
            from facts import fact_scope, canonical
            from conflicts import resolve_entries
        accepted, blocked = [], []
        for doc, score in usable:
            if not doc.headers or any(w != "escaped_newlines_interpreted" for w in doc.block.warnings):
                continue
            col = metric_column(request.metric, doc.headers)
            if col is None or col >= len(doc.block.cells) or not row_matches(request, doc):
                continue
            value = doc.block.cells[col]
            if not re.search(r"\d", value):
                continue
            state = doc.validity.status(target)
            if state != "applicable":
                blocked.append((doc, state))
                continue
            scope = fact_scope(doc, request.metric)
            accepted.append((doc, score, col, value, scope))
        if not accepted:
            reason = "No validated table value supports the requested metric and qualifiers."
            if blocked:
                reason = "Matching evidence is scheduled, expired, or has inconsistent effective dates."
            return finish(refusal(reason, "uncertain" if blocked else "insufficient"))
        # Present distinct published metrics with their labels. Prefer current
        # explicit schedules to undated examples, without changing eligibility.
        accepted.sort(key=lambda x: (x[0].validity.start or "", x[1]), reverse=True)
        # Resolve every scope that can reach the output, including later rows.
        from collections import defaultdict
        chosen = accepted[0]
        chosen_table = (chosen[0].occurrence.url, chosen[0].block.header)
        all_scopes = request.intent == "list" or request.operation != "value" or any(
            "card type" in [h.lower() for h in x[0].headers] for x in accepted)
        requested_scopes = {x[4] for x in accepted if all_scopes or
                            (x[0].occurrence.url, x[0].block.header) == chosen_table}
        groups = defaultdict(list)
        for item in accepted:
            if item[4] in requested_scopes:
                groups[item[4]].append(item)
        resolved, unresolved, notes = [], [], []
        for group in groups.values():
            winner, reason = resolve_entries([(x[3], x[0]) for x in group], target=target)
            if winner is None:
                unresolved.extend(x[0] for x in group)
                continue
            resolved.append(next(x for x in group if canonical(x[3]) == winner))
            if len({canonical(x[3]) for x in group}) > 1:
                notes.append(reason)
        def scalar(item):
            value = canonical(item[3])
            match = re.fullmatch(r"\$?(\d+(?:\.\d+)?)\s*%?", value)
            return Decimal(match[1]) if match else None
        if request.operation == "exists" and request.predicate is not None:
            # A positive witness is sufficient; absence is not proof of no tier.
            resolved = [x for x in resolved if scalar(x) == request.predicate]
            if not resolved:
                return finish(refusal("No resolved matching tier establishes the requested value."))
        elif unresolved:
            result = refusal("A requested output fact has unresolved competing values.",
                             "conflicting", [citation(store, d) for d in unresolved])
            result.selected = unresolved
            result.answer.conflict_note = "Conflicting entries were not silently omitted."
            return finish(result)
        if request.operation in ("max", "min"):
            values = [scalar(x) for x in resolved]
            if not values or any(v is None for v in values) or blocked:
                return finish(refusal("An extreme requires comparable scalar values and complete applicable tiers.", "uncertain"))
            extreme = (max if request.operation == "max" else min)(values)
            resolved = [x for x in resolved if scalar(x) == extreme]
        # Malformed or uncertain rows in the selected schedule cannot vanish.
        for doc in index.docs:
            if (doc.occurrence.url, doc.block.header) != chosen_table:
                continue
            if not entity_matches(request, doc, anchors) or not row_matches(request, doc):
                continue
            if any(w != "escaped_newlines_interpreted" for w in doc.block.warnings) or doc.validity.status(target) != "applicable":
                return finish(refusal("The matching table contains uncertain rows; a complete answer is not supported.", "uncertain"))
        rows = [(x[0], x[2]) for x in resolved]
        resolution_note = " ".join(dict.fromkeys(notes)) or None
        if len(rows) > 20:
            return finish(refusal("Please narrow the product or tier so the complete result can be shown.", "ambiguous"))
        texts, docs = [], []
        for doc, col in rows:
            labels = [f"{h}: {c}" for i, (h, c) in enumerate(zip(doc.headers, doc.block.cells))
                      if i != col and (request.metric == "rate" or not re.search(r"(?:rate|apy|apr|yield)", h, re.I))]
            texts.append(f"{'; '.join(labels)} — {doc.headers[col]}: {doc.block.cells[col]}")
            docs.append(doc)
        if request.operation in ("max", "min"):
            texts.insert(0, "Among the published matching tiers:")
        if request.operation == "exists":
            texts.insert(0, "A published matching tier exists:")
        if request.intent != "list" and not {"business", "personal"} & set(request.terms) and any("business" in tokens(d.identity, True) for d in docs):
            texts.insert(0, "Only the labeled variants below are established by this evidence; specify the audience if you mean another variant.")
        result = Decision("supported", "Validated table cells with matching qualifiers.",
                          Answer("\n".join(texts), [citation(store, d) for d in docs], True), docs,
                          scope=(tuple(sorted(anchors)), request.metric, tuple(sorted((x[4] for x in resolved), key=repr))))
        result.answer.conflict_note = resolution_note
        return finish(result)
    # A bounded list is the entire selected explicit list section. We do not
    # claim to enumerate every service on the whole site.
    if request.intent == "list":
        for doc, _ in usable:
            items = index.section_items(doc)
            if not items or len(items) > 30:
                continue
            if any(d.validity.status(target) != "applicable" for d in items):
                return finish(refusal("The list contains uncertain date constraints.", "uncertain"))
            heading_terms = set(tokens(" ".join(doc.section), True))
            topic = set(request.terms) - anchors - {"method", "option"}
            if not topic & heading_terms:
                continue
            text = "Published in " + " / ".join(doc.section) + ":\n" + "\n".join(store.quote(d.occurrence, d.block.span) for d in items)
            return finish(Decision("supported", "Complete explicit list section.", Answer(text, [citation(store, d) for d in items], True), items))
        return finish(refusal("No complete explicit list section supports that request."))
    # Descriptive support: extract an actual passage, not a heading or link.
    wanted = set(request.terms) - anchors - {"saving", "savings", "account", "loan", "certificate", "product", "member"}
    for doc, _ in usable:
        if doc.block.kind != "passage" or doc.validity.status(target) != "applicable":
            continue
        body = store.quote(doc.occurrence, doc.block.span)
        body_terms = set(tokens(body, True))
        heading_terms = set(tokens(" ".join(doc.section), True))
        if len(body.split()) < 6 or not wanted or not wanted & (body_terms | heading_terms):
            continue
        if event_date and event_date not in body and not re.search(DATE, body, re.I):
            continue
        return finish(Decision("supported", "Extracted supporting passage; semantic review remains necessary.",
                               Answer(body, [citation(store, doc)], True), [doc]))
    return finish(refusal("The retrieved material does not sufficiently support that question."))
