#!/usr/bin/env python3
"""Build the problem-solving patterns sheet (content.html + verified programs) -> CSL_Patterns.pdf.

Every program printed in the sheet comes from verify/programs.py and is executed on the machine
model first; the build stops if any of them fails.
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "verify"))

from asm import Sim  # noqa: E402
from machines import M1398, M1399, M1400, M1401, M1402  # noqa: E402
from programs import PROGRAMS, run_all  # noqa: E402

OUT_HTML = ROOT / "patterns.html"
OUT_PDF = ROOT.parent / "CSL_Patterns.pdf"
RENDER = ROOT.parent / "jozveh" / "render.js"
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(n):
    return str(n).translate(FA)


# ------------------------------------------------------------------ code blocks
def hl(line):
    line = html.escape(line)
    code, sep, com = line.partition(";")
    code = re.sub(r"^([A-Za-z_]\w*:)", r'<span class="lb">\1</span>', code)
    return code + (f'<span class="cm">;{com}</span>' if sep else "")


def code(pid):
    m, src = PROGRAMS[pid]
    body = "\n".join(hl(l) for l in src.splitlines())
    return f'<pre class="code" data-m="{m.name}">{body}</pre>'


# ------------------------------------------------------------------ IBM 360 listings
import ibm360  # noqa: E402
import programs360  # noqa: E402


def c360(pid):
    """Listing (address, machine code, source) of a verified IBM 360 program."""
    a = ibm360.assemble(programs360.P360[pid][1])
    out = []
    for r in a.rows:
        if r["kind"] == "comment":
            continue
        loc = "%04X" % r["loc"] if r["kind"] in ("ins", "dc", "ds") else "    "
        obj = r.get("obj", b"").hex().upper()
        if r["kind"] == "ins":
            obj = " ".join(obj[i:i + 4] for i in range(0, len(obj), 4))
        if len(obj) > 9:
            obj = obj[:8] + "…"
        lab = r.get("label") or ""
        src = f'{lab:<7} {r.get("mn") or "":<5} {r.get("ops") or ""}'.rstrip()
        if len(src) > 30:
            src = src[:29] + "…"
        line = html.escape(f"{loc} {obj:<9} ") + (f'<span class="lb">{html.escape(lab)}</span>' + html.escape(src[len(lab):]) if lab else html.escape(src))
        out.append(line)
    res = programs360.RESULTS360.get(pid, "")
    return f'<pre class="code" data-m="IBM 360">' + "\n".join(out) + "</pre>" + (f'<p class="sm">نتیجه (شبیه‌ساز): {res}</p>' if res else "")


# ------------------------------------------------------------------ Q4 listings
FIELDS = {
    "1402": {"I": [3, 24, 3, 24], "II": [3, 24, 3]},
    "1401": {"I": [4, 1, 21, 2, 21], "II": [4, 1, 21, 2]},
    "1400": {"I": [3, 16, 1, 16], "II": [3, 16, 1], "III": [3, 16, 1, 16, 16]},
    "1398": {},
}


def split(bits, widths):
    out, k = [], 0
    for w in widths:
        out.append(bits[k:k + w])
        k += w
    return out


def fmt_fields(m, mnem, ops, bits):
    if mnem == "dw":
        w = m.unit * m.word_units
        parts = split(bits, [w] * (len(bits) // w))
        if m.unit == 4:
            return " ".join("?" * (w // 4) if "?" in p else "%0*X" % (w // 4, int(p, 2)) for p in parts[:6]) + (" …" if len(parts) > 6 else "")
        return " ".join(p if "?" not in p else "?" * w for p in parts[:3]) + (" …" if len(parts) > 3 else "")
    name = m.name
    if name == "1398":
        n0 = bits[:4]
        widths = [4, 4, 32] if n0 == "0000" else [8, 4, 4, 32] if n0 == "1111" else [4, 4, 4]
        return " ".join("%X" % int(p, 2) if len(p) <= 4 else "%0*X" % (len(p) // 4, int(p, 2)) for p in split(bits, widths))
    if name == "1400":
        L = len(bits)
        widths = FIELDS["1400"][{36: "I", 20: "II", 52: "III"}[L]]
    elif name in ("1402", "1401"):
        L = len(bits)
        widths = FIELDS[name]["I" if L in (54, 49) else "II"]
    else:  # 1399
        if bits[0] == "1":
            widths = [1, 5, 24]
        elif bits[:2] == "00":
            widths = [2, 4, 1, 5, 6] if mnem in ("addq", "subq", "movq") else [2, 4, 1, 5, 1, 5]
        elif bits[:3] == "010":
            widths = [3, 4, 5]
        else:
            widths = [3, 4, 5, 24]
    return " ".join(split(bits, widths))


def fmt_units(m, bits):
    u = m.unit
    us = [bits[i:i + u] for i in range(0, len(bits), u)]
    if u == 4:
        return "".join("?" if "?" in x else "%X" % int(x, 2) for x in us)
    if u == 6:
        return " ".join("??" if "?" in x else "%02o" % int(x, 2) for x in us[:12]) + (" …" if len(us) > 12 else "")
    return " ".join("??" if "?" in x else "%02X" % int(x, 2) for x in us[:12]) + (" …" if len(us) > 12 else "")


def q4(pid, presym=None):
    m, src = PROGRAMS[pid]
    m = m() if isinstance(m, type) else type(m)()
    img, lst = m.assemble(src, presym=presym)
    unit_head = {4: "Hex (1 digit = 1 unit)", 6: "Octal (2 digits = 1 unit)", 7: "Hex per 7-bit unit"}[m.unit]
    rows = []
    for addr, label, mnem, ops, raw, bits in lst:
        src_txt = html.escape(raw.split(";")[0].strip())
        flds = html.escape(fmt_fields(m, mnem, ops, bits))
        units = html.escape(fmt_units(m, bits)) if m.unit != 4 else ""
        if m.unit == 4:
            rows.append(f'<tr><td>{addr:X}</td><td class="l">{src_txt}</td><td class="l">{flds}</td></tr>')
        else:
            rows.append(f'<tr><td>{addr:X}</td><td class="l">{src_txt}</td><td class="l">{flds}</td><td class="l">{units}</td></tr>')
    if m.unit == 4:
        head = '<tr><th>Addr</th><th class="l">Source</th><th class="l">Machine code (hex, by field)</th></tr>'
    else:
        head = f'<tr><th>Addr</th><th class="l">Source</th><th class="l">Fields (binary)</th><th class="l">{unit_head}</th></tr>'
    syms = ", ".join(f"{k}={v:X}h" for k, v in m.sym.items() if not (presym and k in presym))
    return (f'<table class="t mono tiny q4"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table>'
            f'<p class="sm mw">Symbols: {html.escape(syms)}</p>')


PRESYM = {"e1402": {"OS_Control_Point": 0xFFFF00}, "e1398": {"OS_control_point": 0xFFFF0000}}


def assemble_doc(pages=None, markers=False):
    body = (ROOT / "content.html").read_text(encoding="utf-8")
    body = re.sub(r"\{\{code:(\w+)\}\}", lambda m: code(m.group(1)), body)
    programs360.run_programs360(verbose=False)
    body = re.sub(r"\{\{c360:(\w+)\}\}", lambda m: c360(m.group(1)), body)
    body = re.sub(r"\{\{q4:(\w+)\}\}", lambda m: q4(m.group(1), PRESYM.get(m.group(1))), body)
    toc, n = [], 0

    def h2(mm):
        nonlocal n
        n += 1
        title = mm.group(1)
        toc.append((f"s{n}", n, re.sub("<[^>]+>", "", title)))
        mk = f'<span class="mk">QQS{n:02d}QQ</span>' if markers else ""
        return f'<h2 id="s{n}"><span class="sn">{fa(n)}</span>{title}{mk}</h2>'

    body = re.sub(r"<h2>(.*?)</h2>", h2, body, flags=re.S)
    items = []
    for hid, num, title in toc:
        pg = fa(pages.get(hid, "")) if pages else "۰"
        items.append(f'<div><a href="#{hid}">{fa(num)}. {html.escape(title)}</a><span class="dots"></span>'
                     f'<a class="pg" href="#{hid}">{pg}</a></div>')
    body = body.replace("<!--TOC-->", '<div class="toc">' + "".join(items) + "</div>")
    OUT_HTML.write_text('<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
                        '<title>ایده‌ها و الگوهای حل مسئله — ساختار و زبان کامپیوتر</title>'
                        '<link rel="stylesheet" href="style.css"></head><body>' + body + "</body></html>",
                        encoding="utf-8")
    return [t[0] for t in toc]


def render(pdf):
    subprocess.run(["node", str(RENDER), str(OUT_HTML), str(pdf)], check=True)


def page_numbers(pdf):
    txt = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    res = {}
    for pno, page in enumerate(txt.split("\f"), start=1):
        for mm in re.finditer(r"QQS(\d\d)QQ", page):
            res.setdefault(f"s{int(mm.group(1))}", pno)
    return res


if __name__ == "__main__":
    run_all()
    assemble_doc(markers=True)
    tmp = ROOT / "_pass1.pdf"
    render(tmp)
    pages = page_numbers(tmp)
    assemble_doc(pages, markers=True)
    render(OUT_PDF)
    tmp.unlink(missing_ok=True)
    print("built", OUT_PDF)
