from dataclasses import dataclass, field


@dataclass
class Source:
    url: str
    snapshot_id: str | None = None
    quote: str | None = None


@dataclass
class Answer:
    text: str
    sources: list[Source] = field(default_factory=list)
    confident: bool = False
    conflict_note: str | None = None


@dataclass
class Conflict:
    topic: str
    values: list[str]
    sources: list[Source]
    resolution: str | None = None
    reason: str | None = None


# Use the organizer's already-loaded boundary types when running in its harness.
# Its repeat checker handles its own Answer class differently from other
# structurally compatible objects. Standalone use keeps the local dataclasses.
import sys

if "contract" in sys.modules:
    from contract import Answer, Source, Conflict
