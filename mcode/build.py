#!/usr/bin/env python3
"""Build the machine-code writing cheat sheet (content.html + generated examples) -> PDF.

Every example table is produced by the same assemblers that the catalog uses (patterns/verify), so
the numbers in the sheet are exactly what the verified assemblers output.
"""
import html
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "patterns" / "verify"))

from asm import parse  # noqa: E402
from lecture_programs import LECTURE, run_lecture  # noqa: E402
from programs import PROGRAMS  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CAT = load_module("cat_build", REPO / "catalog" / "build.py")

OUT_HTML = ROOT / "mcode.html"
OUT_PDF = REPO / "CSL_MachineCode_CheatSheet.pdf"
RENDER = REPO / "jozveh" / "render.js"
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(n):
    return str(n).translate(FA)


# ====================================================================== small examples
MINI = {
    "order_m4": ("M4", """
        mov  R3,A       ; op 5 : r ← (M)
        mov  A,R3       ; op 6 : M ← r
        mov  R3,(A)     ; op 7
        mov  (A),R3     ; op 8
        mov  R3,(R2)    ; op 1 (قالب I)
        mov  R3,#A      ; op D : خودِ آدرس A
A:      dw   7""", ()),
    "order_m5": ("M5", """
        mov  R3,A(R1)   ; op 6 : r1=R3 r2=R1
        mov  A(R1),R3   ; op 7 : r1=R3 r2=R1
        mov  R2,R5,A    ; op 8 : r1=R2 r2=R5
        mov  A,R2,R5    ; op 9 : r1=R2 r2=R5
        call R0,0(R63)  ; op E
A:      dw   0""", ()),
    "order_1399": ("1399", """
        mov  R2,x       ; III 0000
        mov  x,R2       ; III 0001
        mov  R2,(x)     ; III 0010
        mov  (x),R2     ; III 0011
        mov  R2,#x      ; V
x:      dw   0""", ()),
    "modes_1402": ("1402", """
        mov  x,#5       ; yz=10 data
        mov  x,y        ; yz=00
        mov  x,(p)      ; yz=01
        mov  (p),y      ; x=1
        add  x,#-1      ; data = FFFFFF
        jz   L          ; 110 x=0
        jnz  L          ; 110 x=1
        jneg L          ; 111 x=0
L:      jmp  L          ; 111 x=1
x:      dw   0
y:      dw   0
p:      dw   x""", ()),
    "modes_1401": ("1401", """
        mov  a,#5       ; xy=10
        cmp  (p),a      ; i=1 xy=00
        add  a,#-2      ; 21-bit: 1FFFFE
        inc  a          ; F II: xy=11
        dec  (p)        ; i=1
L:      jmp  (1FFFFDh)  ; i=1 indirect
        call L
a:      dw   0
p:      dw   a""", ()),
    "modes_1400": ("1400", """
        mov  a,#5       ; d=1
        add  a,b        ; d=0
        inc  a          ; 011 x=0
        dec  a          ; 011 x=1
L:      jmp  (FFFEh)    ; 100 x=0
        call L          ; 100 x=1
        je   a,#0,L     ; III d=1
        jl   a,b,L      ; III d=0
a:      dw   0
b:      dw   0""", ()),
    "fmt_1399": ("1399", """
        mov  R1,R2      ; I
        add  (R1),R2    ; I i1=1
        swap (R1),(R2)  ; I i1=i2=1
        addq R1,4       ; I qdata
        inc4 R1         ; II
        jmp  R31        ; II
L:      loop R3,L       ; III
        mov  R5,#100    ; V""", ()),
    "fmt_1398": ("1398", """
        mov  R2,#3F800000h ; I
        fadd R3,R2      ; II
        mov  R1,x(R0)   ; III 0000
        mov  x(R0),R3   ; III 0001
L:      loop- R1,R4,L   ; III 0010
        fjh  R2,R6,L    ; III 1001
x:      dw   0""", ()),
    "fmt_m5": ("M5", """
        xor  R0,R0      ; I
        add  R1,#2      ; III
        jne  R1,R2,L    ; II
L:      mov  R3,A(R1)   ; II
A:      dw   0""", ()),
    "neg_imm": ("M4", """
        add  R5,#-1     ; −1 در ۱۶ بیت
        sub  R5,#1      ; همان نتیجه
        mov  R6,#-200   ; FF38h""", ()),
    "neg_1a": ("1A", """
        add  #-1        ; 1 FFFF
        load #-4        ; 0 FFFC""", ()),
    "rel_m7": ("M7", """
        org  100h
L:      load x
        jpos F          ; d = F − 107h = 7
        subi 1
        jmp  L          ; d = 100h − 10Eh = −14
F:      jmpl far        ; مطلق: دور است
x:      dw   -3
        org  300h
far:    load x""", ()),
    "dw_m7": ("M7", """
        org  100h
a:      dw   -1         ; FFFFFFFF
b:      dw   80000000h  ; کوچک‌ترین عدد
p:      dw   arr        ; آدرس arr
q:      dw   arr+8      ; آدرس arr[2]
arr:    dw   3,4,5      ; سه کلمه پشت‌سرهم
t:      dw   2 dup(?)   ; نامعلوم""", ()),
    "dw_1398": ("1398", """
one:    dw   3F800000h  ; 1.0
eps:    dw   3A800000h  ; 2^-10
f:      dw   -1.0e+109  ; −1.0 × 2^109
g:      dw   -40.5e+112 ; −40.5 × 2^112
i:      dw   -1         ; صحیح""", ()),
    "lc_m3": ("M3", LECTURE["m3_arrsum"][1], ()),
    "self_m3": ("M3", """
        org  100h
loop:   add  sum,array  ; addr2 = loop+3
        add  loop+3,two ; addr2 += 2
sum:    dw   0
two:    dw   2
array:  dw   0""", ()),
    "self_1402": ("1402", """
loop:   add  sum,A      ; addr2 = units 5..8
        add  loop+5,#4  ; addr2 += 4
sum:    dw   0
A:      dw   0""", ()),
    "exec_1399": ("1399", """
        dw   41006h     ; این «داده» اجرا می‌شود""", ()),
}

