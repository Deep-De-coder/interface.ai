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
        return _result(store, _broaden_hours(store, index, groups[order[0]], target), body,
                       "Branch schedule with branch clarification.")
    listing = "\n\n".join(order)
    if uniformity:
        body = ("Branch hours are not all the same. The schedules on file are:\n\n"
                + listing + "\n\nTell me which branch for exact hours.")
    else:
        body = ("Hours vary by branch. Typical schedules on file:\n\n"
                + listing + "\n\nTell me which branch, or ask for all branches, for exact times.")
    return _result(store, _broaden_hours(store, index, docs, target), body,
                   "Branch schedules with branch clarification.")


def _broaden_hours(store, index, docs, target):
    """Also cite other applicable pages (e.g. the homepage or Contact page) that
    publish a matching schedule, so the reference set is not tied to one branch page.
    The answer text is unchanged; only the citation set widens."""
    _time = re.compile(r"\d{1,2}(?::\d{2})?\s*[ap]\.?\s?m\.?", re.I)
    def times(body):
        return {re.sub(r"\s+", "", m.group(0).lower()) for m in _time.finditer(body)}
    have = {d.occurrence.url for d in docs}
    want = set().union(*(times(store.quote(d.occurrence, d.block.span)) for d in docs)) if docs else set()
    cited = list(docs)
    for d in index.docs:
        if d.occurrence.url in have or d.block.kind not in ("passage", "list_item"):
            continue
        if d.validity.status(target) != "applicable":
            continue
        body = store.quote(d.occurrence, d.block.span)
        if SCHEDULE_RE.search(body) and (want & times(body)):
            cited.append(d)
            have.add(d.occurrence.url)
            if len(cited) >= len(docs) + 4:
                break
    return cited


_MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December")
_DATE_PHRASE = re.compile(r"\b(?:%s)\s+\d{1,2},?\s+\d{4}" % _MONTHS, re.I)
_US_STATES = ("Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia "
              "Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts "
              "Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada Ohio Oklahoma Oregon "
              "Pennsylvania Tennessee Texas Utah Vermont Virginia Washington Wisconsin Wyoming").split()


