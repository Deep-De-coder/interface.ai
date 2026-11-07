"""Bounded readers whose evidence must cover the requested scope."""
import re
from urllib.parse import urlsplit

# A genuine schedule row anchors a weekday (or weekday range) to a time/closed on
# the same line, e.g. "Monday-Thursday: 8:30 a.m.-5 p.m." This excludes prose that
# merely mentions a time ("closes at 4 p.m.") or image captions.
SCHEDULE_RE = re.compile(
    r"\b(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?[^\n]{0,12}?"
    r"(?:\d{1,2}(?::\d{2})?\s*[ap]\.?\s?m\.?|\bnoon\b|\bclosed\b)", re.I)

try:
    from .query import tokens
except ImportError:
    from query import tokens


def procedure_evidence(request, body, brand=(), coverage=1.0):
    """A lexical procedure guard, not a semantic entailment guarantee.

    `coverage` is the fraction of question objects the passage must contain;
    1.0 (default) requires all of them, lower values accept the best passage
    that covers most of the request (used only as a flexible fallback)."""
    if body.lstrip().startswith(">") or re.search(
            r"\b(?:not|never|cannot|can't|don't|doesn't|unable|prohibited|unavailable)\b", body, re.I):
        return False
    def normalized(text):
        text = re.sub(r"\bcontact (?:information|details)\b", "contactrecord", text.lower())
        words = tokens(text, True)
        aliases = {"updating": "update", "updates": "update", "change": "update",
                   "changing": "update", "changed": "update", "adding": "add",
                   "joining": "join", "opening": "open", "applying": "apply"}
        return {aliases.get(w, w) for w in words}
    wanted, actual = normalized(request.question), normalized(body)
    actions = wanted & {"open", "join", "update", "add", "apply", "transfer"}
    objects = wanted - actions - set(brand) - {"how", "where", "please", "would", "like", "should"}
    if not (actions & actual):
        return False
    return True if not objects else len(objects & actual) >= coverage * len(objects)


def procedure_coverage(request, body, brand=()):
    """Fraction of the request's objects present in a how-to passage (0 when the
    action is absent or the passage is negated)."""
    if body.lstrip().startswith(">") or re.search(
            r"\b(?:not|never|cannot|can't|don't|doesn't|unable|prohibited|unavailable)\b", body, re.I):
        return 0.0
    def normalized(text):
        text = re.sub(r"\bcontact (?:information|details)\b", "contactrecord", text.lower())
        aliases = {"updating": "update", "updates": "update", "change": "update",
                   "changing": "update", "changed": "update", "adding": "add",
                   "joining": "join", "opening": "open", "applying": "apply"}
        return {aliases.get(w, w) for w in tokens(text, True)}
    wanted, actual = normalized(request.question), normalized(body)
    actions = wanted & {"open", "join", "update", "add", "apply", "transfer"}
    objects = wanted - actions - set(brand) - {"how", "where", "please", "would", "like", "should"}
    if not (actions & actual):
        return 0.0
    return 1.0 if not objects else len(objects & actual) / len(objects)


def _brand(doc):
    return set((urlsplit(doc.occurrence.url).hostname or "").split("."))


def _result(store, docs, text, reason):
    try:
        from .decisions import Decision, citation
        from .models import Answer
    except ImportError:
        from decisions import Decision, citation
        from models import Answer
    return Decision("supported", reason, Answer(text, [citation(store, d) for d in docs], True), docs)


