#!/usr/bin/env python3
"""Build the program catalog: every program of the notes, the midterms and the patterns sheet,
grouped by machine, each with the instruction formats, machine code and assembly listing.

All programs are assembled with the machine models in patterns/verify and executed before the PDF
is produced; the build stops if any test fails or a jozveh listing disagrees with the assembler.
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
from check_jozveh import check as check_jozveh  # noqa: E402
from exam_q3_tests import run_exam_q3  # noqa: E402
from lecture import L1, L1A, L2, L3, L4, L5, L6, L7  # noqa: E402
from lecture_programs import LECTURE, run_lecture  # noqa: E402
from machines import M1398, M1399, M1400, M1401, M1402  # noqa: E402
from programs import PROGRAMS, run_all  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CS = load_module("cs_build", REPO / "cheatsheet" / "build.py")      # opcode tables of lecture machines
JZ = load_module("jz_build", REPO / "jozveh" / "build.py")          # wrap_ltr for Persian comments

OUT_HTML = ROOT / "catalog.html"
OUT_PDF = REPO / "CSL_Programs_Catalog.pdf"
RENDER = REPO / "jozveh" / "render.js"
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(n):
    return str(n).translate(FA)


# ====================================================================== machines
def fmt(fields):
    return '<span class="fmt">' + "".join(f"<span>{n} <i>{b}</i></span>" for n, b in fields) + "</span>"


MACHINES = {
    "M1": dict(cls=L1, title="ماشین ۱ — دوآدرسه", table=CS.m1,
               spec="۱۲۸ خانهٔ ۱۶ بیتی (واحد آدرس‌پذیر = کلمه = ۱۶ بیت)؛ آدرس‌دهی مستقیم.",
               regs="MAR = 7، MBR = 16 بیت.",
               formats=[("یک قالب (۱۶ بیت = ۱ واحد)", [("op", 2), ("addr1", 7), ("addr2", 7)])]),
    "M2": dict(cls=L2, title="ماشین ۲ — دوآدرسه (بدون پرش)", table=CS.m2,
               spec="<span class=m>2<sup>16</sup></span> واحد ۸ بیتی، کلمه ۱۶ بیت (۲ بایت)؛ آدرس‌دهی مستقیم؛ دستور پرش ندارد.",
               regs="MAR = PC = 16، MBR = 16، IR = 40 بیت.",
               formats=[("یک قالب (۴۰ بیت = ۵ بایت)", [("op", 8), ("addr1", 16), ("addr2", 16)])]),
    "M3": dict(cls=L3, title="ماشین ۳ — دوآدرسه + غیرمستقیم + پرش شرطی", table=CS.m3,
               spec="مثل ماشین ۲؛ کلمهٔ ۱۶ بیتی ناهم‌تراز و Big Endian؛ مستقیم و غیرمستقیم حافظه‌ای؛ در پرش‌ها addr1 = متغیر شرط و addr2 = مقصد.",
               regs="MAR = PC = 16، MBR = 16، IR = 40 بیت.",
               formats=[("یک قالب (۵ بایت)", [("op", 8), ("addr1", 16), ("addr2", 16)])]),
    "M4": dict(cls=L4, title="ماشین ۴ — دوآدرسه با ۱۶ ثبات و واحد ۴ بیتی", table=CS.m4,
               spec="<span class=m>2<sup>12</sup></span> واحد ۴ بیتی، کلمه ۱۶ بیت = ۴ واحد، ناهم‌تراز و BE؛ R0..R15؛ ثباتی و حافظه‌ای (مستقیم و غیرمستقیم) و بی‌واسطه. هر رقم هگز = یک واحد.",
               regs="MAR = PC = 12، MBR = 16، IR = 24، R0..R15 = 16 بیت.",
               formats=[("I (۳ واحد)", [("op", 4), ("r1", 4), ("r2", 4)]),
                        ("II (۵ واحد)", [("op", 4), ("r", 4), ("addr", 12)]),
                        ("III (۶ واحد)", [("op", 4), ("r", 4), ("data", 16)])]),
    "M5": dict(cls=L5, title="ماشین ۵ — ۲/۳ آدرسه با ۶۴ ثبات", table=CS.m5,
               spec="<span class=m>2<sup>16</sup></span> بایت، کلمه ۱۶ بیت؛ R0..R63؛ ثباتی، مستقیم، بی‌واسطه و شاخص‌دار؛ کد عمل گسترش‌پذیر (1111 ⇐ ۶ بیت دیگر).",
               regs="MAR = PC = 16، MBR = 16، IR = 32، R0..R63 = 16 بیت.",
               formats=[("I (۲ بایت)", [("op", 4), ("r1", 6), ("r2", 6)]),
                        ("II (۴ بایت)", [("op", 4), ("r1", 6), ("r2", 6), ("addr", 16)]),
                        ("III (۴ بایت)", [("1111 op", 10), ("r", 6), ("data", 16)])]),
    "1A": dict(cls=L1A, title="ماشین تک‌آدرسه (انباره‌ای)", table=CS.m1a,
               spec="<span class=m>2<sup>16</sup></span> واحد ۴ بیتی، کلمه ۱۶ بیت = ۴ واحد؛ یک عملوند همیشه در ACC؛ ضمنی، مستقیم، غیرمستقیم و بی‌واسطه.",
               regs="MAR = PC = 16، MBR = ACC = 16، IR = 20 بیت.",
               formats=[("یک قالب (۲۰ بیت = ۵ واحد)", [("op", 4), ("addr/data", 16)])]),
    "M6": dict(cls=L6, title="ماشین ۶ — صفرآدرسه (پشته‌ای)", table=CS.m6,
               spec="<span class=m>2<sup>32</sup></span> بایت، کلمه ۳۲ بیت؛ پشتهٔ سخت‌افزاری ۱۶ کلمه‌ای؛ SP به اولین خانهٔ خالی اشاره می‌کند؛ ضمنی، مستقیم و بی‌واسطه. (کد jn در اسلاید اشتباهاً 08 آمده است.)",
               regs="MAR = PC = 32، MBR = 32، IR = 40، SP = 4 بیت.",
               formats=[("I (۵ بایت)", [("op", 8), ("addr/data", 32)]), ("II (۱ بایت)", [("op", 8)])]),
    "M7": dict(cls=L7, title="ماشین ۷ — تک‌آدرسه با پرش نسبی", table=CS.m7,
               spec="<span class=m>2<sup>32</sup></span> بایت، کلمه ۳۲ بیت (مکمل دو)، ناهم‌تراز و BE؛ مستقیم، غیرمستقیم، بی‌واسطه و نسبی. جابه‌جایی پرش = مقصد − آدرس دستور بعد (۸ بیت، ‎−128..127).",
               regs="MAR = PC = 32، MBR = ACC = 32، IR = 40 بیت.",
               formats=[("I (۵ بایت)", [("op", 8), ("addr/data", 32)]), ("II (۲ بایت)", [("op", 8), ("disp", 8)])]),
}

EXAM_TABLES = {
    "1398": [
        ("#", "Format I: 0000 | r 4 | data 32 (10 units)"), ("0000", "mov r,#data", "r ← data"),
        ("#", "Format II: op4 | r1 4 | r2 4 (3 units)"),
        ("0001", "mov r1,r2", "r1 ← (r2)"), ("0010", "add r1,r2", "r1 ← (r1)+(r2)"), ("0011", "sub r1,r2", "r1 ← (r1)−(r2)"),
        ("0100", "and r1,r2", "r1 ← (r1)∧(r2)"), ("0101", "or r1,r2", "r1 ← (r1)∨(r2)"), ("0110", "xor r1,r2", "r1 ← (r1)⊕(r2)"),
        ("0111", "ctf r1,r2", "r1 ← float(r2)"), ("1000", "cti r1,r2", "r1 ← integer(r2)"), ("1001", "efp r1,r2", "r1 ← fraction(r2)"),
        ("1010", "fadd r1,r2", "r1 ← (r1)+(r2)"), ("1011", "fsub r1,r2", "r1 ← (r1)−(r2)"), ("1100", "fmul r1,r2", "r1 ← (r1)×(r2)"),
        ("1101", "fdiv r1,r2", "r1 ← (r1)/(r2)"), ("1110", "fsqrt r1,r2", "r1 ← SQRT(r2)"),
        ("#", "Format III: 1111 op4 | r1 4 | r2 4 | addr 32 (12 units)"),
        ("0000", "mov r1,addr(r2)", "r1 ← (M<sub>addr+(r2)</sub>)"), ("0001", "mov addr(r2),r1", "M<sub>addr+(r2)</sub> ← (r1)"),
        ("0010", "loop- r1,r2,addr", "r1 ← (r1)−(r2); if (r1)&gt;(r2): PC ← addr"), ("0011", "loop+ r1,r2,addr", "r1 ← (r1)+1; if (r1)&lt;(r2): PC ← addr"),
        ("0100", "jl r1,r2,addr", "if (r1)&lt;(r2): PC ← addr"), ("0101", "jh", "if (r1)&gt;(r2)"), ("0110", "je", "if (r1)=(r2)"), ("0111", "jne", "if (r1)≠(r2)"),
        ("1000", "fjl", "float &lt;"), ("1001", "fjh", "float &gt;"), ("1010", "fjnan1", "r1 or r2 NaN"), ("1011", "fjnan2", "r1 and r2 NaN"),
        ("1100", "fjden1", "r1 or r2 denormal"), ("1101", "fjden2", "both denormal"), ("1110", "fjinf1", "r1 or r2 = ±∞"), ("1111", "fjinf2", "both ±∞"),
    ],
    "1399": [
        ("#", "Format I: 00 op4 | i1 r1 5 | i2 r2 5 / qdata 6 (3 units); i = 1 → M<sub>(r)</sub>"),
        ("0000", "mov opr1,opr2", "opr1 ← (opr2)"), ("0001", "add", "opr1 ← (opr1)+(opr2)"), ("0010", "sub", "opr1 ← (opr1)−(opr2)"),
        ("0011", "and", "∧"), ("0100", "or", "∨"), ("0101", "xor", "⊕"), ("0110", "swap opr1,opr2", "opr1 ⇄ opr2"),
        ("0111", "addq opr1,q", "opr1 ← (opr1)+q"), ("1000", "subq opr1,q", "opr1 ← (opr1)−q"), ("1001", "movq opr1,q", "opr1 ← q"),
        ("#", "Format II: 010 op4 | r 5 (2 units)"),
        ("0000", "jmp r", "PC ← (r)"), ("0001", "inc r", "+1"), ("0010", "dec r", "−1"), ("0011", "clr r", "r ← 0"),
        ("0100", "not r", "r ← not(r)"), ("0101", "neg r", "r ← −(r)"), ("0110", "inc4 r", "+4"), ("0111", "dec4 r", "−4"),
        ("#", "Format III: 011 op4 | r 5 | addr 24 (6 units)"),
        ("0000", "mov r,addr", "r ← (M<sub>addr</sub>)"), ("0001", "mov addr,r", "M<sub>addr</sub> ← (r)"),
        ("0010", "mov r,(addr)", "r ← (M<sub>(M<sub>addr</sub>)</sub>)"), ("0011", "mov (addr),r", "M<sub>(M<sub>addr</sub>)</sub> ← (r)"),
        ("0100", "jnz r,addr", "if (r)≠0"), ("0101", "jz r,addr", "if (r)=0"), ("0110", "jneg r,addr", "if (r)&lt;0"), ("0111", "jpos r,addr", "if (r)≥0"),
        ("1000", "loop r,addr", "r ← (r)−1; if (r)≠0: PC ← addr"), ("1001", "jmp+ r,addr", "r ← (r)+1; PC ← addr"), ("1010", "call r,addr", "r ← (PC); PC ← addr"),
        ("#", "Format V: 1 | r 5 | data 24 (5 units)"), ("1", "mov r,#data", "r ← data"),
    ],
    "1400": [
        ("#", "Format I: op3 | addr1 16 | d | addr2/data 16 (9 units); d=0: opr2 = (M<sub>a2</sub>), d=1: data"),
        ("000", "mov addr1,opr2", "M<sub>a1</sub> ← opr2"), ("001", "add addr1,opr2", "M<sub>a1</sub> ← (M<sub>a1</sub>)+opr2"), ("010", "sub addr1,opr2", "M<sub>a1</sub> ← (M<sub>a1</sub>)−opr2"),
        ("#", "Format II: op3 | addr1 16 | x (5 units)"),
        ("011 x=0", "inc addr1", "M<sub>a1</sub> ← (M<sub>a1</sub>)+1"), ("011 x=1", "dec addr1", "M<sub>a1</sub> ← (M<sub>a1</sub>)−1"),
        ("100 x=0", "jmp (addr1)", "PC ← (M<sub>a1</sub>)"), ("100 x=1", "call addr1", "M<sub>FFFE</sub> ← (PC); PC ← addr1"),
        ("#", "Format III: op3 | addr1 16 | d | addr2/data 16 | addr3 16 (13 units)"),
        ("101", "je a1,opr2,a3", "if (M<sub>a1</sub>)=opr2: PC ← a3"), ("110", "jne", "if ≠"), ("111", "jl", "if &lt;"),
    ],
    "1401": [
        ("#", "Format I: op4 | i | addr1 21 | xy | addr2/data 21 (7 units); i=1: opr1 indirect; xy: 00 dir, 01 ind, 10 data, 11 → II"),
        ("0000", "mov opr1,opr2", "opr1 ← opr2"), ("0001", "and", "∧"), ("0010", "or", "∨"), ("0011", "xor", "⊕"),
        ("0100", "cmp opr1,opr2", "(opr1) − opr2, update PSR"), ("0101", "sub", "opr1 ← (opr1)−opr2"), ("0110", "add", "opr1 ← (opr1)+opr2"),
        ("#", "Format II: op4 | i | addr1 21 | 11 (4 units); i=1: target = (M<sub>a1</sub>)"),
        ("0000", "clr opr1", "← 0"), ("0001", "inc opr1", "+1"), ("0010", "dec opr1", "−1"), ("0011", "not opr1", "¬"), ("0100", "neg opr1", "−"),
        ("0101", "call target", "M<sub>1FFFFD</sub> ← (PC); PC ← target"), ("0110", "jmp target", "PC ← target"),
        ("0111", "jz", "if z=1"), ("1000", "jnz", "if z=0"), ("1001", "jneg", "if s=1"), ("1010", "jpos", "if s∨z = 0"), ("1011", "jover", "if v (table: v=0)"),
    ],
    "1402": [
        ("#", "Format I: op3 | addr1 24 | x y z | addr2/data 24 (9 units); x=1: opr1 indirect; yz: 00 dir, 01 ind, 10 data, 11 → II"),
        ("000", "mov opr1,opr2", "opr1 ← opr2"), ("001", "and", "opr1 ← (opr1)∧opr2"), ("010", "or", "∨"), ("011", "xor", "⊕"),
        ("100", "sub", "opr1 ← (opr1)−opr2"), ("101", "add", "opr1 ← (opr1)+opr2"),
        ("#", "Format II: op3 | address 24 | x 1 1 (5 units)"),
        ("110 x=0", "jz address", "if z=1: PC ← address"), ("110 x=1", "jnz", "if z=0"), ("111 x=0", "jneg", "if s=1"), ("111 x=1", "jmp", "PC ← address"),
    ],
}

MACHINES.update({
    "1398": dict(cls=M1398, title="ماشین میان‌ترم ۱۳۹۸", table=lambda: split_table(EXAM_TABLES["1398"]),
                 spec="<span class=m>2<sup>29</sup></span> کلمهٔ ۳۲ بیتی با واحد ۴ بیتی (<span class=m>2<sup>32</sup></span> واحد)؛ R0..R15 و <b>R0 همیشه صفر</b>؛ ثباتی مستقیم، بی‌واسطه و شاخص‌دار؛ مکمل دو و IEEE 754 تک‌دقتی.",
                 regs="MAR = PC = 32، MBR = 32، IR = 48، R0..R15 = 32 بیت.",
                 formats=[("I (۱۰ واحد)", [("0000", 4), ("r", 4), ("data", 32)]), ("II (۳ واحد)", [("op", 4), ("r1", 4), ("r2", 4)]),
                          ("III (۱۲ واحد)", [("1111", 4), ("op", 4), ("r1", 4), ("r2", 4), ("addr", 32)])]),
    "1399": dict(cls=M1399, title="ماشین میان‌ترم ۱۳۹۹", table=lambda: split_table(EXAM_TABLES["1399"]),
                 spec="<span class=m>2<sup>24</sup></span> واحد ۶ بیتی، کلمه ۲۴ بیت (۴ واحد)؛ R0..R31 و آدرس بازگشت OS در R31؛ ثباتی و حافظه‌ای (مستقیم و غیرمستقیم) و بی‌واسطه؛ مکمل دو.",
                 regs="MAR = PC = 24، MBR = 24، IR = 36، R0..R31 = 24 بیت.",
                 formats=[("I (۳ واحد)", [("00", 2), ("op", 4), ("i1 r1", 6), ("i2 r2 / q", 6)]), ("II (۲ واحد)", [("010", 3), ("op", 4), ("r", 5)]),
                          ("III (۶ واحد)", [("011", 3), ("op", 4), ("r", 5), ("addr", 24)]), ("V (۵ واحد)", [("1", 1), ("r", 5), ("data", 24)])]),
    "1400": dict(cls=M1400, title="ماشین میان‌ترم ۱۴۰۰", table=lambda: split_table(EXAM_TABLES["1400"]),
                 spec="<span class=m>2<sup>14</sup></span> کلمهٔ ۱۶ بیتی با واحد ۴ بیتی (<span class=m>2<sup>16</sup></span> واحد)؛ مستقیم، غیرمستقیم و بی‌واسطه؛ مکمل دو؛ بدون ثبات و پرچم.",
                 regs="MAR = PC = 16، MBR = 16، IR = 52 بیت.",
                 formats=[("I (۹ واحد)", [("op", 3), ("addr1", 16), ("d", 1), ("addr2/data", 16)]), ("II (۵ واحد)", [("op", 3), ("addr1", 16), ("x", 1)]),
                          ("III (۱۳ واحد)", [("op", 3), ("addr1", 16), ("d", 1), ("addr2/data", 16), ("addr3", 16)])]),
    "1401": dict(cls=M1401, title="ماشین میان‌ترم ۱۴۰۱", table=lambda: split_table(EXAM_TABLES["1401"]),
                 spec="<span class=m>2<sup>21</sup></span> واحد ۷ بیتی، کلمه ۲۱ بیت (۳ واحد)؛ مستقیم، غیرمستقیم و بی‌واسطه؛ مکمل دو؛ PSR = z s v.",
                 regs="MAR = PC = 21، MBR = 21، IR = 49، PSR = 3 بیت.",
                 formats=[("I (۷ واحد)", [("op", 4), ("i", 1), ("addr1", 21), ("xy", 2), ("addr2/data", 21)]),
                          ("II (۴ واحد)", [("op", 4), ("i", 1), ("addr1", 21), ("11", 2)])]),
    "1402": dict(cls=M1402, title="ماشین میان‌ترم ۱۴۰۲", table=lambda: split_table(EXAM_TABLES["1402"]),
                 spec="<span class=m>2<sup>24</sup></span> واحد ۶ بیتی، کلمه ۲۴ بیت (۴ واحد)؛ مستقیم، غیرمستقیم و بی‌واسطه؛ مکمل دو؛ PSR = z s (فقط دستورهای حسابی/منطقی).",
                 regs="MAR = PC = 24، MBR = 24، IR = 54، PSR = 2 بیت.",
                 formats=[("I (۹ واحد)", [("op", 3), ("addr1", 24), ("xyz", 3), ("addr2/data", 24)]), ("II (۵ واحد)", [("op", 3), ("address", 24), ("x11", 3)])]),
})


def split_table(rows):
    """Two side-by-side opcode tables (split at a group boundary near the middle)."""
    if len(rows) <= 14:
        return CS.optable(rows)
    cut = len(rows) // 2
    for k in range(cut, len(rows)):
        if rows[k][0] != "#" and (k == 0 or rows[k - 1][0] != "#"):
            cut = k
            break
    left, right = rows[:cut], rows[cut:]
    if right and right[0][0] != "#":
        prev = [r for r in left if r[0] == "#"]
        if prev:
            right = [("#", prev[-1][1] + " (cont.)")] + right
    return f'<div class="two">{CS.optable(left)}{CS.optable(right)}</div>'


def lecture_table(gen):
    t = gen()
    rows = re.findall(r"<tr>.*?</tr>", t, re.S)
    if len(rows) <= 12:
        return t
    head = t[:t.index("<tbody>")]
    body = rows[1:] if "<th>Opcode" in rows[0] else rows
    half = (len(body) + 1) // 2
    while half < len(body) and 'colspan="3"' in body[half - 1]:
        half += 1
    a = head + "<tbody>" + "".join(body[:half]) + "</tbody></table>"
    b = head + "<tbody>" + "".join(body[half:]) + "</tbody></table>"
    return f'<div class="two">{a}{b}</div>'


# ====================================================================== programs
def P(pid, mkey, title, source, purpose, src=None, externals=(), result=None):
    return dict(pid=pid, m=mkey, title=title, source=source, purpose=purpose, src=src, ext=tuple(externals), result=result)


def lec(pid, mkey, title, source, purpose):
    cls, src, ext = LECTURE[pid]
    return P(pid, mkey, title, source, purpose, src, ext)


def pat(pid, title, purpose, ext=("OS",)):
    return P(pid, "1402", title, "برگهٔ الگوها", purpose, PROGRAMS[pid][1], ext)


SECTIONS = [
    ("بخش ۱: برنامه‌های جزوه و اسلایدها", [
        ("M1", [lec("m1_examples", "M1", "نمونه‌دستورهای ماشین ۱", "جزوه فصل ۲ (مثال ۲-۸ و تمرین ۲-۳)", "رمزگذاری و رمزگشایی دستورهای ۱۶ بیتی")]),
        ("M2", [lec("m2_fib7", "M2", "مجموع ۷ جملهٔ اول فیبوناچی", "جزوه مثال ۲-۱۰ (تمرین اسلاید)", "بدون پرش؛ حلقه کامل باز شده؛ t1 و t2 به نوبت جملهٔ جدید را می‌گیرند"),
                lec("m2_xorswap", "M2", "جابه‌جایی دو متغیر با XOR", "جزوه تمرین ۲-۴", "بدون متغیر کمکی"),
                lec("m2_expr", "M2", "محاسبهٔ r = 2(a+b) − c", "جزوه تمرین ۲-۵", "ضرب در ۲ با add r,r")]),
        ("M3", [lec("m3_altfib", "M3", "مجموع ۱۰۰ جملهٔ فیبوناچی متناوب", "جزوه فصل ۳ برنامهٔ ۱ (تمرین اسلاید)", "دو جمله در هر دور (+ و −)؛ ۵۰ دور؛ ثابت one چون بی‌واسطه نداریم"),
                lec("m3_arrsum", "M3", "جمع آرایهٔ ۱۰۰ کلمه‌ای (غیرمستقیم)", "جزوه فصل ۳ برنامهٔ ۲ (تمرین اسلاید)", "اشاره‌گر arrptr؛ شمارندهٔ ۲۰۰ با گام ۲. پس از حلقه PC به داده (0114h) می‌رسد؛ باید به OS برگشت"),
                lec("m3_selfmod", "M3", "جمع آرایه بدون غیرمستقیم (کد خودتغییرده)", "جزوه فصل ۳ برنامهٔ ۳ (پرسش اسلاید)", "فیلد addr2 دستور اول (بایت‌های loop+3..4) هر دور ۲ واحد جلو می‌رود")]),
        ("M4", [lec("m4_vecadd", "M4", "جمع دو بردار C = A + B", "جزوه فصل ۳ (تمرین اسلاید ماشین ۴)", "سه اشاره‌گر ثباتی و غیرمستقیم ثباتی؛ گام ۴ واحد")]),
        ("M5", [lec("m5_arrsum", "M5", "جمع آرایهٔ ۱۰۰ عنصری (شاخص‌دار)", "جزوه فصل ۳ (پرسش ۲ ماشین ۵)", "R1 شاخص، R0 انباره؛ بازگشت با call R0,0(R63)"),
                lec("m5_sumregs_straight", "M5", "جمع R0…R62 در R62 — کد خطی", "تکلیف ۱ ماشین ۵ (راه‌حل الف)", "۶۲ دستور add R62,Rk با کد 1F80h + k"),
                lec("m5_sumregs_loop", "M5", "جمع R0…R62 — حلقهٔ خودتغییرده", "تکلیف ۱ ماشین ۵ (راه‌حل ب)", "فیلد r2 دستور loop هر دور یکی زیاد می‌شود تا به کد 1FBDh برسد")]),
        ("1A", [lec("a1_fib20", "1A", "ساختن ۲۰ جملهٔ فیبوناچی در آرایه", "جزوه فصل ۳ (مثال اسلاید + تکلیف ۲)", "سه اشاره‌گر p1، p2، p3 و آدرس‌دهی غیرمستقیم")]),
        ("M6", [lec("m6_pushpop", "M6", "push و pop (مثال اسلاید) + add", "جزوه فصل ۳", "قطعه‌کد اسلاید؛ اجرا تا رسیدن به داده"),
                lec("m6_expr", "M6", "محاسبهٔ (a+b) − (c−d) روی پشته", "جزوه، تمرین نمادگذاری لهستانی", "عبارت پسوندی ab+cd−−"),
                lec("m6_fib_slide", "M6", "مجموع فیبوناچی روی پشته (برنامهٔ اسلاید)", "جزوه فصل ۳ (تکلیف ماشین ۶)", "ترفند pop x / sp++ برای کپی بالای پشته"),
                lec("m6_fib_better", "M6", "مجموع ۲۰ جملهٔ فیبوناچی — برنامهٔ بهتر", "جزوه فصل ۳ (تکلیف ماشین ۶)", "اتحاد ΣF<sub>0..n−1</sub> = F<sub>n+1</sub> − 1")]),
        ("M7", [lec("m7_gnome", "M7", "مرتب‌سازی Gnome با نگهبان (برنامهٔ اسلاید)", "جزوه فصل ۵ (تمرین اسلاید)", "نگهبان 80000000h قبل از آرایه؛ پرش‌های نسبی"),
                lec("m7_gnome_safe", "M7", "مرتب‌سازی Gnome بدون نگهبان", "جزوه فصل ۵ (اصلاح ب)", "در i = 0 عقب نمی‌رود؛ با هر عددی (بدون سرریز تفریق) درست است"),
                lec("m7_primes", "M7", "جمع ۱۰۰ عدد اول (غربال اراتستن)", "جزوه فصل ۵ (تکلیف)", "فقط جمع لازم است؛ پرش برگشت با jmpl چون از بازهٔ نسبی بیرون است")]),
    ]),
    ("بخش ۲: میان‌ترم‌های ۱۳۹۸ تا ۱۴۰۲", [
        ("1398", [P("q1398", "1398", "سؤال ۲: e<sup>x</sup> با دقت 2<sup>−10</sup>", "میان‌ترم ۱۳۹۸", "سری تیلور؛ ثابت‌ها با بیت‌های IEEE؛ x(R0) = آدرس مستقیم", PROGRAMS["q1398"][1], ("OS",)),
                  P("e1398", "1398", "سؤال ۳ و ۴: برنامهٔ امتحان", "میان‌ترم ۱۳۹۸", "اجرا از org 0 یعنی از روی «داده»", PROGRAMS["e1398"][1], ("OS_control_point",))]),
        ("1399", [P("q1399", "1399", "سؤال ۲: مرتب‌سازی صعودی ۱۰۰ کلمه", "میان‌ترم ۱۳۹۹", "Gnome با دستور swap و inc4/dec4", PROGRAMS["q1399"][1]),
                  P("e1399", "1399", "سؤال ۳ و ۴: برنامهٔ امتحان", "میان‌ترم ۱۳۹۹", "dw 41006h دستور است و loop-6 وسط دستور فرود می‌آید", PROGRAMS["e1399"][1])]),
        ("1400", [P("q1400", "1400", "سؤال ۲: مجموع ۱۰۰ جملهٔ فیبوناچی", "میان‌ترم ۱۴۰۰", "دو جمله در هر دور؛ پاسخ به پیمانهٔ 2<sup>16</sup>", PROGRAMS["q1400"][1]),
                  P("e1400", "1400", "سؤال ۳ و ۴: برنامهٔ امتحان (org 100h چاپ‌شده)", "میان‌ترم ۱۴۰۰", "۹ کلمهٔ Arr = ۴ دستور؛ کد خودتغییرده", PROGRAMS["e1400"][1])]),
        ("1401", [P("q1401_template", "1401", "سؤال ۲: تکمیل قالب مرتب‌سازی (Gnome با XOR)", "میان‌ترم ۱۴۰۱", "جاهای خالی قالب امتحان پر شده است", PROGRAMS["q1401_template"][1]),
                  P("q1401_safe", "1401", "سؤال ۲: نسخهٔ امن", "میان‌ترم ۱۴۰۱", "فقط وارونگی واقعی جابه‌جا می‌شود؛ با عددهای تکراری هم درست است", PROGRAMS["q1401_safe"][1]),
                  P("e1401", "1401", "سؤال ۳ و ۴: برنامهٔ امتحان (43Dh مستقیم، مطابق متن)", "میان‌ترم ۱۴۰۱", "XOR روی خود دستور", PROGRAMS["e1401"][1])]),
        ("1402", [P("q1402", "1402", "سؤال ۲: جمع متناوب پیشوندی", "میان‌ترم ۱۴۰۲", "A<sub>i</sub> = Σ<sub>j≤i</sub>(−1)<sup>j</sup>A<sub>j</sub>؛ دو عنصر در هر دور", PROGRAMS["q1402"][1], ("OS_Control_Point",)),
                  P("e1402", "1402", "سؤال ۳ و ۴: برنامهٔ امتحان", "میان‌ترم ۱۴۰۲", "برچسب‌های here±k و ماسک دوبرابرشونده", PROGRAMS["e1402"][1], ("OS_Control_Point",))]),
    ]),
    ("بخش ۳: الگوهای حل مسئله (ماشین ۱۴۰۲)", [
        ("1402*", [
            pat("swap_xor", "جابه‌جایی با XOR", "سه xor؛ a و b باید دو خانهٔ متفاوت باشند"),
            pat("swap_tmp", "جابه‌جایی با متغیر موقت", "سه mov"),
            pat("swap_ptr", "جابه‌جایی دو خانه از طریق اشاره‌گر", "xor با عملوندهای غیرمستقیم"),
            pat("zero_inc", "صفر کردن، ±۱ و تست مقدار", "sub #FFFFFFh = +1؛ add y,#0 فقط برای پرچم"),
            pat("count_loop", "حلقهٔ شمارشی", "sub n,#1 / jnz"),
            pat("arr_sum", "جمع آرایه با اشاره‌گر", "گام اشاره‌گر = ۴ واحد"),
            pat("arr_max", "بیشینهٔ آرایه", "مقایسه = تفریق در متغیر موقت"),
            pat("arr_count_neg", "شمارش عناصر منفی", "mov t,#0 / or t,(p) = بار کردن + پرچم"),
            pat("reverse", "وارونه کردن آرایه با دو اشاره‌گر", "تا برخورد اشاره‌گرها"),
            pat("prefix", "جمع پیشوندی", "A[i] = A[0] + … + A[i]"),
            pat("altsum", "جمع متناوب پیشوندی", "باز کردن حلقه به اندازهٔ ۲"),
            pat("fib_sum", "مجموع ۱۰۰ جملهٔ فیبوناچی", "a += b; b += a"),
            pat("fib_fill", "ساختن فیبوناچی در آرایه", "یک اشاره‌گر که عقب و جلو می‌رود"),
            pat("mul_add", "ضرب با جمع‌های متوالی", "b بار a را جمع می‌کند"),
            pat("mul_shift", "ضرب با شیفت و جمع", "ماسک دوبرابرشونده تا سرریز"),
            pat("divmod", "تقسیم و باقی‌مانده", "تفریق‌های متوالی"),
            pat("popcount", "شمارش بیت‌های ۱", "and با ماسک و پرچم z"),
            pat("pow2", "تشخیص توان ۲", "x and (x−1) = 0"),
            pat("abs", "قدر مطلق", "−x = not(x) + 1"),
            pat("max2", "بیشینهٔ دو عدد", "تفریق و پرش روی علامت"),
            pat("gnome", "مرتب‌سازی Gnome", "یک حلقه؛ «≥» یعنی مرتب"),
            pat("bubble", "مرتب‌سازی حبابی", "دو حلقه"),
            pat("selfmod_walk", "پیمایش آرایه با تغییر فیلد آدرس", "add loop+5,#4 روی فیلد addr2"),
            pat("toggle", "دستور «چشمک‌زن» با XOR", "داده بین ۱ و ۰ جابه‌جا می‌شود"),
        ]),
    ]),
]

PATTERN_RESULTS = {
    "swap_xor": "a = ABCDEh، b = 1234h", "swap_tmp": "a = 9، b = 5", "swap_ptr": "x = 3، y = 7",
    "zero_inc": "x = 0 و flag = 1 (y منفی)", "count_loop": "sum = 55", "arr_sum": "مجموع ۱۰۰ عدد تصادفی درست",
    "arr_max": "بیشینه درست", "arr_count_neg": "تعداد منفی‌ها درست", "reverse": "آرایه وارونه شد",
    "prefix": "جمع‌های پیشوندی درست", "altsum": "جمع‌های متناوب درست", "fib_sum": "مجموع ۱۰۰ جمله به پیمانهٔ 2^24",
    "fib_fill": "A = ۱۰۰ جملهٔ فیبوناچی (پیمانهٔ 2^24)", "mul_add": "r = −7 × 12 = −84", "mul_shift": "r = 1234 × 567 = 699678",
    "divmod": "100 / 7 ⇒ q = 14، x = 2", "popcount": "0B5A3h ⇒ cnt = 9", "pow2": "4096 ⇒ 1 و 4095 ⇒ 0",
    "abs": "x = 37", "max2": "mx = 9", "gnome": "مرتب شد (عددهای تکراری)", "bubble": "مرتب شد (عددهای تکراری)",
    "selfmod_walk": "مجموع درست", "toggle": "x = 5 بعد از ۱۰ دور",
    "q1402": "جمع‌های متناوب ۱۰۰ عدد تصادفی درست", "q1401_template": "۱۰۰ عدد متمایز بزرگ‌تر از ‎−9 مرتب شد (با عددهای برابر بی‌پایان است)",
    "q1401_safe": "مرتب شد (عددهای تکراری)", "q1400": "sum = مجموع ۱۰۰ جمله به پیمانهٔ 2^16", "q1399": "مرتب شد (عددهای تکراری)",
    "q1398": "برای x = −6 تا 7 خطا کمتر از 2^−10 (بیشترین ≈ 1.4×10^−4)",
}


# ====================================================================== listing
def unit_text(m, bits, limit=None):
    u = m.unit
    us = [bits[i:i + u] for i in range(0, len(bits), u)]
    more = limit is not None and len(us) > limit
    if more:
        us = us[:limit]
    if u == 4:
        t = "".join("?" if "?" in x else "%X" % int(x, 2) for x in us)
    elif u == 8:
        t = " ".join("??" if "?" in x else "%02X" % int(x, 2) for x in us)
    elif u == 6:
        t = " ".join("??" if "?" in x else "%02o" % int(x, 2) for x in us)
    elif u == 7:
        t = " ".join("??" if "?" in x else "%02X" % int(x, 2) for x in us)
    else:
        t = " ".join("????" if "?" in x else "%04X" % int(x, 2) for x in us)
    return t + (" …" if more else "")


def field_html(bits, widths):
    out, k = [], 0
    for w in widths:
        fb = bits[k:k + w]
        k += w
        if w >= 12:
            d = (w + 3) // 4
            txt = "?" * d if "?" in fb else "%0*X" % (d, int(fb, 2))
            out.append(f'<span class="fh">{txt}<small>h</small></span>')
        else:
            out.append(f'<span class="fb">{fb}</span>')
    return " ".join(out)


def dw_fields(m, bits):
    w = m.unit * m.word_units
    words = [bits[i:i + w] for i in range(0, len(bits), w)]
    d = (w + 3) // 4
    show = ["?" * d if "?" in x else "%0*X" % (d, int(x, 2)) for x in words[:3]]
    txt = " ".join(f'<span class="fh">{t}<small>h</small></span>' for t in show)
    if len(words) > 3:
        txt += f' <span class="more">… ×{len(words)}</span>'
    return txt


def comment_html(c):
    c = c.strip()
    if not c:
        return '<td class="cm"></td>'
    if re.search(r"[؀-ۿ]", c):
        return f'<td class="cm fa">{JZ.wrap_ltr(html.escape(c))}</td>'
    return f'<td class="cm en">{html.escape(c)}</td>'


def instr_text(raw):
    code = raw.split(";")[0].strip()
    code = re.sub(r"^[A-Za-z_]\w*\s*:\s*", "", code)
    parts = code.split(None, 1)
    if not parts:
        return ""
    return html.escape(parts[0].ljust(6) + " " + (parts[1].strip() if len(parts) > 1 else ""))


def listing(entry):
    mdef = MACHINES[entry["m"]]
    m = mdef["cls"]()
    img, lst = m.assemble(entry["src"], externals=entry["ext"])
    rows = []
    it = iter(lst)
    code_units = data_units = 0
    dg = getattr(m, "addr_digits", 4)
    for label, mnem, ops, raw in parse(entry["src"]):
        comment = raw.split(";", 1)[1] if ";" in raw else ""
        lab = html.escape(label + ":") if label else ""
        if mnem in ("org", "end", None):
            rows.append(f'<tr class="dir"><td class="ad"></td><td class="mc"></td><td class="fd"></td>'
                        f'<td class="lb">{lab}</td><td class="in">{instr_text(raw)}</td>{comment_html(comment)}</tr>')
            continue
        addr, _, mn, op, _, bits = next(it)
        n = len(bits) // m.unit
        if mn == "dw":
            data_units += n
            fd = dw_fields(m, bits)
            mc = unit_text(m, bits, limit=12 if m.unit == 4 else 8)
            cls = ' class="data"'
        else:
            code_units += n
            fd = field_html(bits, m.widths(mn, op, bits))
            mc = unit_text(m, bits)
            cls = ""
        rows.append(f'<tr{cls}><td class="ad">{addr:0{dg}X}</td><td class="mc">{mc}</td><td class="fd">{fd}</td>'
                    f'<td class="lb">{lab}</td><td class="in">{instr_text(raw)}</td>{comment_html(comment)}</tr>')
    head = ('<thead><tr><th class="ad">Addr</th><th class="mc">Machine code</th><th class="fd">Fields (instruction format)</th>'
            '<th class="lb">Label</th><th class="in">Assembly</th><th class="cm">توضیح</th></tr></thead>')
    syms = ", ".join(f"{k} = {v:X}h" for k, v in m.sym.items())
    ext = "، ".join(entry["ext"])
    return (f'<table class="lst">{head}<tbody>{"".join(rows)}</tbody></table>',
            code_units, data_units, syms, ext, m.unit)


# ====================================================================== document
def machine_card(key):
    d = MACHINES[key]
    fm = "".join(f'<div class="fmtrow"><b>{name}</b> {fmt(fields)}</div>' for name, fields in d["formats"])
    table = lecture_table(d["table"]) if key in ("M1", "M2", "M3", "M4", "M5", "1A", "M6", "M7") else d["table"]()
    return (f'<div class="mcard"><p class="spec">{d["spec"]} <span class="regs">طول ثبات‌ها: {d["regs"]}</span></p>'
            f'<div class="fmts">{fm}</div>{table}</div>')


def build_doc(results, pages=None, markers=False):
    out, toc_rows, n_prog, n_sec = [], [], 0, 0
    for part, groups in SECTIONS:
        out.append(f'<h1 class="part">{part}</h1>')
        for key, progs in groups:
            pattern_part = key.endswith("*")
            key = key.rstrip("*")
            n_sec += 1
            sid = f"s{n_sec}"
            mk = f'<span class="mk">QQS{n_sec:02d}QQ</span>' if markers else ""
            title = "الگوهای حل مسئله روی ماشین ۱۴۰۲" if pattern_part else MACHINES[key]["title"]
            out.append(f'<h2 id="{sid}"><span class="mtag">{html.escape(key)}</span>{title}{mk}</h2>')
            out.append(machine_card(key) if not pattern_part else
                       '<p class="note">قالب‌ها و کد عمل‌ها همان ماشین میان‌ترم ۱۴۰۲ است (بخش ۲). در این برنامه‌ها <code>OS</code> نشانی بازگشت به سیستم‌عامل است و نامعلوم (؟) نوشته شده.</p>')
            toc_rows.append(("sec", sid, f"{key} — {re.sub('<[^>]+>', '', title)}"))
            for e in progs:
                n_prog += 1
                pid = f"p{n_prog}"
                mkp = f'<span class="mk">QQP{n_prog:02d}QQ</span>' if markers else ""
                tbl, cu, du, syms, ext, unit = listing(e)
                res = results.get(e["pid"]) or PATTERN_RESULTS.get(e["pid"], "")
                foot = f'<b>اندازه:</b> کد {fa(cu)} واحد، داده {fa(du)} واحد (واحد = {fa(unit)} بیت)'
                if syms:
                    foot += f' · <b>نمادها:</b> <span class="mw">{html.escape(syms)}</span>'
                if ext:
                    foot += f' · <b>نماد بیرونی (؟):</b> <span class="mw">{html.escape(ext)}</span>'
                out.append(
                    f'<section class="prog" id="{pid}"><h3><span class="num">{fa(n_prog)}</span>{e["title"]}'
                    f'<span class="mtag sm">{html.escape(e["m"])}</span>{mkp}</h3>'
                    f'<p class="pmeta"><span class="src">{e["source"]}</span> — {e["purpose"]}</p>'
                    f'{tbl}<p class="pfoot">{foot}</p>'
                    f'<p class="pres">✓ <b>آزموده با شبیه‌ساز:</b> {res}</p></section>')
                toc_rows.append(("prog", pid, f'{re.sub("<[^>]+>", "", e["title"])}', e["source"], e["m"], n_prog))
    # index
    idx = ['<table class="idx"><thead><tr><th>#</th><th>برنامه</th><th>ماشین</th><th>منبع</th><th>ص</th></tr></thead><tbody>']
    for r in toc_rows:
        pg = fa(pages.get(r[1], "")) if pages else "۰"
        if r[0] == "sec":
            idx.append(f'<tr class="sec"><td colspan="4"><a href="#{r[1]}">{html.escape(r[2])}</a></td><td>{pg}</td></tr>')
        else:
            idx.append(f'<tr><td>{fa(r[5])}</td><td><a href="#{r[1]}">{html.escape(r[2])}</a></td><td class="mw">{html.escape(r[4])}</td>'
                       f'<td>{r[3]}</td><td>{pg}</td></tr>')
    idx.append("</tbody></table>")
    intro = (ROOT / "intro.html").read_text(encoding="utf-8").replace("<!--INDEX-->", "".join(idx))
    intro = intro.replace("{{NPROG}}", fa(n_prog))
    doc = ('<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
           '<title>کاتالوگ برنامه‌ها — ساختار و زبان کامپیوتر</title><link rel="stylesheet" href="style.css"></head><body>'
           + intro + "".join(out) + "</body></html>")
    OUT_HTML.write_text(doc, encoding="utf-8")
    return n_prog


def render(pdf):
    subprocess.run(["node", str(RENDER), str(OUT_HTML), str(pdf)], check=True)


def page_numbers(pdf):
    txt = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    res = {}
    for pno, page in enumerate(txt.split("\f"), start=1):
        for mm in re.finditer(r"QQ([SP])(\d\d)QQ", page):
            res.setdefault(f"{mm.group(1).lower()}{int(mm.group(2))}", pno)
    return res


if __name__ == "__main__":
    run_all()
    results = {}
    results.update(run_lecture())
    results.update(run_exam_q3())
    check_jozveh()
    build_doc(results, markers=True)
    tmp = ROOT / "_pass1.pdf"
    render(tmp)
    pages = page_numbers(tmp)
    n = build_doc(results, pages, markers=True)
    render(OUT_PDF)
    tmp.unlink(missing_ok=True)
    print("built", OUT_PDF, "programs:", n)
