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
                if re.match(r"^\s*!\[.*\]\([^\n]*\)\s*$", body) or not tokens(body):
                    continue
                if re.match(r"^\s*\[.*\]\([^\n]*\)\s*$", body):
                    block = replace(block, kind="link")
                headers = cells(store.quote(occurrence, block.header)) if block.header else ()
                fact = re.fullmatch(r"(.{1,100}?)\s+(APY|APR|fee|rate)\s*:?\s*(\$?\d[\d,.]*(?:%)?)(.*)", body, re.I)
                if not headers and fact and ("%" in fact[3] or "$" in fact[3]):
                    headers = ("Product", fact[2].upper())
                    # Keep the complete numeric expression: suffixes may carry
                    # a range endpoint, tier boundary or essential condition.
                    # Treat it as an opaque value, not a scalar we can compute.
                    block = replace(block, kind="table_row", cells=(fact[1], (fact[3] + fact[4]).strip()), header=block.span)
                    suffix_metric = re.search(r"\b(APR|APY)\b", fact[4], re.I)
                    if fact[2].lower() == "rate" and suffix_metric and block.headings:
                        product = block.headings[-1]
                        headers = ("Card Type" if re.search(r"card|visa", product, re.I) else "Product", suffix_metric[1].upper())
                        block = replace(block, cells=(product, body))
                elif not headers and len(body) < 700 and block.headings:
                    # Product-local prose may put the metric after the range.
                    # Keep the entire statement, including purpose/conditions.
                    metric_fact = re.search(r"\d+(?:\.\d+)?%[^\n]{0,30}\b(APR|APY)\b", body, re.I)
                    product = block.headings[-1]
                    if metric_fact and re.search(r"\b(card|visa|savings|certificate|loan)\b", product, re.I) and not product.endswith("?"):
                        headers = ("Card Type" if re.search(r"card|visa", product, re.I) else "Product", metric_fact[1].upper())
                        block = replace(block, kind="table_row", cells=(product, body), header=block.span)
                spans = table_context(store, occurrence, block) if block.header and block.header != block.span else ()
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
        # Evidence-derived reader indexes, built once per snapshot (not answers).
        self.reader_groups = []
        for positions in self.by_section.values():
            docs = [self.docs[i] for i in positions if self.docs[i].block.kind in ("passage", "list_item")]
            if docs:
                self.reader_groups.append((docs, "\n".join(store.quote(d.occurrence, d.block.span) for d in docs)))
        self.labeled_links, self.count_statements = [], []
        for doc in self.docs:
            raw = store.quote(doc.occurrence, doc.block.span)
            for match in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", raw):
                self.labeled_links.append((doc, frozenset(tokens(match[1], True)), match[0]))
            if re.search(r"\b\d+\s+(?:[\w-]+\s+){0,2}(?:branches|employees|members)\b", raw, re.I):
                self.count_statements.append((doc, frozenset(tokens(raw, True)), raw))

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
