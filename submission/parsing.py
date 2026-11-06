"""Conservative Markdown evidence parsing. No factual values are inferred.

Offsets always refer to the unmodified input. Table context is a candidate
association, not an assertion that every nearby condition applies to every row.
"""
from dataclasses import dataclass
import re

PARSER_VERSION = "2"


@dataclass(frozen=True)
class Span:
    start: int
    end: int


@dataclass(frozen=True)
class Block:
    kind: str
    span: Span
    headings: tuple[str, ...] = ()
    cells: tuple[str, ...] = ()
    header: Span | None = None
    context: tuple[Span, ...] = ()
    warnings: tuple[str, ...] = ()


def cells(text: str) -> tuple[str, ...]:
    # Preserve escaped pipes inside cells. Complex code-span tables are flagged.
    text = text.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith(r"\|"):
        text = text[:-1]
    return tuple(x.strip() for x in re.split(r"(?<!\\)\|", text))


def parse(raw: str) -> tuple[Block, ...]:
    # Treat literal escaped line breaks as virtual boundaries, without rewriting
    # the raw source or losing quote offsets. Flag this heuristic explicitly.
    lines = []
    pos = 0
    escaped = False
    for m in re.finditer(r"\r\n|\n|\\+r\\+n|\\+n", raw):
        lines.append((Span(pos, m.start()), raw[pos:m.start()]))
        escaped |= m.group().startswith("\\")
        pos = m.end()
    lines.append((Span(pos, len(raw)), raw[pos:]))
    blocks = []
    headings = []
    i = 0
    base_warning = ("escaped_newlines_interpreted",) if escaped else ()
    while i < len(lines):
        span, text = lines[i]
        if not text.strip():
            i += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", text)
        if heading:
            depth = len(heading[1])
            headings = [(d, t) for d, t in headings if d < depth]
            headings.append((depth, heading[2]))
            blocks.append(Block("heading", span, tuple(t for _, t in headings), warnings=base_warning))
            i += 1
            continue
        path = tuple(t for _, t in headings)
        if "|" in text and i + 1 < len(lines):
            separators = cells(lines[i + 1][1])
            if separators and all(re.fullmatch(r":?-{3,}:?", c) for c in separators):
                header = span
                widths = len(cells(text))
                table_warning = base_warning + (("header_width_mismatch",) if widths != len(separators) else ())
                blocks.append(Block("table_header", header, path, cells(text), warnings=table_warning))
                j = i + 2
                while j < len(lines) and "|" in lines[j][1] and lines[j][1].strip():
                    if j + 1 < len(lines) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells(lines[j + 1][1])):
                        break
                    j += 1
                # Neighboring context is retained conservatively and explicitly.
                before = [s for s, t in lines[max(0, i - 6):i] if t.strip()]
                after = []
                for s, t in lines[j:j + 16]:
                    if "|" in t or re.match(r"^#{1,6}\s", t):
                        break
                    if t.strip():
                        after.append(s)
                context = tuple(before + after)
                for row_span, row in lines[i + 2:j]:
                    row_cells = cells(row)
                    warnings = table_warning
                    if len(row_cells) != widths:
                        warnings += ("row_width_mismatch",)
                    if "`" in row:
                        warnings += ("code_span_table_requires_review",)
                    blocks.append(Block("table_row", row_span, path, row_cells, header, context, warnings))
                i = j
                continue
        kind = "list_item" if re.match(r"^\s*(?:[-*+] |\d+[.)] )", text) else "passage"
        warnings = base_warning + (("unparsed_pipe_structure",) if "|" in text else ())
        # A source line is an exact, auditable passage; section assembly comes later.
        blocks.append(Block(kind, span, path, warnings=warnings))
        i += 1
    return tuple(blocks)
