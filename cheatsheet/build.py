#!/usr/bin/env python3
"""Build the open-book cheat sheet: content.html (+ generated tables) -> cheatsheet.html -> PDF.

Two render passes: the first finds the page of every section for the table of contents.
"""
import html
import re
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_HTML = ROOT / "cheatsheet.html"
OUT_PDF = ROOT.parent / "CSL_CheatSheet.pdf"
RENDER = ROOT.parent / "jozveh" / "render.js"
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(n):
    return str(n).translate(FA)


def M(x):
    return f"M<sub>{x}</sub>"


def C(x):
    return f"(M<sub>{x}</sub>)"


# ------------------------------------------------------------------ machine opcode tables
def optable(rows, head=("Opcode", "Mnemonic", "Operation")):
    """rows: (opcode, mnemonic, operation) or ('#', group label) to start a group row."""
    out = ['<table class="t tiny"><thead><tr>' + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead><tbody>"]
    for r in rows:
        if r[0] == "#":
            out.append(f'<tr><th colspan="3" class="l">{r[1]}</th></tr>')
            continue
        op, mn, sem = r
        out.append(f'<tr><td class="op">{op}</td><td class="mn">{mn}</td><td class="ex">{sem}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def m1():
    return optable([
        ("00", "add a1,a2", f"{M('a1')} ← {C('a1')} + {C('a2')}"),
        ("01", "sub a1,a2", f"{M('a1')} ← {C('a1')} − {C('a2')}"),
        ("10", "mov a1,a2", f"{M('a1')} ← {C('a2')}"),
        ("11", "nop", "no operation"),
    ])


def m2():
    return optable([
        ("00", "mov a1,a2", f"{M('a1')} ← {C('a2')}"),
        ("01", "add a1,a2", f"{M('a1')} ← {C('a1')} + {C('a2')}"),
        ("02", "sub a1,a2", f"{M('a1')} ← {C('a1')} − {C('a2')}"),
        ("03", "and a1,a2", f"{M('a1')} ← {C('a1')} ∧ {C('a2')}"),
        ("04", "or  a1,a2", f"{M('a1')} ← {C('a1')} ∨ {C('a2')}"),
        ("05", "xor a1,a2", f"{M('a1')} ← {C('a1')} ⊕ {C('a2')}"),
    ])


def m3():
    ia = "M<sub>(M<sub>a2</sub>)</sub>"
    return optable([
        ("00", "mov a1,a2", f"{M('a1')} ← {C('a2')}"),
        ("01", "mov a1,(a2)", f"{M('a1')} ← ({ia})"),
        ("02", "mov (a1),a2", f"M<sub>(M<sub>a1</sub>)</sub> ← {C('a2')}"),
        ("03", "add a1,a2", f"{M('a1')} ← {C('a1')} + {C('a2')}"),
        ("04", "sub a1,a2", f"{M('a1')} ← {C('a1')} − {C('a2')}"),
        ("05", "add a1,(a2)", f"{M('a1')} ← {C('a1')} + ({ia})"),
        ("06", "sub a1,(a2)", f"{M('a1')} ← {C('a1')} − ({ia})"),
        ("80", "jnz a1,a2", f"if {C('a1')} ≠ 0: PC ← a2"),
        ("81", "jz a1,a2", f"if {C('a1')} = 0: PC ← a2"),
        ("82", "jneg a1,a2", f"if {C('a1')} &lt; 0: PC ← a2"),
        ("83", "jpos a1,a2", f"if {C('a1')} &gt; 0: PC ← a2"),
    ])


def m4():
    return optable([
        ("#", "Format I: op4 | r1 4 | r2 4 (3 units)"),
        ("0", "mov r1,r2", "r1 ← (r2)"),
        ("1", "mov r1,(r2)", "r1 ← (M<sub>(r2)</sub>)"),
        ("2", "mov (r1),r2", "M<sub>(r1)</sub> ← (r2)"),
        ("3", "add r1,r2", "r1 ← (r1)+(r2)"),
        ("4", "sub r1,r2", "r1 ← (r1)−(r2)"),
        ("#", "Format II: op4 | r 4 | addr 12 (5 units)"),
        ("5", "mov r,addr", f"r ← {C('addr')}"),
        ("6", "mov addr,r", f"{M('addr')} ← (r)"),
        ("7", "mov r,(addr)", "r ← (M<sub>(M<sub>addr</sub>)</sub>)"),
        ("8", "mov (addr),r", "M<sub>(M<sub>addr</sub>)</sub> ← (r)"),
        ("9", "jz r,addr", "if (r)=0: PC ← addr"),
        ("A", "jnz r,addr", "if (r)≠0: PC ← addr"),
        ("B", "jneg r,addr", "if (r)&lt;0: PC ← addr"),
        ("C", "jpos r,addr", "if (r)&gt;0: PC ← addr"),
        ("#", "Format III: op4 | r 4 | data 16 (6 units)"),
        ("D", "mov r,#data", "r ← data"),
        ("E", "add r,#data", "r ← (r)+data"),
        ("F", "sub r,#data", "r ← (r)−data"),
    ])


def m5():
    return optable([
        ("#", "Format I: op4 | r1 6 | r2 6 (2 bytes) — hex = op·1000h + r1·40h + r2"),
        ("0", "mov r1,r2", "r1 ← (r2)"),
        ("1", "add r1,r2", "r1 ← (r1)+(r2)"),
        ("2", "sub r1,r2", "r1 ← (r1)−(r2)"),
        ("3", "and r1,r2", "r1 ← (r1)∧(r2)"),
        ("4", "or r1,r2", "r1 ← (r1)∨(r2)"),
        ("5", "xor r1,r2", "r1 ← (r1)⊕(r2)"),
        ("#", "Format II: op4 | r1 6 | r2 6 | addr 16 (4 bytes)"),
        ("6", "mov r1,addr(r2)", "r1 ← (M<sub>addr+(r2)</sub>)"),
        ("7", "mov addr(r2),r1", "M<sub>addr+(r2)</sub> ← (r1)"),
        ("8", "mov r1,r2,addr", f"r1 ← (r2); r2 ← {C('addr')}"),
        ("9", "mov addr,r1,r2", f"{M('addr')} ← (r1); r1 ← (r2)"),
        ("A", "je r1,r2,addr", "if (r1)=(r2): PC ← addr"),
        ("B", "jne r1,r2,addr", "if (r1)≠(r2): PC ← addr"),
        ("C", "jl r1,r2,addr", "if (r1)&lt;(r2): PC ← addr"),
        ("D", "jh r1,r2,addr", "if (r1)&gt;(r2): PC ← addr"),
        ("E", "call r1,addr(r2)", "r1 ← (PC); PC ← addr+(r2)"),
        ("#", "Format III: op10 | r 6 | data 16 (4 bytes) — first word = F000h + sub·40h + r"),
        ("1111 000000", "mov r,#data", "r ← data"),
        ("1111 000001", "add r,#data", "r ← (r)+data"),
        ("1111 000010", "sub r,#data", "r ← (r)−data"),
        ("1111 000011", "and r,#data", "r ← (r)∧data"),
        ("1111 000100", "or r,#data", "r ← (r)∨data"),
        ("1111 000101", "xor r,#data", "r ← (r)⊕data"),
    ])


def m1a():
    return optable([
        ("0", "load #data", "ACC ← data"),
        ("1", "add #data", "ACC ← (ACC)+data"),
        ("2", "load addr", f"ACC ← {C('addr')}"),
        ("3", "store addr", f"{M('addr')} ← (ACC)"),
        ("4", "add addr", f"ACC ← (ACC)+{C('addr')}"),
        ("5", "sub addr", f"ACC ← (ACC)−{C('addr')}"),
        ("6", "and addr", f"ACC ← (ACC)∧{C('addr')}"),
        ("7", "or addr", f"ACC ← (ACC)∨{C('addr')}"),
        ("8", "xor addr", f"ACC ← (ACC)⊕{C('addr')}"),
        ("9", "load (addr)", "ACC ← (M<sub>(M<sub>addr</sub>)</sub>)"),
        ("A", "store (addr)", "M<sub>(M<sub>addr</sub>)</sub> ← (ACC)"),
        ("B", "j addr", "PC ← addr"),
        ("C", "jz addr", "if (ACC)=0: PC ← addr"),
        ("D", "jnz addr", "if (ACC)≠0: PC ← addr"),
        ("E", "jn addr", "if (ACC)&lt;0: PC ← addr"),
        ("F", "jp addr", "if (ACC)&gt;0: PC ← addr"),
    ])


def m6():
    s = "Stack<sub>(SP)−1</sub>"
    s2 = "Stack<sub>(SP)−2</sub>"
    return optable([
        ("#", "Format I: op 8 | addr/data 32 (5 bytes)"),
        ("00", "push #data", "Stack<sub>(SP)</sub> ← data; SP++"),
        ("01", "push addr", f"Stack<sub>(SP)</sub> ← {C('addr')}; SP++"),
        ("02", "pop addr", f"SP−−; {M('addr')} ← (Stack<sub>(SP)</sub>)"),
        ("#", "Format II: op 8 (1 byte)"),
        ("03", "add", f"{s2} ← ({s2})+({s}); SP−−"),
        ("04", "sub", f"{s2} ← ({s2})−({s}); SP−−"),
        ("05", "swap", f"{s} ↔ {s2}"),
        ("06", "sp++", "SP ← (SP)+1"),
        ("07", "sp--", "SP ← (SP)−1"),
        ("08", "j", f"PC ← ({s}); SP−−"),
        ("09", "jz", f"if ({s2})=0: PC ← ({s}); SP −= 2"),
        ("0A", "jnz", f"if ({s2})≠0: PC ← ({s}); SP −= 2"),
        ("0B*", "jn", f"if ({s2})&lt;0: PC ← ({s}); SP −= 2"),
    ])


def m7():
    return optable([
        ("#", "Format I: op 8 | addr/data 32 (5 bytes)"),
        ("00", "load addr", f"ACC ← {C('addr')}"),
        ("01", "load (addr)", "ACC ← (M<sub>(M<sub>addr</sub>)</sub>)"),
        ("02", "store addr", f"{M('addr')} ← (ACC)"),
        ("03", "store (addr)", "M<sub>(M<sub>addr</sub>)</sub> ← (ACC)"),
        ("04", "add addr", f"ACC ← (ACC)+{C('addr')}"),
        ("05", "sub addr", f"ACC ← (ACC)−{C('addr')}"),
        ("06", "addi data", "ACC ← (ACC)+data"),
        ("07", "subi data", "ACC ← (ACC)−data"),
        ("08", "jmpl addr", "PC ← addr  (absolute)"),
        ("#", "Format II: op 8 | displacement 8 (2 bytes) — PC = next instr."),
        ("80", "jnz addr", "if (ACC)≠0: PC ← (PC)+d"),
        ("81", "jz addr", "if (ACC)=0: PC ← (PC)+d"),
        ("82", "jneg addr", "if (ACC)&lt;0: PC ← (PC)+d"),
        ("83", "jpos addr", "if (ACC)≥0: PC ← (PC)+d"),
        ("84", "jmp addr", "PC ← (PC)+d"),
    ])


# ------------------------------------------------------------------ number tables
def hextable():
    rows = []
    for i in range(16):
        rows.append(f"<tr><td>{i}</td><td>{i:04b}</td><td>{i:o}</td><td>{i:X}</td></tr>")
    half = len(rows) // 2
    head = "<thead><tr><th>Dec</th><th>Bin</th><th>Oct</th><th>Hex</th></tr></thead>"
    t1 = f'<table class="t mono tiny">{head}<tbody>{"".join(rows[:half])}</tbody></table>'
    t2 = f'<table class="t mono tiny">{head}<tbody>{"".join(rows[half:])}</tbody></table>'
    return f'<div class="two">{t1}{t2}</div>'


def pow2():
    rows = []
    for n in range(0, 17):
        m = n + 16
        rows.append(f"<tr><td>{n}</td><td>{2**n:,}</td><td>{m}</td><td>{2**m:,}</td></tr>")
    neg = "".join(f"<tr><td>−{n}</td><td>{2**-n:.10g}</td></tr>" for n in range(1, 13))
    t1 = ('<table class="t mono tiny"><thead><tr><th>n</th><th>2<sup>n</sup></th><th>n</th><th>2<sup>n</sup></th></tr></thead>'
          f"<tbody>{''.join(rows)}</tbody></table>")
    t2 = f'<table class="t mono tiny"><thead><tr><th>n</th><th>2<sup>n</sup></th></tr></thead><tbody>{neg}</tbody></table>'
    return f'<div class="two" style="grid-template-columns:1.7fr 1fr">{t1}{t2}</div>'


def signed4():
    rows = []
    for v in range(7, -9, -1):
        sm = (f"{abs(v):04b}" if v >= 0 else f"{8 + abs(v):04b}") if abs(v) <= 7 else "—"
        o1 = (f"{v:04b}" if v >= 0 else f"{15 + v:04b}") if v >= -7 else "—"
        t2 = f"{v & 15:04b}"
        e8 = f"{v + 8:04b}"
        e7 = f"{v + 7:04b}" if -7 <= v <= 8 else "—"
        rows.append(f"<tr><td><b>{v:+d}</b></td><td>{sm}</td><td>{o1}</td><td>{t2}</td><td>{e8}</td><td>{e7}</td></tr>")
    rows.insert(8, "<tr><td><b>−0</b></td><td>1000</td><td>1111</td><td>—</td><td>—</td><td>—</td></tr>")
    rows.insert(0, "<tr><td><b>+8</b></td><td>—</td><td>—</td><td>—</td><td>—</td><td>1111</td></tr>")
    return ('<table class="t mono tiny"><thead><tr><th>Value</th><th>Sign-Mag</th><th>1s</th><th>2s</th><th>Excess-8</th><th>Excess-7</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>")


def ieee_common():
    vals = [("+0", 0.0), ("−0", -0.0), ("1.0", 1.0), ("−1.0", -1.0), ("2.0", 2.0), ("0.5", 0.5), ("0.1 (≈)", 0.1),
            ("0.15625", 0.15625), ("10.75", 10.75), ("25.0", 25.0), ("85.125", 85.125), ("−6.5", -6.5),
            ("−120.0", -120.0), ("+∞", float("inf")), ("−∞", float("-inf")),
            ("min normal 2<sup>−126</sup>", 2 ** -126), ("min denormal 2<sup>−149</sup>", 2 ** -149),
            ("max ≈3.4028×10<sup>38</sup>", 3.4028234663852886e38)]
    rows = []
    for name, v in vals:
        h = struct.pack(">f", v).hex().upper()
        b = f"{int(h, 16):032b}"
        bits = f"{b[0]} {b[1:9]} {b[9:20]}…"
        rows.append(f'<tr><td class="l">{name}</td><td>{h}</td><td class="l">{bits}</td></tr>')
    rows.append('<tr><td class="l">NaN (example)</td><td>7FC00000</td><td class="l">0 11111111 10000000000…</td></tr>')
    return ('<table class="t mono tiny"><thead><tr><th class="l">Value</th><th>Hex</th><th class="l">S | E(8) | F(23)</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>")


def ascii_table():
    ctrl = ["NUL", "SOH", "STX", "ETX", "EOT", "ENQ", "ACK", "BEL", "BS", "HT", "LF", "VT", "FF", "CR", "SO", "SI",
            "DLE", "DC1", "DC2", "DC3", "DC4", "NAK", "SYN", "ETB", "CAN", "EM", "SUB", "ESC", "FS", "GS", "RS", "US"]
    head = "".join(f"<th>{c}<br>{c:03b}</th>" for c in range(8))
    rows = []
    for r in range(16):
        cells = []
        for c in range(8):
            code = c * 16 + r
            if code < 32:
                t = ctrl[code]
            elif code == 32:
                t = "SP"
            elif code == 127:
                t = "DEL"
            else:
                t = html.escape(chr(code))
            cells.append(f"<td>{t}</td>")
        rows.append(f"<tr><th>{r:X} {r:04b}</th>" + "".join(cells) + "</tr>")
    return ('<table class="t mono tiny"><thead><tr><th>low\\high</th>' + head + "</tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def gray():
    rows = []
    for i in range(16):
        g = i ^ (i >> 1)
        rows.append(f"<tr><td>{i}</td><td>{i:04b}</td><td>{g:04b}</td></tr>")
    head = "<thead><tr><th>n</th><th>Binary</th><th>Gray</th></tr></thead>"
    return (f'<div class="two"><table class="t mono tiny">{head}<tbody>{"".join(rows[:8])}</tbody></table>'
            f'<table class="t mono tiny">{head}<tbody>{"".join(rows[8:])}</tbody></table></div>')


def fib():
    f = [0, 1]
    while len(f) < 26:
        f.append(f[-1] + f[-2])
    rows = []
    for i in range(0, 26, 2):
        a = f"<td>{i}</td><td>{f[i]}</td><td>{sum(f[:i+1])}</td>"
        b = f"<td>{i+1}</td><td>{f[i+1]}</td><td>{sum(f[:i+2])}</td>" if i + 1 < 26 else "<td></td><td></td><td></td>"
        rows.append(f"<tr>{a}{b}</tr>")
    return ('<table class="t mono tiny"><thead><tr><th>i</th><th>F<sub>i</sub></th><th>ΣF<sub>0..i</sub></th>'
            '<th>i</th><th>F<sub>i</sub></th><th>ΣF<sub>0..i</sub></th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")


def primes():
    pr = []
    k = 2
    while len(pr) < 100:
        if all(k % p for p in pr):
            pr.append(k)
        k += 1
    first = ", ".join(map(str, pr[:30]))
    return (f'<p class="mw sm" style="font-family:JBMono">{first}, …</p>'
            f'<p>صدمین عدد اول = <b>541</b>؛ مجموع ۱۰ / ۲۰ / ۵۰ / ۱۰۰ عدد اول: '
            f'<span class="m">{sum(pr[:10])} / {sum(pr[:20])} / {sum(pr[:50])} / <b>{sum(pr)}</b></span></p>')


GEN = {
    "m1": m1, "m2": m2, "m3": m3, "m4": m4, "m5": m5, "m1a": m1a, "m6": m6, "m7": m7,
    "hex": hextable, "pow2": pow2, "signed4": signed4, "ieee": ieee_common, "ascii": ascii_table,
    "gray": gray, "fib": fib, "primes": primes,
}


# ------------------------------------------------------------------ assemble
def assemble(pages=None, markers=False):
    body = (ROOT / "content.html").read_text(encoding="utf-8")
    body = re.sub(r"\{\{gen:(\w+)\}\}", lambda m: GEN[m.group(1)](), body)
    toc = []
    n = 0

    def h2(m):
        nonlocal n
        n += 1
        title = m.group(1)
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
    doc = ('<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
           '<title>چیت‌شیت ساختار و زبان کامپیوتر</title><link rel="stylesheet" href="style.css"></head><body>'
           + body + "</body></html>")
    OUT_HTML.write_text(doc, encoding="utf-8")
    return [t[0] for t in toc]


def render(pdf):
    subprocess.run(["node", str(RENDER), str(OUT_HTML), str(pdf)], check=True)


def page_numbers(pdf, ids):
    """Find each section's page from invisible markers (named destinations get lost in multicol)."""
    txt = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    res = {}
    for pno, page in enumerate(txt.split("\f"), start=1):
        for m in re.finditer(r"QQS(\d\d)QQ", page):
            res.setdefault(f"s{int(m.group(1))}", pno)
    return res


if __name__ == "__main__":
    ids = assemble(markers=True)
    tmp = ROOT / "_pass1.pdf"
    render(tmp)
    pages = page_numbers(tmp, ids)
    assemble(pages, markers=True)
    render(OUT_PDF)
    tmp.unlink(missing_ok=True)
    print("built", OUT_PDF)
