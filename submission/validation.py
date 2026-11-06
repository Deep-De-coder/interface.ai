"""Check source identity, exact excerpts and numerical provenance before output."""
import re


def validate(answer, store, eligible_ids):
    if not answer.confident:
        return None
    if not answer.sources:
        return "A confident answer requires supporting sources."
    allowed_numbers = set()
    for sid in eligible_ids:
        for date in [taken for taken, ident in store.snapshots() if ident == sid]:
            allowed_numbers.update(re.findall(r"\d+(?:\.\d+)?", date))
    for source in answer.sources:
        if source.snapshot_id not in eligible_ids:
            return "A citation is outside the selected evidence view."
        occurrences = [p for p in store.occurrences(source.snapshot_id) if p.url == source.url]
        if len(occurrences) != 1 or not source.quote:
            return "A citation has no identifiable supporting excerpt."
        raw = store.raw(occurrences[0])
        for excerpt in source.quote.split("\n[…]\n"):
            if not excerpt or excerpt not in raw:
                return "A citation excerpt is not present in its source."
        allowed_numbers.update(re.findall(r"\d+(?:\.\d+)?", source.quote.replace(",", "")))
    # Date-boundary notes are generated from request metadata, checked by the
    # temporal selector; do not treat them as source-derived financial values.
    text = re.sub(r"\d{4}-\d{2}-\d{2}", "", answer.text)
    if not set(re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))) <= allowed_numbers:
        return "A numerical claim lacks support in the cited excerpts."
    return None
