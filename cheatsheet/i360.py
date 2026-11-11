"""IBM 360 tables for the cheat sheet, generated from the verified assembler (patterns/verify/ibm360.py)."""
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "patterns" / "verify"))
import ibm360  # noqa: E402
import programs360  # noqa: E402

# (mnemonic, format, operation, CC) — CC: A = arithmetic (00 zero, 01 <0, 10 >0, 11 overflow),
# L = logical add/sub (00 zero, 10 nonzero, 11 carry), B = bitwise (sign of result), C = compare, — = unchanged
OPS = [
    ("#", "RR — ۲ بایت: op r1 r2"),
    ("LR", "r1 ← (r2)", "—"), ("LCR", "r1 ← −(r2)", "A"), ("LNR", "r1 ← −|(r2)|", "A"), ("LPR", "r1 ← |(r2)|", "A"),
    ("AR", "r1 ← (r1)+(r2)", "A"), ("SR", "r1 ← (r1)−(r2)", "A"),
    ("MR", "r1:r1+1 ← (r1+1)×(r2) ; r1 even", "A"), ("DR", "r1:r1+1 ÷ (r2): q→r1+1, rem→r1", "A"),
    ("ALR", "r1 ← (r1)+(r2) unsigned", "L"), ("SLR", "r1 ← (r1)−(r2) unsigned", "L"),
    ("NR", "r1 ← (r1)∧(r2)", "B"), ("OR", "r1 ← (r1)∨(r2)", "B"), ("XR", "r1 ← (r1)⊕(r2)", "B"),
    ("CR", "(r1) ? (r2) signed", "C"), ("CLR", "(r1) ? (r2) unsigned", "C"),
    ("BCTR", "r1−−; if ≠0 and r2≠0: PC ← (r2)", "—"), ("BCR", "if mask(CC): PC ← (r2) ; r2=0 never", "—"),
    ("BALR", "r1 ← next PC; if r2≠0: PC ← (r2)", "—"),
    ("#", "RX — ۴ بایت: op r1 X2 B2 D2 ؛ EA = D2+(B2)+(X2)"),
    ("L", "r1 ← M[EA]", "—"), ("ST", "M[EA] ← (r1)", "—"), ("LA", "r1 ← EA (24 bit, no memory)", "—"),
    ("A", "r1 ← (r1)+M", "A"), ("S", "r1 ← (r1)−M", "A"), ("M", "r1:r1+1 ← (r1+1)×M", "A"),
    ("D", "r1:r1+1 ÷ M: q→r1+1, rem→r1", "A"), ("AL", "r1 ← (r1)+M unsigned", "L"), ("SL", "r1 ← (r1)−M unsigned", "L"),
    ("N", "r1 ← (r1)∧M", "B"), ("O", "r1 ← (r1)∨M", "B"), ("X", "r1 ← (r1)⊕M", "B"),
    ("C", "(r1) ? M signed", "C"), ("CL", "(r1) ? M unsigned", "C"),
    ("BCT", "r1−−; if ≠0: PC ← EA", "—"), ("BC", "if mask M1 matches CC: PC ← EA", "—"),
    ("#", "RS — ۴ بایت: op r1 r3 B2 D2"),
    ("LM", "r1..r3 ← consecutive words at EA", "—"), ("STM", "words at EA ← r1..r3", "—"),
    ("SLL", "r1 ← (r1) << (EA mod 64)", "—"), ("SRL", "r1 ← (r1) >> (EA mod 64)", "—"),
    ("#", "SI — ۴ بایت: op I2 B1 D1 (یک بایت)"),
    ("MVI", "byte M[EA] ← I2", "—"), ("CLI", "byte M[EA] ? I2", "C"),
    ("NI", "byte ∧= I2", "*"), ("OI", "byte ∨= I2", "*"), ("XI", "byte ⊕= I2", "*"),
    ("#", "SS — ۶ بایت: op L−1 B1 D1 B2 D2 (AP: L1−1|L2−1)"),
    ("MVC", "move L bytes: D1(L,B1) ← D2(B2)", "—"), ("CLC", "compare L bytes", "C"),
    ("NC", "AND L bytes", "*"), ("OC", "OR L bytes", "*"), ("XC", "XOR L bytes", "*"),
    ("AP", "packed-decimal add (lengths L1, L2)", "*"),
]


