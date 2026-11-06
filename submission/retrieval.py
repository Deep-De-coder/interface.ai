"""Two interchangeable retrievers over the same immutable snapshot evidence."""
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
import math
import re

try:
    from .query import tokens
    from .parsing import cells
    from .temporal import applicability
except ImportError:
    from query import tokens
    from parsing import cells
    from temporal import applicability


@dataclass(frozen=True)
class Document:
    occurrence: object
    block: object
    text: str
    identity: str
    headers: tuple[str, ...]
    context_spans: tuple
    section: tuple[str, ...]
    validity: object

    @property
    def key(self):
        return (self.occurrence.url, self.block.span.start)


def table_context(store, occurrence, block):
    """Do not inherit a previous table's dates or the next product's label."""
    before, after = [], []
    for span in block.context:
        text = store.quote(occurrence, span).strip()
        if span.end <= block.header.start:
            if len(text) < 100 and not re.search(r"[.%]|https?://|\|", text):
                before.append(span)
        elif span.start > block.span.end:
            if re.match(r"\[.*\]\(|!\[", text):
                break
            if len(text) < 100 and not re.search(r"[.:;]|\b(effective|fees?|members?|only|expires?|valid|rates?)\b", text, re.I):
                break
            after.append(span)
    return tuple(before[-2:] + after)


class Index:
    def __init__(self, store, snapshot_id):
        self.docs = []
        self.postings = defaultdict(list)
        self.lengths = []
        self.identities = []
        self.by_section = defaultdict(list)
        for occurrence in store.occurrences(snapshot_id):
            heading_spans = []
            for block in store.blocks(occurrence):
                if block.kind == "heading":
                    heading_spans = [(path, span) for path, span in heading_spans if len(path) < len(block.headings)]
                    heading_spans.append((block.headings, block.span))
                if block.kind not in ("table_row", "passage", "list_item"):
                    continue
                body = store.quote(occurrence, block.span)
                if re.match(r"^\s*!?\[.*\]\([^\n]*\)\s*$", body) or not tokens(body):
                    continue
                headers = cells(store.quote(occurrence, block.header)) if block.header else ()
                fact = re.fullmatch(r"(.{1,100}?)\s+(APY|APR|fee|rate)\s*:?\s*(\$?\d[\d,.]*(?:%)?)(.*)", body, re.I)
                if not headers and fact and ("%" in fact[3] or "$" in fact[3]):
                    headers = ("Product", fact[2].upper())
                    block = replace(block, kind="table_row", cells=(fact[1], fact[3]), header=block.span)
                spans = table_context(store, occurrence, block) if block.header else ()
                context = "\n".join(store.quote(occurrence, s) for s in spans)
                label = " ".join(store.quote(occurrence, s) for s in spans if s.end <= block.header.start) if block.header else ""
                identity = " ".join((occurrence.title, *block.headings, label))
                if block.cells:
                    identity += " " + block.cells[0]
                text = "\n".join(x for x in (" | ".join(headers), body, context) if x)
                doc = Document(occurrence, block, text, identity, headers, spans,
                               block.headings, applicability(text))
                doc = Document(occurrence, block, text, identity, headers,
                               tuple(dict.fromkeys([s for _, s in heading_spans] + list(spans))),
                               block.headings, doc.validity)
                i = len(self.docs)
                self.docs.append(doc)
                counts = Counter(tokens(text + " " + identity, True))
                self.identities.append(frozenset(tokens(identity, True)))
                self.lengths.append(sum(counts.values()))
                self.by_section[(occurrence.url, block.headings)].append(i)
                for term, count in counts.items():
                    self.postings[term].append((i, count))
        self.average = sum(self.lengths) / max(1, len(self.lengths))

    def search(self, request, mode, target, limit=40):
        scores = defaultdict(float)
        terms = set(request.terms)
        n = len(self.docs)
        for term in terms:
            posting = self.postings.get(term, ())
            idf = math.log(1 + (n - len(posting) + .5) / (len(posting) + .5))
            for i, frequency in posting:
                if mode == "basic":
                    scores[i] += 1
                else:
                    length_ratio = self.lengths[i] / max(1, self.average)
                    scores[i] += idf * frequency * 2.2 / (frequency + 1.2 * (.25 + .75 * length_ratio))
                    if term in self.identities[i]:
                        scores[i] += .35 * idf
        if mode == "research":
            for i in scores:
                valid = self.docs[i].validity
                # An explicit applicable date is a small relevance signal, never
                # authority or permission to use a source outside this snapshot.
                if valid.start and valid.status(target) == "applicable":
                    scores[i] *= 1.05
        ranked = sorted(scores, key=lambda i: (-scores[i], self.docs[i].key))[:limit]
        return [(self.docs[i], scores[i]) for i in ranked]

    def section_items(self, doc):
        return [self.docs[i] for i in self.by_section[(doc.occurrence.url, doc.section)]
                if self.docs[i].block.kind == "list_item"]
