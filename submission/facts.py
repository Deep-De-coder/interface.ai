"""Conservative shared identity for comparable source facts.

Unknown identity is scoped to its source, never treated as a wildcard. This is
not an alias resolver: editorial changes may remain separate until evidenced.
"""
import re


def canonical(value):
    value = value.lower().replace(",", "").replace("–", "-").replace("—", "-")
    value = re.sub(r"(%)(?:\d+|\[\d+\])", r"\1", value)
    return re.sub(r"\s+", " ", value).strip()


def _product_heading(text):
    text = canonical(text).strip(" *#")
    words = set(re.findall(r"[a-z]+", text))
    generic = {"personal", "business", "current", "our", "rates", "rate", "savings",
               "saving", "account", "accounts", "loan", "loans", "credit", "cards",
               "card", "products", "product", "services", "apy", "apr", "fees", "fee"}
    return text if words - generic and words & {"savings", "saving", "account", "loan", "card", "visa", "certificate", "mortgage", "checking"} else ""


def fact_scope(doc, metric):
    """Return a hashable entity/qualifier key shared by answering and auditing."""
    pairs = [(canonical(h), canonical(c)) for h, c in zip(doc.headers, doc.block.cells)]
    named = tuple((h, c) for h, c in pairs
                  if re.fullmatch(r"(?:account|card) type|certificate|product", h))
    heading = next((_product_heading(h) for h in reversed(doc.section) if _product_heading(h)), "")
    title = _product_heading(doc.occurrence.title)
    if named:
        entity = ("named", repr(named))
    elif heading and (not title or title == heading):
        entity = ("heading", heading)
    else:
        entity = ("source", doc.occurrence.url, heading or canonical(doc.occurrence.title))
    # Qualifiers explicitly present in row/headings take precedence over a
    # generic page title. Unknown audience/channel is not personal/general.
    context = canonical(" ".join((*doc.section, " ".join(c for _, c in pairs))))
    audience = tuple(x for x in ("business", "personal") if re.search(r"\b" + x + r"\b", context)) or ("unspecified",)
    channel = tuple(x for x in ("lobby", "drive-up", "online") if x in context) or ("unspecified",)
    purpose = tuple(x for x in ("purchase", "balance transfer", "cash advance", "refinance") if x in context) or ("unspecified",)
    qualifiers = tuple((h, c) for h, c in pairs
                       if not re.search(r"apy|apr|yield|rate|fee|payment|points", h))
    return entity, audience, channel, purpose, metric, qualifiers
