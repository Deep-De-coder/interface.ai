"""Small inspectable query representation, with no site-specific answers."""
from dataclasses import dataclass
from decimal import Decimal
import re

STOP = set("a an the of on in for to and or is are was were what which how can you me tell give please at as it its with do does your our about from now latest current published applies apply list all more than least much has have had these those this that their my i us by get when been will be per describe explain".split())
SYNONYMS = {"yield": "apy", "dividends": "dividend", "automobile": "auto", "vehicle": "auto", "car": "auto", "charges": "fee", "charge": "fee", "cost": "fee", "fees": "fee", "accounts": "account", "loans": "loan", "certificates": "certificate", "methods": "method", "withdrawals": "withdrawal", "rates": "rate", "members": "member"}
SYNONYMS.update({"aprs": "apr", "apys": "apy", "cards": "card"})


def tokens(text, expand=False):
    text = re.sub(r"https?://\S+", " ", text.lower())
    text = text.replace("annual percentage yield", "apy").replace("annual percentage rate", "apr")
    text = re.sub(r"\bhome loans?\b", "mortgage", text)
    words = re.findall(r"[a-z]+|\d+(?:\.\d+)?", text)
    words = [w for w in words if w not in STOP and w != "s"]
    return [SYNONYMS.get(w, w) for w in words] if expand else words


@dataclass(frozen=True)
class Request:
    question: str
    intent: str
    metric: str | None
    amount: Decimal | None
    term_months: int | None
    model_year: int | None
    terms: tuple[str, ...]


def interpret(question):
    q = question.lower().replace("annual percentage yield", "apy").replace("annual percentage rate", "apr")
    q = re.sub(r"\bshare certificates?\b", "certificate", q)
    numbers = {"six": "6", "twelve": "12", "seventeen": "17", "thirty": "30", "sixty": "60"}
    for word, value in numbers.items():
        q = re.sub(r"\b" + word + r"(?=[ -]+(?:month|year))", value, q)
    metric = next((m for m in ("apy", "apr", "fee", "rate") if re.search(r"\b" + m + r"s?\b", q)), None)
    if metric is None and re.search(r"\b(cost|charge)\b", q):
        metric = "fee"
    amount = re.search(r"\$([\d,]+(?:\.\d+)?)", q)
    term = re.search(r"\b(\d+)[ -]*(month|year)s?\b(?![ -]*(?:old|model))", q)
    model = re.search(r"\b(20\d{2})[ -]*(?:model|vehicle)", q)
    intent = "list" if re.search(r"\b(list|all|which|what .*methods|what .*options)\b", q) else "value" if metric else "description"
    if re.search(r"\bwhat (?:credit )?cards\b", q):
        intent = "list"
    if metric is None and re.search(r"\b(how|where|can i|can we)\b", q):
        intent = "procedure"
    return Request(q, intent, metric, Decimal(amount[1].replace(",", "")) if amount else None,
                   int(term[1]) * (12 if term[2] == "year" else 1) if term else None,
                   int(model[1]) if model else None, tuple(tokens(q, True)))
