"""Snapshot-first answering with selectable basic/research retrieval."""
from dataclasses import replace
import os
import re
try:
    from .evidence import EvidenceStore
    from .models import Answer
    from .query import interpret as query_request, tokens
    from .temporal import interpret as time_request, select_view, DATE
    from .retrieval import Index
    from .decisions import decide, refusal
    from .conflicts import enumerate_conflicts
    from .validation import validate
    from .extractive import extract
except ImportError:
    from evidence import EvidenceStore
    from models import Answer
    from query import interpret as query_request, tokens
    from temporal import interpret as time_request, select_view, DATE
    from retrieval import Index
    from decisions import decide, refusal
    from conflicts import enumerate_conflicts
    from validation import validate
    from extractive import extract


class KnowledgeSystem:
    def __init__(self, mode="basic"):
        if mode not in ("basic", "research"):
            raise ValueError("mode must be basic or research")
        self.mode = mode
        self.evidence = EvidenceStore()
        self.indexes = {}

    def ingest(self, snapshot):
        self.evidence.ingest(snapshot)
        if snapshot.snapshot_id not in self.indexes:
            self.indexes[snapshot.snapshot_id] = Index(self.evidence, snapshot.snapshot_id)

    def answer(self, question, as_of=None):
        return self.explain(question, as_of)[0]

    def explain(self, question, as_of=None):
        """Return an answer and an audit trace without mutating query state."""
        if not isinstance(question, str) or not question.strip():
            return refusal("Please supply a question.").answer, {"status": "ambiguous"}
        temporal = time_request(question, as_of)
        if temporal.error:
            return refusal(temporal.error, "ambiguous").answer, {"status": "ambiguous", "reason": temporal.error}
        request = query_request(question)
        if self.mode == "research":
            request = replace(request, terms=tuple(tokens(re.sub(DATE, "", request.question, flags=re.I), True)))
        cutoffs = temporal.endpoints or (temporal.cutoff,)
        results, views = [], []
        for cutoff in cutoffs:
            view = select_view(self.evidence, cutoff)
            views.append(view)
            if view.error:
                result = refusal(view.error)
            else:
                result = decide(self.evidence, self.indexes[view.snapshot_id], request, view, self.mode, temporal.event_date)
                if result.status == "insufficient":
                    # One bounded expansion, identical for both experiment arms.
                    result = decide(self.evidence, self.indexes[view.snapshot_id], request, view, self.mode,
                                    temporal.event_date, limit=160)
                if result.status == "insufficient":
                    result = extract(self.evidence, self.indexes[view.snapshot_id], request, view, self.mode) or result
            results.append(result)
        if len(results) == 2:
            if not all(r.answer.confident for r in results):
                answer = refusal("Both comparison endpoints need supported evidence.").answer
                status = "insufficient"
            elif not results[0].scope or results[0].scope != results[1].scope:
                answer = refusal("The endpoint facts do not have matching product and qualifier scopes.", "ambiguous").answer
                status = "ambiguous"
            else:
                answer = Answer("\n".join(f"Observed {v.observed_on}: {r.answer.text}" for v, r in zip(views, results)),
                                [s for r in results for s in r.answer.sources], True)
                status = "supported"
        else:
            answer, status = results[0].answer, results[0].status
        if answer.confident and temporal.event_date and views[0].observed_on < temporal.event_date:
            answer.text = (f"The snapshot observed on {views[0].observed_on} describes the following for "
                           f"{temporal.event_date}; later implementation is unconfirmed.\n" + answer.text)
        trace = {"mode": self.mode, "status": status, "time": vars(temporal),
                 "views": [vars(v) for v in views],
                 "decisions": [{"status": r.status, "reason": r.reason,
                                "selected": [{"url": d.occurrence.url, "snapshot_id": d.occurrence.snapshot_id,
                                              "start": d.block.span.start, "end": d.block.span.end,
                                              "warnings": list(d.block.warnings)} for d in r.selected],
                                "retrieved": [{"url": d.occurrence.url, "snapshot_id": d.occurrence.snapshot_id,
                                               "start": d.block.span.start, "end": d.block.span.end} for d in r.candidates]}
                               for r in results]}
        failure = validate(answer, self.evidence, {v.snapshot_id for v in views if v.snapshot_id})
        if failure:
            answer = refusal(failure).answer
            trace.update(status="validation_failed", validation_error=failure)
        return answer, trace

    def conflicts(self):
        return enumerate_conflicts(self.evidence, self.indexes)


def build(mode=None):
    return KnowledgeSystem(mode or os.environ.get("KNOWLEDGE_MODE", "basic"))