FULL = {
    "worked_m5": ("M5", LECTURE["m5_arrsum"][1], ()),
    "worked_1402": ("1402", PROGRAMS["e1402"][1], ("OS_Control_Point",)),
}


def mini(key):
    mkey, src, ext = MINI[key]
    m = CAT.MACHINES[mkey]["cls"]()
    img, lst = m.assemble(src, externals=ext)
    it = iter(lst)
    rows = []
    dg = getattr(m, "addr_digits", 4)
    for label, mnem, ops, raw in parse(src):
        if mnem in ("org", "end", None):
            continue
        addr, _, mn, op, _, bits = next(it)
        if mn == "dw":
            fd, code = CAT.dw_fields(m, bits), CAT.unit_text(m, bits, limit=8)
        else:
            fd, code = CAT.field_html(bits, m.widths(mn, op, bits)), CAT.unit_text(m, bits)
        lab = html.escape(label + ": ") if label else ""
        comment = raw.split(";", 1)[1] if ";" in raw else ""
        rows.append(f'<tr><td class="ad">{addr:0{dg}X}</td><td class="in"><span class="lb">{lab}</span>{CAT.instr_text(raw)}</td>'
                    f'<td class="fd">{fd}</td><td class="mc">{code}</td>{CAT.comment_html(comment)}</tr>')
    head = ('<thead><tr><th class="ad">Addr</th><th class="in">Assembly</th><th class="fd">Fields</th>'
            f'<th class="mc">Code ({html.escape(unit_name(m.unit))})</th><th class="cm">نکته</th></tr></thead>')
    return f'<table class="lst mini" data-m="{mkey}">{head}<tbody>{"".join(rows)}</tbody></table>'


def unit_name(u):
    return {4: "hex digit = 4b", 8: "bytes", 6: "octal pair = 6b", 7: "hex per 7b unit", 16: "16b"}[u]


def full(key):
    mkey, src, ext = FULL[key]
    tbl, cu, du, syms, e, unit = CAT.listing(dict(m=mkey, src=src, ext=ext))
    return tbl + f'<p class="pfoot"><b>نمادها:</b> <span class="mw">{html.escape(syms)}</span></p>'


