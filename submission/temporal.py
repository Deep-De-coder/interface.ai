"""Hard snapshot boundaries and conservative, evidence-backed date constraints."""
from dataclasses import dataclass
from datetime import date, datetime
import re
import calendar

DATE = r"(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})"


def parse_date(value):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%B %d %Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError("Use an explicit valid calendar date")


@dataclass(frozen=True)
class TimeRequest:
    cutoff: str | None = None
    event_date: str | None = None
    endpoints: tuple[str, ...] = ()
    error: str | None = None


def interpret(question, as_of=None):
    try:
        cutoff = parse_date(as_of) if as_of is not None else None
        dated = [(m, parse_date(m.group())) for m in re.finditer(DATE, question, re.I)]
        comparing = bool(re.search(r"\b(chang\w*|compar\w*|difference|between)\b", question, re.I)) and (len(dated) >= 1 or bool(re.search(r"\b(over time|history|since)\b", question, re.I)))
        month = re.search(r"as of\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", question, re.I)
        if month:
            month_number = datetime.strptime(month[1], "%B").month
            year = int(month[2])
            if cutoff and cutoff[:7] != f"{year:04d}-{month_number:02d}":
                return TimeRequest(error="The textual month and API cutoff disagree.")
            cutoff = cutoff or date(year, month_number, calendar.monthrange(year, month_number)[1]).isoformat()
        if comparing and len(dated) == 2:
            endpoints = tuple(d for _, d in dated)
            if endpoints[0] > endpoints[1]:
                return TimeRequest(error="Comparison dates must be in chronological order.")
            if cutoff and endpoints[-1] > cutoff:
                return TimeRequest(error="The comparison extends beyond the requested knowledge cutoff.")
            return TimeRequest(cutoff, endpoints=endpoints)
        explicit = re.search(r"(?:as\s+of|website\s+stood\s+on|back\s+on)\s+(" + DATE + ")", question, re.I)
        if explicit:
            described = parse_date(explicit[1])
            if cutoff and cutoff != described:
                return TimeRequest(error="The API cutoff and the question's as-of date disagree.")
            cutoff = described
        event = None
        if dated and not explicit:
            if len(dated) > 1:
                return TimeRequest(error="The relationship between the requested dates is unclear.")
            event = dated[0][1]
            # A past-tense state request selects a historical observation; an
            # event/scheduled-date request describes content inside the view.
            if as_of is None and re.search(r"\b(was|were|historical)\b", question, re.I) and not re.search(r"\b(event|scheduled|announc\w*)\b", question, re.I):
                cutoff, event = event, None
        if comparing and not (len(dated) == 2):
            return TimeRequest(error="Please specify both comparison dates explicitly.")
        if not dated and not month and re.search(r"\b(yesterday|last (?:year|month|week)|previously|as of)\b", question, re.I):
            return TimeRequest(error="Please specify an explicit calendar date.")
        if cutoff is None and not dated and re.search(r"\b(was|were|historical)\b", question, re.I) and re.search(r"(?<![$\d])\b20\d{2}\b", question) and not re.search(r"model[ -]year", question, re.I):
            return TimeRequest(error="Please specify the full historical calendar date.")
        return TimeRequest(cutoff, event)
    except (ValueError, TypeError):
        return TimeRequest(error="The requested date is invalid or unsupported.")


@dataclass(frozen=True)
class View:
    snapshot_id: str | None
    observed_on: str | None
    requested_on: str | None
    note: str = ""
    error: str | None = None


def select_view(store, cutoff=None):
    snaps = store.snapshots()
    if not snaps:
        return View(None, None, cutoff, error="No snapshots have been ingested.")
    target = cutoff or snaps[-1][0]
    eligible = [(taken, sid) for taken, sid in snaps if taken <= target]
    if not eligible:
        return View(None, None, target, error="No observation exists on or before that date.")
    taken = eligible[-1][0]
    matches = [sid for d, sid in eligible if d == taken]
    if len(matches) != 1:
        return View(None, None, target, error="Multiple snapshots have that date; their ordering is unknown.")
    note = ""
    if target > snaps[-1][0]:
        note = f"Last observed on {taken}; later changes cannot be confirmed."
    elif target != taken:
        note = f"Using the observation from {taken}; no snapshot was captured on {target}."
    return View(matches[0], taken, target, note)


@dataclass(frozen=True)
class Applicability:
    start: str | None = None
    end: str | None = None
    uncertain: bool = False

    def status(self, target):
        if self.uncertain:
            return "uncertain"
        if self.start and target < self.start:
            return "scheduled"
        if self.end and target > self.end:
            return "expired"
        return "applicable"


def applicability(text):
    starts, ends = set(), set()
    patterns = ((starts, r"(?:effective(?:\s+as\s+of|\s+from|\s+on)?|starts?|begins?)\s+(" + DATE + ")"),
                (ends, r"(?:expires?(?:\s+on)?|valid\s+through|ends?(?:\s+on)?|ended(?:\s+on)?)\s+(" + DATE + ")"))
    try:
        for values, pattern in patterns:
            for m in re.finditer(pattern, text, re.I):
                values.add(parse_date(m[1]))
    except ValueError:
        return Applicability(uncertain=True)
    start = min(starts) if starts else None
    end = min(ends) if ends else None
    return Applicability(start, end, len(starts) > 1 or len(ends) > 1 or bool(start and end and start > end))
