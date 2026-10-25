#!/usr/bin/env python3
"""Build the Persian booklet: src/*.html -> book.html -> PDF (two passes for TOC page numbers)."""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT_HTML = ROOT / "book.html"
OUT_PDF = ROOT.parent / "CSL_Jozveh_Persian.pdf"

sys.path.insert(0, str(ROOT))
import figs  # noqa: E402

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(n):
    return str(n).translate(FA_DIGITS)


# ---------------------------------------------------------------- asm tables
ASM_HEAD = {
    "ad": "Address", "mc": "Machine Code", "lb": "Label", "op": "Instr.",
    "ar": "Operands", "cm": "توضیح",
}


LTR_RUN = re.compile(r"[A-Za-z0-9\[\u2212\-][^\u0600-\u06FF<>\u21D0\u21D2]*[A-Za-z0-9\]]|[A-Za-z0-9]")


def wrap_ltr(v):
    """Wrap Latin/number runs of a Persian comment in LTR isolates, keeping parentheses balanced."""
    out, pos = [], 0
    for mm in LTR_RUN.finditer(v):
        a, b = mm.start(), mm.end()
        if a < pos:
            continue
        run = v[a:b]
        if run.count("(") > run.count(")") and b < len(v) and v[b] == ")":
            b += 1
        run = v[a:b]
        if run.count("(") != run.count(")"):
            continue
        out.append(v[pos:a] + f'<span class="m">{run}</span>')
        pos = b
    out.append(v[pos:])
    return "".join(out)


def asm_block(m):
    attrs = m.group(1) or ""
    body = m.group(2)
    cm = re.search(r'cols="([^"]+)"', attrs)
    cols = (cm.group(1) if cm else "ad,mc,lb,op,ar,cm").split(",")
    rows = []
    for raw in body.strip("\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line == "--":
            rows.append(f'<tr class="sep"><td colspan="{len(cols)}"></td></tr>')
            continue
        cls = ""
        if line.startswith("!"):
            cls = ' class="dir"'
            line = line[1:]
        cells = [c.strip() for c in line.split("|")]
        cells += [""] * (len(cols) - len(cells))
        tds = []
        for c, v in zip(cols, cells):
            if c == "cm" and "<span" not in v and re.search(r"[\u0600-\u06FF]", v):
                v = wrap_ltr(v)
            if c != "cm":
                v = v.replace("<", "&lt;") if "<span" not in v and "<b" not in v else v
            tds.append(f'<td class="{c}">{v}</td>')
        rows.append(f"<tr{cls}>" + "".join(tds) + "</tr>")
    head = "".join(f'<th class="{c}">{ASM_HEAD[c]}</th>' for c in cols)
    return f'<table class="asm"><thead><tr>{head}</tr></thead><tbody>' + "".join(rows) + "</tbody></table>"


def fig_sub(m):
    expr = m.group(1).strip()
    if "(" not in expr:
        expr += "()"
    return eval(expr, vars(figs))


def assemble(toc_pages=None):
    parts = sorted(SRC.glob("*.html"))
    body = "\n".join(p.read_text(encoding="utf-8") for p in parts)
    body = re.sub(r"<asm([^>]*)>(.*?)</asm>", asm_block, body, flags=re.S)
    body = re.sub(r"\{\{fig:(.*?)\}\}", fig_sub, body, flags=re.S)

    # number chapters / sections / subsections in document order and collect the TOC
    toc = []
    state = {"ch": 0, "app": 0, "sec": 0, "sub": 0, "prefix": ""}
    pat = re.compile(
        r'<h1 class="chapter"(?: data-label="([^"]*)")?>(.*?)</h1>|<h2>(.*?)</h2>|<h3>(.*?)</h3>', re.S
    )

    def number(m):
        if m.group(2) is not None:  # chapter / appendix
            title = m.group(2)
            state["sec"] = state["sub"] = 0
            if m.group(1):  # appendix with explicit label, e.g. "پیوست الف"
                state["app"] += 1
                hid = f"app{state['app']}"
                label = m.group(1)
                state["prefix"] = label.split()[-1]
            else:
                state["ch"] += 1
                hid = f"ch{state['ch']}"
                label = f"فصل {fa(state['ch'])}"
                state["prefix"] = fa(state["ch"])
            state["hid"] = hid
            toc.append((1, hid, f"{label}: {re.sub('<[^>]+>', '', title)}"))
            return f'<h1 class="chapter" id="{hid}"><span class="num">{label}</span>{title}</h1>'
        if m.group(3) is not None:  # section
            state["sec"] += 1
            state["sub"] = 0
            title = m.group(3)
            hid = f"{state['hid']}-s{state['sec']}"
            num = f"{state['prefix']}-{fa(state['sec'])}"
            toc.append((2, hid, f"{num}  {re.sub('<[^>]+>', '', title)}"))
            return f'<h2 id="{hid}"><span class="sn">{num}</span>{title}</h2>'
        state["sub"] += 1
        num = f"{state['prefix']}-{fa(state['sec'])}-{fa(state['sub'])}"
        return f'<h3><span class="sn">{num}</span>{m.group(4)}</h3>'

    body = pat.sub(number, body)

    items = []
    for lvl, hid, title in toc:
        pg = fa(toc_pages.get(hid, "")) if toc_pages else "۰۰"
        items.append(
            f'<li class="l{lvl}"><a href="#{hid}">{html.escape(title)}</a>'
            f'<span class="dots"></span><a class="pg" href="#{hid}">{pg}</a></li>'
        )
    toc_html = '<section class="toc"><h1>فهرست مطالب</h1><ul>' + "".join(items) + "</ul></section>"
    body = body.replace("<!--TOC-->", toc_html)

    doc = (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        "<title>جزوه ساختار و زبان کامپیوتر</title>"
        '<link rel="stylesheet" href="style.css"></head><body>' + body + "</body></html>"
    )
    OUT_HTML.write_text(doc, encoding="utf-8")
    return [t[1] for t in toc]


def render(pdf_path):
    subprocess.run(["node", str(ROOT / "render.js"), str(OUT_HTML), str(pdf_path)], check=True)


def page_numbers(pdf_path, ids):
    from pypdf import PdfReader

    r = PdfReader(str(pdf_path))
    nd = r.named_destinations
    res = {}
    for i in ids:
        d = nd.get(i) or nd.get("/" + i)
        if d is not None:
            res[i] = r.get_destination_page_number(d) + 1
    return res


if __name__ == "__main__":
    ids = assemble()
    tmp = ROOT / "_pass1.pdf"
    render(tmp)
    pages = page_numbers(tmp, ids)
    missing = [i for i in ids if i not in pages]
    if missing:
        print("WARNING: no page for", missing[:10])
    assemble(pages)
    render(OUT_PDF)
    tmp.unlink(missing_ok=True)
    print("built", OUT_PDF)