# ====================================================================== generated reference tables
ORDER = ["M1", "M2", "M3", "M4", "M5", "1A", "M6", "M7", "1398", "1399", "1400", "1401", "1402"]


def fmt_name(name):
    m = re.match(r"^(I{1,3}|IV|V)\b", name)
    return m.group(1) if m else "—"


def fmt_lengths():
    rows = []
    for k in ORDER:
        d = CAT.MACHINES[k]
        cls = d["cls"]
        u = cls.unit
        cells = []
        for name, fields in d["formats"]:
            b = sum(w for _, w in fields)
            cells.append(f"{fmt_name(name)}: {b}b = {b // u}u")
        word = cls.word_units * u
        rows.append(f'<tr><td>{k}</td><td>{u}</td><td>{word} = {cls.word_units}u</td><td class="l">{"&nbsp;&nbsp; ".join(cells)}</td></tr>')
    return ('<table class="t tiny"><thead><tr><th>Machine</th><th>unit</th><th>word</th><th class="l">formats (bits = units)</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table>")


def field_offset(s, w, u, W, L):
    """Word address X+k that covers field [s, s+w) of an instruction of L bits; e = bits below the field."""
    full_, part = [], []
    for k in range(0, L // u + 1):
        lo, hi = k * u, k * u + W
        if s + w > hi:
            continue
        if lo <= s:
            full_.append((hi > L, hi - (s + w), k))
        elif lo < s + w:
            part.append((hi > L, -(s + w - lo), k))
    if full_:
        inside, e, k = min(full_)
        return k, e, None, inside
    inside, neg, k = min(part)
    e = k * u + W - (s + w)
    return k, e, -neg, inside


def check_offset(s, w, u, W, L, k, e):
    """Bit-level proof: adding d*2^e to the word at unit k adds d to the field (no carry)."""
    import random
    rnd = random.Random(s * 131 + w)
    bits = "".join(rnd.choice("01") for _ in range(L)) + "0" * (W + u)
    fv = int(bits[s:s + w], 2)
    d = 1
    if fv + d >= 1 << w:
        bits = bits[:s] + "0" * w + bits[s + w:]
        fv = 0
    lo = k * u
    word = int(bits[lo:lo + W], 2)
    word = (word + (d << e)) & ((1 << W) - 1)
    nb = bits[:lo] + format(word, f"0{W}b") + bits[lo + W:]
    return int(nb[s:s + w], 2) == fv + d


def offsets():
    rows = []
    for key in ORDER:
        d = CAT.MACHINES[key]
        cls = d["cls"]
        u, W = cls.unit, cls.unit * cls.word_units
        for name, fields in d["formats"]:
            L = sum(b for _, b in fields)
            s = 0
            for fname, b in fields:
                if b >= 12 and W >= 12:
                    k, e, part, outside = field_offset(s, b, u, W, L)
                    assert check_offset(s, b, u, W, L, k, e), (key, name, fname)
                    note = "کامل" if part is None else f"فقط {fa(part)} بیت پایین"
                    if outside:
                        note += "، کلمه از دستور بیرون می‌زند"
                    mult = "1" if e == 0 else f"2<sup>{e}</sup> = {1 << e}"
                    rows.append(f'<tr><td>{key}</td><td>{fmt_name(name)}</td><td class="l">{html.escape(fname)}</td>'
                                f'<td>{s}..{s + b - 1}</td><td><b>X+{k}</b></td><td>{mult}</td><td class="fa">{note}</td></tr>')
                s += b
    return ('<table class="t tiny"><thead><tr><th>M</th><th>F</th><th class="l">field</th><th>bits</th><th>word at</th>'
            '<th>×</th><th class="fa">پوشش</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")


def twos():
    widths = [8, 12, 16, 21, 24, 32]
    vals = [-1, -2, -3, -4, -8, -10, -16, -100, -128]
    head = "".join(f"<th>{w} bit</th>" for w in widths)
    rows = []
    for v in vals:
        cells = "".join(f"<td>{(v & ((1 << w) - 1)):0{(w + 3) // 4}X}</td>" for w in widths)
        rows.append(f"<tr><th>{v}</th>{cells}</tr>")
    return f'<table class="t mono tiny"><thead><tr><th>value</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def hexbin():
    h = "".join(f"<tr><td>{i:X}</td><td>{i:04b}</td><td>{i + 8:X}</td><td>{i + 8:04b}</td></tr>" for i in range(8))
    o = "".join(f"<tr><td>{i}</td><td>{i:03b}</td></tr>" for i in range(8))
    return (f'<div class="two" style="grid-template-columns:2fr 1fr"><table class="t mono tiny"><thead><tr><th>hex</th><th>bin</th>'
            f'<th>hex</th><th>bin</th></tr></thead><tbody>{h}</tbody></table>'
            f'<table class="t mono tiny"><thead><tr><th>oct</th><th>bin</th></tr></thead><tbody>{o}</tbody></table></div>')


def pow2():
    items = [(7, "M1"), (12, "M4"), (14, "1400 words"), (16, "M2,M3,M5,1A,1400"), (21, "1401"), (24, "1399,1402"),
             (29, "1398 words"), (32, "M6,M7,1398")]
    rows = "".join(f"<tr><td>2<sup>{n}</sup></td><td>{2 ** n:,}</td><td>{2 ** n:X}h</td><td class='l'>{w}</td></tr>" for n, w in items)
    return ('<table class="t mono tiny"><thead><tr><th>2^n</th><th>dec</th><th>hex</th><th class="l">used in</th></tr></thead>'
            f"<tbody>{rows}</tbody></table>")


def views(mkey, src, start, ext=()):
    """Fields / units / unit-text for the first instruction whose source starts with `start`."""
    m = CAT.MACHINES[mkey]["cls"]()
    img, lst = m.assemble(src, externals=ext)
    for a, l, mn, op, raw, bits in lst:
        code = raw.split(";")[0]
        code = re.sub(r"^\s*[A-Za-z_]\w*\s*:", "", code).strip()
        if code.startswith(start):
            ws, k, parts = m.widths(mn, op, bits), 0, []
            for w in ws:
                parts.append(bits[k:k + w])
                k += w
            units = " ".join(bits[i:i + m.unit] for i in range(0, len(bits), m.unit))
            name = {6: "octal", 4: "hex", 8: "hex", 7: "hex"}[m.unit]
            return (f'<table class="t mono tiny"><tbody><tr><th class="l">fields</th><td class="l">{" | ".join(parts)}</td></tr>'
                    f'<tr><th class="l">{m.unit}-bit units</th><td class="l">{units}</td></tr>'
                    f'<tr><th class="l">{name}</th><td class="l">{CAT.unit_text(m, bits)}</td></tr></tbody></table>')
    raise KeyError(start)


def view_1402():
    return views("1402", PROGRAMS["e1402"][1], "add  c+4", ("OS_Control_Point",))


def view_1400():
    return views("1400", MINI["modes_1400"][1], "jmp  (FFFEh)")


GEN = {"view_1402": view_1402, "view_1400": view_1400, "fmt_lengths": fmt_lengths, "offsets": offsets, "twos": twos, "hexbin": hexbin, "pow2": pow2}


# ====================================================================== document
def assemble_doc(pages=None, markers=False):
    body = (ROOT / "content.html").read_text(encoding="utf-8")
    body = re.sub(r"\{\{mini:(\w+)\}\}", lambda m: mini(m.group(1)), body)
    body = re.sub(r"\{\{full:(\w+)\}\}", lambda m: full(m.group(1)), body)
    body = re.sub(r"\{\{gen:(\w+)\}\}", lambda m: GEN[m.group(1)](), body)
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
                        '<title>چیت‌شیت نوشتن کد ماشین</title><link rel="stylesheet" href="style.css"></head><body>'
                        + body + "</body></html>", encoding="utf-8")


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
    run_lecture(verbose=False)       # the assemblers used for the examples are the verified ones
    assemble_doc(markers=True)
    tmp = ROOT / "_pass1.pdf"
    render(tmp)
    pages = page_numbers(tmp)
    assemble_doc(pages, markers=True)
    render(OUT_PDF)
    tmp.unlink(missing_ok=True)
    print("built", OUT_PDF)