def opcode(mn):
    for fmt, tab in (("RR", ibm360.RR), ("RX", ibm360.RX), ("RS", ibm360.RS), ("SI", ibm360.SI),
                     ("SS", ibm360.SS1), ("SS", ibm360.SS2)):
        if mn in tab:
            return "%02X" % tab[mn]
    raise KeyError(mn)


def ops_table():
    out = ['<table class="t tiny"><thead><tr><th>Op</th><th>Mn</th><th>Operation</th><th>CC</th></tr></thead><tbody>']
    for r in OPS:
        if r[0] == "#":
            out.append(f'<tr><th colspan="4" class="l">{r[1]}</th></tr>')
            continue
        mn, sem, cc = r
        out.append(f'<tr><td class="op">{opcode(mn)}</td><td class="mn">{mn}</td><td class="ex">{html.escape(sem)}</td><td>{cc}</td></tr>')
    out.append("</tbody></table>")
    out.append('<p class="sm">CC: <b>A</b> حسابی (00 صفر، 01 منفی، 10 مثبت، 11 سرریز) · <b>L</b> منطقی (00 صفر، 10 ناصفر، 11 نقلی/قرض) · '
               '<b>B</b> بیتی (طبق علامت نتیجه) · <b>C</b> مقایسه (00 برابر، 01 اولی کوچک‌تر، 10 اولی بزرگ‌تر) · '
               '<b>—</b> بدون تغییر · <b>*</b> در اسلایدها بررسی نشده. EOJ = SVC 14 = <span class="mw">0A0E</span>.</p>')
    return "".join(out)


MASKS = [
    (0, "—", "never", "NOP", "NOPR"), (1, "11", "overflow", "BO", "BOR"), (2, "10", "plus / high", "BP BH", "BPR BHR"),
    (3, "10,11", "", "—", "—"), (4, "01", "minus / low", "BM BL", "BMR BLR"), (5, "01,11", "", "—", "—"),
    (6, "01,10", "", "—", "—"), (7, "01,10,11", "not zero / not equal", "BNZ BNE", "BNZR BNER"),
    (8, "00", "zero / equal", "BZ BE", "BZR BER"), (9, "00,11", "", "—", "—"), (10, "00,10", "", "—", "—"),
    (11, "00,10,11", "not minus / not low", "BNM BNL", "BNMR BNLR"), (12, "00,01", "", "—", "—"),
    (13, "00,01,11", "not plus / not high", "BNP BNH", "BNPR BNHR"), (14, "00,01,10", "not overflow", "BNO", "BNOR"),
    (15, "all", "always", "B", "BR"),
]


