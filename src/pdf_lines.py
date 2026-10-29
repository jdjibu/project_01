"""Shared helpers: turn `pdftotext -layout` output into (label, numbers) rows."""
import re
import subprocess
from pathlib import Path

NUM = re.compile(r"(?<![\w.])\(?\d[\d,]*(?:\.\d+)?\)?%?(?![\w])|(?<=\s)-(?=\s|$)")
LEADERS = re.compile(r"[\.…·‥]{2,}|…+")


def pdf_text(path: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          capture_output=True, text=True, check=True).stdout


def to_number(tok: str):
    """'(1,234)' -> -1234.0, '-' -> 0.0, '12.3%' -> None (ratios are dropped)."""
    if tok.endswith("%"):
        return None
    if tok == "-":
        return 0.0
    neg = tok.startswith("(") and tok.endswith(")")
    v = float(tok.strip("()").replace(",", ""))
    return -v if neg else v


def clean_label(s: str) -> str:
    s = re.sub(r"^\s*\(\d\)\s*", "", s)          # '(1) External' -> 'External'
    s = LEADERS.sub(" ", s)
    s = re.sub(r"[^\w\s\(\)/,&'’-]", " ", s)     # stray glyphs from the PDF
    return re.sub(r"\s+", " ", s).strip(" .,")


def rows(text: str, int_only: bool = False):
    """Yield (label, [numbers]) per line. Label-only lines are yielded with [] and also
    carry forward to a following numbers-only line (wrapped labels)."""
    pending = ""
    for raw in text.splitlines():
        line = re.sub(r"^\s*\(\d\)\s*", " ", raw)
        toks = list(NUM.finditer(line))
        label = clean_label(line[: toks[0].start()] if toks else line)
        if int_only:  # statement values are whole JPY millions; decimals are ratio columns
            toks = [t for t in toks if "." not in t.group()]
        nums = [to_number(t.group()) for t in toks]
        nums = [n for n in nums if n is not None]
        if not toks:
            pending = label
            if label:
                yield label, []  # header line (e.g. 'CURRENT ASSETS'), used for context
            continue
        if not label:
            label = pending
        pending = ""
        yield label, nums


def section(text: str, start: str, end: str) -> str:
    m = re.search(start, text, flags=re.I | re.M)
    if not m:
        return ""
    rest = text[m.end():]
    e = re.search(end, rest, flags=re.I | re.M)
    return rest[: e.start()] if e else rest