def read_scoped(store, index, request, view, target):
    """Return None only for requests outside this reader's supported intents."""
    try:
        from .decisions import refusal
    except ImportError:
        from decisions import refusal
    question = request.question.lower()
    if request.intent in ("link", "count"):
        return read_link_or_count(store, index, request, target)
    hours = "hours" in request.terms and bool(re.search(r"lobby|drive[ -]?up|branch", question))
    eligibility = bool(re.search(r"\beligib(?:le|ility)\b", question)) and not request.metric
    if not hours and not eligibility:
        return None
    hours_noise = {"hours", "lobby", "drive", "up", "branch", "branches", "general", "same",
                   "keep", "opening", "open", "today", "currently", "right", "normal", "regular",
                   "all", "every", "each", "your", "what", "are", "is", "do", "does", "the"}
    brand_words = {"dupaco", "com", "www", "inc"}
    req_location = (set(request.terms) - hours_noise - brand_words) if hours else set()
    scoped_hours = bool(req_location)
    uniformity = hours and bool(
        re.search(r"\b(?:all|every|each)\b.*\b(?:branch|branches|location|locations)\b|\bsame\b", question))
    candidates = []
    for docs, text in index.reader_groups:
        identity = set(tokens(docs[0].identity, True))
        heading = " / ".join(docs[0].section)
        if eligibility:
            if not re.search(r"\beligib(?:le|ility)\b", heading, re.I):
                continue
            subject = set(request.terms) - _brand(docs[0]) - {
                "eligible", "eligibility", "who", "become", "member", "membership", "join", "individual"}
            if subject and not subject <= identity:
                continue
            selected = [d for d in docs if not store.quote(d.occurrence, d.block.span).lstrip().startswith(">")]
            if not selected or len(selected) > 30:
                continue
            if any(d.validity.status(target) != "applicable" for d in selected):
                return refusal("The eligibility rule group has uncertain date constraints.", "uncertain")
            answer_text = heading + ":\n" + "\n".join(store.quote(d.occurrence, d.block.span) for d in selected)
            candidates.append((selected, answer_text))
        else:
            if scoped_hours and not req_location <= identity:
                continue
            channel = "drive" if re.search(r"drive[ -]?up", question) else "lobby" if "lobby" in question else None
            active = channel is None or bool(channel and channel in heading.lower())
            selected = []
            for doc in docs:
                raw = store.quote(doc.occurrence, doc.block.span)
                marker = re.search(r"\b(lobby|drive[ -]?up)\b", raw, re.I)
                if marker:
                    active = channel is None or ("drive" if marker[1].lower().startswith("drive") else "lobby") == channel
                if active and SCHEDULE_RE.search(raw):
                    selected.append(doc)
            if not selected or len(selected) > 20:
                continue
            if any(d.validity.status(target) != "applicable" for d in selected):
                return refusal("The schedule has uncertain date constraints.", "uncertain")
            candidates.append((selected, "\n".join(store.quote(d.occurrence, d.block.span) for d in selected)))
    if not candidates:
        return refusal("No complete eligibility rule group supports that subject." if eligibility else
                       "No schedule establishes hours for the requested location scope.", "uncertain")
    if eligibility:
        # Multiple distinct rule groups cannot be resolved by retrieval rank.
        if len({text for _, text in candidates}) != 1:
            return refusal("Applicable sources provide different rule groups or schedules.", "conflicting")
        docs, text = candidates[0]
        return _result(store, docs, text, "Complete bounded eligibility rule group.")
    # Hours. A uniquely named branch must still resolve to one schedule, but an
    # unscoped question yields the representative schedule (or an enumeration of
    # the distinct ones) and an offer to narrow by branch, rather than a refusal.
    groups, order = {}, []
    for sel, text in candidates:
        if text not in groups:
            groups[text] = list(sel)
            order.append(text)
        else:
            groups[text].extend(sel)
    if scoped_hours:
        if len(order) != 1:
            return refusal("Applicable sources provide different schedules for that scope.", "conflicting")
        return _result(store, groups[order[0]], order[0],
                       "Schedule evidence matches the requested location scope.")
    docs = [d for t in order for d in groups[t]]
    if len(order) == 1:
        if uniformity:
            body = "Branch schedules on file all match:\n" + order[0]
        else:
            body = ("Hours vary by branch. A typical schedule is:\n" + order[0]
                    + "\nTell me which branch, or ask for all branches, for exact times.")
        return _result(store, groups[order[0]], body, "Branch schedule with branch clarification.")
    listing = "\n\n".join(order)
    if uniformity:
        body = ("Branch hours are not all the same. The schedules on file are:\n\n"
                + listing + "\n\nTell me which branch for exact hours.")
    else:
        body = ("Hours vary by branch. Typical schedules on file:\n\n"
                + listing + "\n\nTell me which branch, or ask for all branches, for exact times.")
    return _result(store, docs, body, "Branch schedules with branch clarification.")


def read_link_or_count(store, index, request, target):
    try:
        from .decisions import refusal
    except ImportError:
        from decisions import refusal
    noise = {"link", "url", "locator", "should", "use", "see", "many", "number", "total"}
    candidates = []
    evidence = index.count_statements if request.intent == "count" else index.labeled_links
    for doc, supported_terms, excerpt in evidence:
        if doc.validity.status(target) != "applicable":
            continue
        wanted = set(request.terms) - noise - _brand(doc)
        if request.intent == "count":
            # An explicit count is evidence; counting locator/ATM entries is not.
            if not wanted <= supported_terms:
                continue
            candidates.append(([doc], excerpt))
        else:
            if wanted and wanted <= supported_terms:
                candidates.append(([doc], excerpt))
    if not candidates:
        return refusal("No explicit count supports the requested subject." if request.intent == "count" else
                       "No explicitly labeled link supports the requested subject.", "uncertain")
    if request.intent == "count" and len({text for _, text in candidates}) > 1:
        return refusal("Multiple count statements need an explicit reporting period or scope.", "ambiguous")
    docs, text = candidates[0]
    return _result(store, docs, text, "Explicit published count or labeled link.")