def mask_table():
    # cross-check the extended mnemonics against the assembler
    for m, _, _, rx, rr in MASKS:
        for name in rx.split():
            if name != "—":
                assert ibm360.EXT[name] == m, name
        for name in rr.split():
            if name != "—":
                assert ibm360.EXTR[name] == m, name
    out = ['<table class="t tiny"><thead><tr><th>M1</th><th>bits</th><th>CC → jump</th><th>RX (47)</th><th>RR (07)</th></tr></thead><tbody>']
    for m, cc, mean, rx, rr in MASKS:
        out.append(f'<tr><td>{m}</td><td class="mw">{m:04b}</td><td>{cc}</td><td class="mn">{rx}</td><td class="mn">{rr}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


BASES = {12: 0x10000, 11: 0x20000, 10: 0x30000, 9: 0x40000}
SYMS = {"ARR": 0x10123, "LOP1": 0x10100, "LOOP": 0x101FF, "HEY": 0x10070, "ABS": 0x20234,
        "DST": 0x1000A, "SRC": 0x10110, "AREA": 0x4011B, "NUM1": 0x1010A, "NUM2": 0x10F10}
ENC = [
    ("LR 3,5", "RR"), ("LR B'101',X'D'", "RR: B'101'=5, X'D'=13"), ("MR 8,4", "RR"), ("BCTR 5,0", "r2=0: no jump"),
    ("BR 14", "BCR 15,14"), ("BALR 11,0", "base setup"),
    ("L 2,ARR(4)", "S2(X2): X=4, B=C"), ("L 2,ARR", "S2: X=0"), ("L 2,20(4,3)", "D(X,B)"), ("L 2,0(5)", "one reg = index!"),
    ("L 2,10(,5)", "D(,B)"), ("A 7,ABS(6)", "ABS via R11"), ("LA 3,4(5,6)", ""), ("LA 5,8", "constant"),
    ("C 4,B'11'(B'10',X'A')", "X=2, B=A, D=3"), ("BC B'1011',2(3,4)", "mask 11"), ("BNE LOP1", "mask 7"),
    ("BNO 12(3,4)", "mask 14"), ("BCT 3,LOOP", ""), ("MVC DST(100),SRC", "L−1 = 99 = 63h"),
    ("OC AREA(10),10(4)", "SS: (L,B)"), ("AP NUM1(6),NUM2(5)", "L1−1, L2−1"),
]


def assemble_one(line):
    src = ("T        START X'8000'\n" + "".join(f"         USING B{r},{r}\n" for r in BASES)
           + "         " + line + "\n         END")
    pre = {f"B{r}": v for r, v in BASES.items()}
    pre.update(SYMS)
    a = ibm360.assemble(src, pre)
    row = [r for r in a.rows if r["kind"] == "ins"][0]
    return row["obj"].hex().upper()


EXPECT = {"LR 3,5": "1835", "MR 8,4": "1C84", "L 2,ARR(4)": "5824C123", "L 2,20(4,3)": "58243014",
          "BNE LOP1": "4770C100", "MVC DST(100),SRC": "D263C00AC110", "AP NUM1(6),NUM2(5)": "FA54C10ACF10",
          "OC AREA(10),10(4)": "D609911B400A", "BC B'1011',2(3,4)": "47B34002"}


def enc_table():
    out = ['<table class="t tiny"><thead><tr><th class="l">Instruction</th><th class="l">Code</th><th class="l">Note</th></tr></thead><tbody>']
    for line, note in ENC:
        code = assemble_one(line)
        if line in EXPECT:
            assert code == EXPECT[line], (line, code)
        out.append(f'<tr><td class="l mw">{html.escape(line)}</td><td class="l mw">{code}</td><td class="l">{html.escape(note)}</td></tr>')
    out.append("</tbody></table>")
    out.append('<p class="sm">نمادها: ARR = (R12)+123h، LOP1 = (R12)+100h، LOOP = (R12)+1FFh، ABS = (R11)+234h، '
               'DST = (R12)+0Ah، SRC = (R12)+110h، AREA = (R9)+11Bh، NUM1 = (R12)+10Ah، NUM2 = (R12)+F10h (همه از اسلایدها؛ با اسمبلر بررسی شده).</p>')
    return "".join(out)


def listing(pid):
    a = ibm360.assemble(programs360.P360[pid][1])
    lines = []
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
        src = f'{lab:<6} {r.get("mn") or "":<5} {r.get("ops") or ""}'.rstrip()
        if len(src) > 28:
            src = src[:27] + "…"
        lines.append(f'{loc} {obj:<9} {html.escape(src)}')
    return '<pre>' + "\n".join(lines) + "</pre>"


def prog_sumarr():
    return listing("sumarr")


def prog_callsub():
    return listing("callsub")


def prog_gnome():
    return listing("gnome")


GEN360 = {"i360ops": ops_table, "i360mask": mask_table, "i360enc": enc_table,
          "i360sum": prog_sumarr, "i360call": prog_callsub, "i360gnome": prog_gnome}
