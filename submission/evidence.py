"""Immutable observations with content-addressed parsing and atomic ingestion."""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
from urllib.parse import urlsplit

try:
    from .parsing import Block, PARSER_VERSION, parse
except ImportError:
    from parsing import Block, PARSER_VERSION, parse


@dataclass(frozen=True)
class Occurrence:
    snapshot_id: str
    taken_on: str
    url: str
    title: str
    fetched_at: str
    content_hash: str


class EvidenceStore:
    def __init__(self):
        self._snapshots = {}
        self._raw = {}
        self._parsed = {}
        self._fingerprints = {}

    def ingest(self, snapshot):
        sid, taken = snapshot.snapshot_id, snapshot.taken_on
        if not isinstance(sid, str) or not sid:
            raise ValueError("snapshot_id must be a nonempty string")
        if date.fromisoformat(taken).isoformat() != taken:
            raise ValueError("taken_on must be YYYY-MM-DD")
        occurrences, raw_new, parsed_new = [], {}, {}
        seen = set()
        for page in snapshot.pages:
            if not all(isinstance(v, str) for v in (page.url, page.title, page.markdown, page.fetched_at)):
                raise ValueError("Page fields must be strings")
            url = urlsplit(page.url)
            if url.scheme not in ("http", "https") or not url.netloc:
                raise ValueError("Page URL must be absolute HTTP(S)")
            if page.url in seen:
                raise ValueError("Duplicate URL within snapshot")
            seen.add(page.url)
            datetime.fromisoformat(page.fetched_at.replace("Z", "+00:00"))
            digest = sha256(page.markdown.encode("utf-8")).hexdigest()
            occurrences.append(Occurrence(sid, taken, page.url, page.title, page.fetched_at, digest))
            if digest not in self._raw and digest not in raw_new:
                raw_new[digest] = page.markdown
                parsed_new[(PARSER_VERSION, digest)] = parse(page.markdown)
        occurrences.sort(key=lambda p: p.url)
        signature = sha256(json.dumps([taken, [vars(p) for p in occurrences]], sort_keys=True).encode()).hexdigest()
        if sid in self._fingerprints:
            if signature != self._fingerprints[sid]:
                raise ValueError("Existing snapshot ID cannot be overwritten")
            return
        if self._snapshots and taken < max(v[0] for v in self._snapshots.values()):
            raise ValueError("Snapshots must be ingested chronologically")
        # Publish only after every page passes validation and parsing.
        self._raw.update(raw_new)
        self._parsed.update(parsed_new)
        self._snapshots[sid] = (taken, tuple(occurrences))
        self._fingerprints[sid] = signature

    def occurrences(self, snapshot_id):
        return self._snapshots[snapshot_id][1]

    def snapshots(self):
        """Public immutable metadata view; no callers need private dictionaries."""
        return tuple(sorted((taken, sid) for sid, (taken, _) in self._snapshots.items()))

    def raw(self, occurrence):
        return self._raw[occurrence.content_hash]

    def blocks(self, occurrence) -> tuple[Block, ...]:
        return self._parsed[(PARSER_VERSION, occurrence.content_hash)]

    def quote(self, occurrence, span):
        raw = self.raw(occurrence)
        if not 0 <= span.start <= span.end <= len(raw):
            raise ValueError("Invalid source span")
        return raw[span.start:span.end]

    def stats(self):
        return {"snapshots": len(self._snapshots),
                "occurrences": sum(len(v[1]) for v in self._snapshots.values()),
                "unique_contents": len(self._raw),
                "unique_blocks": sum(len(v) for v in self._parsed.values()),
                "parser_version": PARSER_VERSION}
