"""Bounded readers whose evidence must cover the requested scope."""
import re
from urllib.parse import urlsplit

try:
    from .query import tokens
except ImportError:
    from query import tokens


def procedure_evidence(request, body, brand=()):
    """A lexical procedure guard, not a semantic entailment guarantee."""
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
    return bool(actions & actual) and objects <= actual


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
            noise = {"hours", "lobby", "drive", "up", "branch", "branches", "general", "same",
                     "keep", "opening", "open", "today", "currently", "right", "normal", "regular"}
            location = set(request.terms) - noise - _brand(docs[0])
            if location:
                if not location <= identity:
                    continue
            elif not re.search(r"\b(?:all branches|every branch|general (?:lobby |branch )?hours)\b", heading + "\n" + text, re.I):
                continue
            channel = "drive" if re.search(r"drive[ -]?up", question) else "lobby" if "lobby" in question else None
            active = channel is None or bool(channel and channel in heading.lower())
            selected = []
            for doc in docs:
                raw = store.quote(doc.occurrence, doc.block.span)
                marker = re.search(r"\b(lobby|drive[ -]?up)\b", raw, re.I)
                if marker:
                    active = channel is None or ("drive" if marker[1].lower().startswith("drive") else "lobby") == channel
                if active and re.search(r"\d.*(?:a\.?m\.?|p\.?m\.?)|\bclosed\b", raw, re.I):
                    selected.append(doc)
            if not selected or len(selected) > 20:
                continue
            if any(d.validity.status(target) != "applicable" for d in selected):
                return refusal("The schedule has uncertain date constraints.", "uncertain")
            candidates.append((selected, "\n".join(store.quote(d.occurrence, d.block.span) for d in selected)))
    if not candidates:
        return refusal("No complete eligibility rule group supports that subject." if eligibility else
                       "No schedule establishes hours for the requested location scope.", "uncertain")
    # Multiple distinct rule groups/schedules cannot be resolved by retrieval rank.
    distinct = {text for _, text in candidates}
    if len(distinct) != 1:
        return refusal("Applicable sources provide different rule groups or schedules.", "conflicting")
    docs, text = candidates[0]
    return _result(store, docs, text, "Complete bounded eligibility rule group." if eligibility else
                   "Schedule evidence matches the requested location scope.")


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