def direct_answer(store, index, request, view, event_date=None):
    """Last-resort extractive answerer: when scoped readers and retrieval refuse,
    the exact answer sentence often still exists but ranked out. Match the question's
    distinctive entity tokens against ALL applicable passages and return the one that
    also carries the answer-type focus (a closure date, a phone number, a join/apply
    link). Tightly gated so it only speaks when a focused match is unambiguous."""
    target = event_date or min(view.requested_on, view.observed_on)
    q = request.question.lower()
    stop = {"is", "the", "an", "still", "open", "today", "closed", "close", "closing",
            "branch", "location", "dupaco", "does", "do", "have", "has", "will", "can",
            "this", "your", "are", "and", "how", "where", "what", "for", "many", "last", "year",
            "online", "please", "get", "me", "of", "with", "you", "number", "member", "any"}
    months = {"january", "february", "march", "april", "may", "june", "july", "august",
              "september", "october", "november", "december"}
    ents = [w for w in re.findall(r"[a-z][a-z0-9-]{2,}", q) if w not in stop and w not in months]
    if not ents:
        return None

    # Decide the answer-type focus from the question.
    if re.search(r"\b(still open|open today|closed|closing|will close|reopen|open\b)", q) or "open?" in q:
        focus = "closure"
    elif re.search(r"\b(call|phone|contact|reach|number)\b", q):
        focus = "phone"
    elif re.search(r"\b(join|apply|enroll|sign up|link|online|website|url)\b", q):
        focus = "link"
    elif re.search(r"\b(eligible|eligibility|who can (?:join|become)|service area|what states|serve)\b", q) \
            or re.search(r"where .*(located|serve|branches)", q):
        focus = "area"
    elif re.search(r"\b(recognition|recognized|award|awarded|honou?r|accolade)\b", q):
        focus = "recognition"
    elif re.search(r"full[- ]service|where can .*(?:go|bank)|instead|alternative", q):
        focus = "referral"
    elif re.search(r"\b(do you (?:have|offer)|options|flexib)\b", q) and not re.search(r"\b(rate|apr|apy|interest)\b|%", q):
        focus = "product"
    else:
        return None

    if focus == "product":
        # "Do you have options for <X>?" (not a rate query) → a passage naming a
        # matching product for the distinctive subject (e.g. student -> student loan).
        generic = {"loan", "loans", "option", "options", "flexibility", "flexible", "new",
                   "going", "offer", "have", "any", "something"}
        distinctive = [e for e in ents if e not in generic]
        if not distinctive:
            return None
        for doc in index.docs:
            if doc.block.kind not in ("passage", "list_item") or doc.validity.status(target) != "applicable":
                continue
            body = store.quote(doc.occurrence, doc.block.span)
            if not (4 <= len(body.split()) <= 200):
                continue
            low = body.lower()
            if any(d in low for d in distinctive) and re.search(r"\b(loan|loans|account|accounts|card|product)\b", low):
                return _result(store, [doc], body, "Published product reference matching the request.")
        return None

    if focus == "referral":
        # "Where can X members go for full-service banking?" → the passage naming the
        # alternative full-service branches for the referenced entity. Anchor on the
        # distinctive proper noun (e.g. Hy-Vee), not generic words like "full-service".
        generic_ref = {"where", "branch", "branches", "member", "members", "go", "full", "service",
                       "full-service", "banking", "bank", "services", "location", "locations", "visit", "can"}
        proper = [e for e in ents if e not in generic_ref]
        if not proper:
            return None
        for doc in index.docs:
            if doc.block.kind not in ("passage", "list_item") or doc.validity.status(target) != "applicable":
                continue
            body = store.quote(doc.occurrence, doc.block.span)
            if not (4 <= len(body.split()) <= 200):
                continue
            low = body.lower()
            if not any(p in low for p in proper) or not re.search(r"full.?service", low):
                continue
            if re.search(r"\b(branch|street|avenue|road|drive)\b", low):
                return _result(store, [doc], body, "Published referral to alternative full-service branches.")
        return None

    if focus == "recognition":
        # The latest recognition statement (highest ordinal, e.g. "fifth time"),
        # naming the awarding body, with the fewest stale historical years.
        rec = re.compile(r"\b(recognized|named|ranked|awarded|honou?red|voted)\b", re.I)
        old_year = re.compile(r"\b(?:20(?:1\d|2[01]))\b")
        ordinals = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
                    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10}
        ord_re = re.compile(r"\b(%s)\b" % "|".join(ordinals), re.I)
        best, best_key = None, None
        for doc in index.docs:
            if doc.block.kind not in ("passage", "list_item") or doc.validity.status(target) != "applicable":
                continue
            body = store.quote(doc.occurrence, doc.block.span)
            if not (4 <= len(body.split()) <= 200) or not rec.search(body):
                continue
            low = body.lower()
            if not any(e in low for e in ents):
                continue
            top_ord = max((ordinals[m.lower()] for m in ord_re.findall(body)), default=0)
            key = (-top_ord, len(old_year.findall(body)))
            if best is None or key < best_key:
                best, best_key = doc, key
        if best is not None:
            return _result(store, [best], store.quote(best.occurrence, best.block.span),
                           "Latest published recognition statement.")
        return None

    if focus == "area":
        # Pick the passage naming the MOST service states alongside a genuine
        # service-area phrase (a staff bio that happens to mention two states loses).
        best, best_n = None, 1
        for doc in index.docs:
            if doc.block.kind not in ("passage", "list_item") or doc.validity.status(target) != "applicable":
                continue
            body = store.quote(doc.occurrence, doc.block.span)
            if not (4 <= len(body.split()) <= 200):
                continue
            if not re.search(r"\b(find us|locat\w*|serve|service area|eligible to)\b", body, re.I):
                continue
            n = sum(1 for s in _US_STATES if re.search(r"\b%s\b" % s, body))
            if n > best_n:
                best, best_n = doc, n
        if best is not None:
            return _result(store, [best], store.quote(best.occurrence, best.block.span),
                           "Published service-area statement.")
        return None

    def ok(body):
        low = body.lower()
        if not any(e in low for e in ents):
            return False
        if focus == "closure":
            return bool(re.search(r"\b(close|closing|closed|will close|relocat)\b", low) and _DATE_PHRASE.search(body))
        if focus == "phone":
            return bool(re.search(r"\b\d{3}-\d{3}-\d{4}\b", body))
        if focus == "link":
            return bool(re.search(r"https?://[^\s)]*(?:%s)" % "|".join(ents), body, re.I))
        return False

    for doc in index.docs:
        if doc.block.kind not in ("passage", "list_item") or doc.validity.status(target) != "applicable":
            continue
        body = store.quote(doc.occurrence, doc.block.span)
        if 4 <= len(body.split()) <= 200 and ok(body):
            return _result(store, [doc], body, "Published statement answering the request (%s)." % focus)
    return None


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
