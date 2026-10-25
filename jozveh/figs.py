"""Inline SVG figures for the booklet (all labels kept simple; drawn LTR)."""
import itertools

_ids = itertools.count(1)

BLUE = "#34507f"
FILL = "#eef4fd"
RED = "#c0392b"
GREEN = "#1d7a4c"
GREY = "#f3f5f9"


class S:
    def __init__(self, w, h, cap=None):
        self.w, self.h, self.cap = w, h, cap
        self.id = f"f{next(_ids)}"
        self.el = []

    def marker(self, color):
        return f"{self.id}{color.strip('#')}"

    def rect(self, x, y, w, h, fill=FILL, stroke=BLUE, rx=5, sw=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.el.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def text(self, x, y, t, size=13, anchor="middle", color="#1d2433", weight=400, family="Vazirmatn", rot=None):
        tr = f' transform="rotate({rot} {x} {y})"' if rot is not None else ""
        self.el.append(
            f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}" '
            f'font-weight="{weight}" font-family="{family}" dominant-baseline="middle"{tr}>{t}</text>'
        )

    def box(self, x, y, w, h, label, size=13, fill=FILL, stroke=BLUE, weight=500, color="#1d2433", sub=None):
        self.rect(x, y, w, h, fill, stroke)
        if sub:
            self.text(x + w / 2, y + h / 2 - 7, label, size, weight=weight, color=color)
            self.text(x + w / 2, y + h / 2 + 10, sub, size - 3, color="#5b6475")
        else:
            self.text(x + w / 2, y + h / 2 + 1, label, size, weight=weight, color=color)

    def line(self, pts, color=BLUE, sw=1.6, end=True, start=False, dash=None):
        mid = self.marker(color)
        p = " ".join(f"{x},{y}" for x, y in pts)
        me = f' marker-end="url(#{mid})"' if end else ""
        ms = f' marker-start="url(#{mid}s)"' if start else ""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.el.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{sw}"{me}{ms}{d}/>')
        self._need = getattr(self, "_need", set())
        self._need.add(color)

    def arrow(self, x1, y1, x2, y2, **kw):
        self.line([(x1, y1), (x2, y2)], **kw)

    def fat(self, x1, y1, x2, y2, color="#c9d6ea", stroke=BLUE, both=True, w=14):
        """Fat double arrow (bus)."""
        import math

        ang = math.atan2(y2 - y1, x2 - x1)
        L = math.hypot(x2 - x1, y2 - y1)
        hw, hl = w / 2, 12
        pts = []
        if both:
            shape = [(0, 0), (hl, -hw - 5), (hl, -hw), (L - hl, -hw), (L - hl, -hw - 5), (L, 0),
                     (L - hl, hw + 5), (L - hl, hw), (hl, hw), (hl, hw + 5)]
        else:
            shape = [(0, -hw), (L - hl, -hw), (L - hl, -hw - 5), (L, 0), (L - hl, hw + 5), (L - hl, hw), (0, hw)]
        for px, py in shape:
            pts.append((x1 + px * math.cos(ang) - py * math.sin(ang), y1 + px * math.sin(ang) + py * math.cos(ang)))
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.el.append(f'<polygon points="{p}" fill="{color}" stroke="{stroke}" stroke-width="1.1"/>')

    def raw(self, s):
        self.el.append(s)

    def svg(self):
        defs = ""
        for c in getattr(self, "_need", set()):
            mid = self.marker(c)
            defs += (
                f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
                f'<marker id="{mid}s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
            )
        s = (
            f'<svg viewBox="0 0 {self.w} {self.h}" width="{self.w}" xmlns="http://www.w3.org/2000/svg" direction="ltr">'
            f"<defs>{defs}</defs>" + "".join(self.el) + "</svg>"
        )
        cap = f"<figcaption>{self.cap}</figcaption>" if self.cap else ""
        return f"<figure>{s}{cap}</figure>"


# ------------------------------------------------------------------ chapter 1
def vonneumann():
    s = S(520, 230, "شکل: ساختار کامپیوتر با برنامهٔ ذخیره‌شده (مدل فون‌نویمان)")
    s.rect(130, 10, 260, 210, GREY, "#8892a6")
    s.text(260, 205, "COMPUTER", 12, weight=700, color="#5b6475")
    s.box(200, 22, 120, 44, "MEMORY", 13, fill="#fff3c4", stroke="#b38f00", weight=700)
    s.rect(150, 96, 220, 92, "#fde0d6", "#b5523b")
    s.text(260, 110, "CPU", 13, weight=700)
    s.box(160, 124, 95, 52, "CONTROL UNIT", 11, fill="#c9f0c4", stroke="#3c8a34", weight=700)
    s.box(265, 124, 95, 52, "ALU", 12, fill="#c9f0c4", stroke="#3c8a34", weight=700, sub="Arithmetic/Logic")
    s.arrow(245, 66, 245, 96)
    s.arrow(275, 96, 275, 66)
    s.box(20, 126, 80, 40, "INPUT", 12, fill="#eee", stroke="#777")
    s.box(420, 126, 80, 40, "OUTPUT", 12, fill="#eee", stroke="#777")
    s.arrow(100, 146, 150, 146)
    s.arrow(370, 146, 420, 146)
    return s.svg()


def _flynn_base(s, cu_y):
    s.box(20, cu_y, 70, 46, "CU", 16)


def sisd():
    s = S(460, 150, "SISD: یک جریان دستور و یک جریان داده (همان ساختار پایهٔ فون‌نویمان)")
    s.box(20, 30, 80, 50, "CU", 17)
    s.box(190, 30, 80, 50, "PU", 17)
    s.box(360, 30, 80, 50, "MU", 17)
    s.arrow(100, 55, 190, 55, color=RED)
    s.text(145, 45, "IS", 11, color=RED, weight=700)
    s.line([(270, 55), (360, 55)], color=GREEN, start=True)
    s.text(315, 45, "DS", 11, color=GREEN, weight=700)
    s.line([(400, 80), (400, 115), (60, 115), (60, 80)], color=RED)
    s.text(230, 128, "IS", 11, color=RED, weight=700)
    return s.svg()


def simd():
    s = S(460, 230, "SIMD: یک جریان دستور، چند جریان داده (پردازنده‌های برداری و بیشتر ابررایانه‌های اولیه)")
    s.box(20, 85, 80, 50, "CU", 17)
    ys = [20, 80, 160]
    for i, y in enumerate(ys):
        lab = ["PU₁", "PU₂", "PUₙ"][i]
        s.box(200, y, 70, 42, lab, 15)
        s.line([(150, 110), (150, y + 21), (200, y + 21)], color=RED)
        s.line([(270, y + 21), (340, y + 21)], color=GREEN, start=True)
        s.text(305, y + 11, ["DS₁", "DS₂", "DSₙ"][i], 10, color=GREEN, weight=700)
    s.text(235, 140, "⋮", 18)
    s.arrow(100, 110, 150, 110, color=RED, end=False)
    s.text(125, 100, "IS", 11, color=RED, weight=700)
    s.box(340, 15, 80, 195, "MU", 17)
    s.line([(380, 210), (380, 222), (60, 222), (60, 135)], color=RED)
    return s.svg()


def misd():
    s = S(480, 250, "MISD: چند جریان دستور روی یک جریان داده (ساختارهای خط لوله‌ای / آرایه‌های سیستولیک)")
    s.box(20, 95, 80, 50, "CU", 17)
    s.rect(190, 15, 110, 200, GREY, "#9aa3b5")
    s.text(285, 160, "PU", 14, weight=700)
    ys = [30, 90, 165]
    labs = ["Sub PU₁", "Sub PU₂", "Sub PUₘ"]
    for i, y in enumerate(ys):
        s.box(205, y, 70, 38, labs[i], 11)
        s.line([(140, 120), (140, y + 19), (205, y + 19)], color=RED)
        s.text(172, y + 9, ["IS₁", "IS₂", "ISₘ"][i], 10, color=RED, weight=700)
    s.arrow(240, 68, 240, 90, color=GREEN)
    s.arrow(240, 128, 240, 150, color=GREEN)
    s.text(240, 140, "⋮", 14)
    s.arrow(100, 120, 140, 120, color=RED, end=False)
    s.box(370, 80, 80, 80, "MU", 17)
    s.line([(410, 80), (410, 8), (240, 8), (240, 30)], color=GREEN)
    s.line([(240, 203), (240, 225), (420, 225), (420, 160)], color=GREEN)
    s.text(330, 18, "DS", 10, color=GREEN, weight=700)
    s.line([(395, 160), (395, 240), (60, 240), (60, 145)], color=RED)
    return s.svg()


def mimd():
    s = S(500, 250, "MIMD: چند جریان دستور و چند جریان داده (چندکامپیوتری؛ تقریباً همهٔ ابررایانه‌های امروزی)")
    ys = [15, 75, 165]
    for i, y in enumerate(ys):
        k = ["₁", "₂", "ₙ"][i]
        s.rect(60, y - 5, 420, 52, "#eef8e8", "#b7d9a8")
        s.box(80, y, 60, 42, "CU" + k, 14)
        s.box(190, y, 60, 42, "PU" + k, 14)
        s.box(300, y, 70, 42, "Sub MU" + k, 11, fill="#dde3ec")
        s.text(430, y + 21, "Computer" + k, 12, color=GREEN, weight=700)
        s.arrow(140, y + 21, 190, y + 21, color=RED)
        s.line([(250, y + 21), (300, y + 21)], color=GREEN, start=True)
        s.line([(335, y + 42), (335, 230 - 4 * i), (30 + 10 * i, 230 - 4 * i), (30 + 10 * i, y + 21), (80, y + 21)], color=RED, sw=1.2)
    s.text(110, 140, "⋮", 18)
    s.text(220, 140, "⋮", 18)
    s.text(335, 140, "⋮", 18)
    return s.svg()


# ------------------------------------------------------------------ chapter 2
def computer_system():
    s = S(440, 230, "شکل: اجزای اصلی یک سیستم کامپیوتری در مدل فون‌نویمان")
    s.rect(30, 15, 140, 120, "#fff", BLUE)
    s.text(100, 32, "CPU", 14, weight=700)
    s.box(45, 50, 50, 70, "CU", 13)
    s.box(105, 50, 50, 70, "ALU", 13)
    s.box(270, 25, 130, 100, "Main Memory", 14, weight=700)
    s.fat(172, 75, 268, 75)
    s.box(70, 180, 330, 40, "Input / Output (I/O) Devices", 13, weight=700)
    s.fat(100, 137, 100, 178)
    s.fat(335, 127, 335, 178)
    return s.svg()


def memory_generic():
    s = S(470, 260, "شکل: دسترسی به حافظه از طریق MAR، رمزگشا (Decoder) و MBR")
    s.rect(30, 90, 34, 80, "#fff", BLUE)
    s.text(47, 185, "MAR", 12, weight=700)
    s.fat(66, 130, 120, 130, both=False)
    s.raw(f'<polygon points="122,40 152,55 152,205 122,220" fill="{FILL}" stroke="{BLUE}" stroke-width="1.4"/>')
    s.text(137, 130, "DECODER", 11, weight=700, rot=90)
    rows = [("0", 50), ("1", 70), ("M-2", 180), ("M-1", 200)]
    s.rect(230, 40, 110, 170, "#fff", BLUE, rx=0)
    for lab, y in rows:
        s.arrow(152, y, 230, y, sw=1)
        s.text(190, y - 7, lab, 9.5, color="#1f5fbf")
        s.raw(f'<line x1="230" y1="{y+10}" x2="340" y2="{y+10}" stroke="{BLUE}" stroke-width="1"/>')
    s.text(285, 125, "⋮", 18)
    s.arrow(400, 90, 342, 90)
    s.text(420, 90, "read", 11, anchor="start")
    s.arrow(400, 140, 342, 140)
    s.text(420, 140, "write", 11, anchor="start")
    s.fat(285, 212, 285, 236)
    s.rect(235, 238, 100, 18, "#fff", BLUE, rx=2)
    s.text(375, 247, "MBR", 12, weight=700)
    return s.svg()


def mem16(contents, mar=None, mbr=None, hl=None, cap=None, op=None):
    """16x16 memory with MAR (4 bits) / 4x16 decoder / MBR (16 bits)."""
    s = S(470, 330, cap)
    s.text(60, 45, "MAR", 12, weight=700)
    s.text(60, 60, "(4 bits)", 10, color="#5b6475")
    s.rect(45, 75, 30, 70, "#fff", BLUE)
    if mar is not None:
        s.text(60, 110, str(mar), 13, color=RED, weight=700)
    s.arrow(75, 110, 125, 110)
    s.text(100, 100, "4", 10)
    s.raw(f'<polygon points="125,20 160,38 160,292 125,310" fill="{FILL}" stroke="{BLUE}" stroke-width="1.4"/>')
    s.text(143, 165, "4x16 DECODER", 11, weight=700, rot=90)
    y0, rh = 30, 16.5
    for i in range(16):
        y = y0 + i * rh
        s.raw(f'<line x1="160" y1="{y+rh/2}" x2="250" y2="{y+rh/2}" stroke="{BLUE}" stroke-width=".8"/>')
        s.text(205, y + rh / 2 - 1, str(i), 10, color="#1f5fbf")
        fill = "#ffe3dc" if hl == i else "#fff"
        s.rect(250, y, 100, rh, fill, BLUE, rx=0, sw=1)
        s.text(300, y + rh / 2 + 1, str(contents[i]), 11, color=RED if hl == i else GREEN, weight=700 if hl == i else 400)
    s.arrow(410, 140, 352, 140)
    s.text(415, 140, "Read", 11, anchor="start", weight=700 if op == "r" else 400, color=RED if op == "r" else "#1d2433")
    s.arrow(410, 185, 352, 185)
    s.text(415, 185, "Write", 11, anchor="start", weight=700 if op == "w" else 400, color=RED if op == "w" else "#1d2433")
    s.line([(300, 295), (300, 300)], end=False)
    s.arrow(300, 297, 300, 302, start=True)
    s.rect(250, 304, 100, 20, "#fff", BLUE, rx=2)
    if mbr is not None:
        s.text(300, 314, str(mbr), 12, color=RED, weight=700)
    s.text(410, 314, "MBR (16 bits)", 10.5)
    return s.svg()


def banks(title_cap, cells=None, mark=None):
    """4-bank byte-addressable memory, 32-bit word, MAR 16 bits."""
    s = S(560, 270, title_cap)
    s.rect(28, 40, 26, 170, "#cfe8b8", "#5a8f3a", rx=2)
    s.text(41, 20, "MAR", 12, color=GREEN, weight=700)
    s.text(41, 32, "(16 bits)", 9.5, color=GREEN)
    s.raw('<line x1="28" y1="185" x2="54" y2="185" stroke="#5a8f3a" stroke-width="1.4"/>')
    s.arrow(54, 110, 100, 110)
    s.text(78, 95, "14 MSBs", 9.5)
    s.raw(f'<polygon points="100,45 125,58 125,200 100,213" fill="{FILL}" stroke="{BLUE}" stroke-width="1.3"/>')
    s.text(112, 130, "14-DEC", 10, weight=700, rot=90)
    s.line([(54, 197), (80, 197), (80, 232)], color="#5a8f3a")
    s.text(85, 240, "2 LSBs → Bank Select (00,01,10,11)", 9.5, anchor="start")
    rows_y = [60, 78, 96, 175]
    for b in range(4):
        x = 150 + b * 95
        s.text(x + 37, 45, f"Bank {b}", 11, weight=700)
        s.rect(x, 52, 75, 140, "#fff", BLUE, rx=0, sw=1.1)
        for r, y in enumerate(rows_y):
            s.raw(f'<line x1="{x}" y1="{y+9}" x2="{x+75}" y2="{y+9}" stroke="{BLUE}" stroke-width=".7"/>')
            if cells:
                lab = cells[r][b]
            else:
                lab = ["0", "4", "8", "2¹⁶-4"][r]
                lab = str(int(lab) + b) if r < 3 else f"2¹⁶-{4-b}"
            col = "#1f5fbf"
            if mark and (r, b) in mark:
                s.rect(x + 1, y - 8, 73, 17, "#ffe3dc", "none", rx=0)
                col = RED
            s.text(x + 37, y + 1, lab, 10, color=col, weight=700 if mark and (r, b) in mark else 400)
        s.text(x + 37, 140, "⋮", 14)
        s.line([(x + 37, 192), (x + 37, 212)], start=True)
        s.rect(x + 7, 214, 60, 16, "#cfe8b8", "#5a8f3a", rx=1)
    for r, y in enumerate(rows_y):
        s.arrow(125, y, 150, y, sw=0.8)
    s.text(530, 60, "Word 0", 9.5)
    s.text(530, 78, "Word 1", 9.5)
    s.text(530, 96, "Word 2", 9.5)
    s.text(530, 175, "Word 2¹⁴-1", 9.5)
    s.text(340, 250, "MBR (32 bits)", 11, color=GREEN, weight=700)
    return s.svg()


def internal_paths():
    s = S(420, 250, "شکل: مسیرهای داخلی ماشین")
    s.rect(40, 30, 130, 140, "#fff", BLUE)
    s.text(105, 20, "CPU", 13, weight=700)
    s.box(55, 45, 80, 40, "ALU", 13)
    s.box(55, 115, 80, 40, "CU", 13)
    s.box(270, 40, 120, 120, "Main Memory", 13, weight=700)
    s.fat(137, 62, 268, 62, color="#e4dca6")
    s.text(205, 62, "2", 11, weight=700)
    s.fat(268, 135, 137, 135, color="#f5c6c2", both=False)
    s.text(205, 135, "1", 11, weight=700)
    s.fat(70, 113, 70, 87, color="#7fa7ff", both=True, w=8)
    s.text(60, 100, "3", 11, weight=700, anchor="end")
    s.fat(115, 113, 115, 87, color="#e4dca6", both=False, w=10)
    s.text(125, 100, "4", 11, weight=700, anchor="start")
    s.box(40, 205, 350, 36, "Input / Output (I/O) Devices", 12, weight=700)
    s.fat(95, 157, 95, 203, color="#9ed37a")
    s.text(105, 182, "5", 11, weight=700, anchor="start")
    s.fat(330, 162, 330, 203, color="#9ed37a")
    s.text(342, 182, "6 (DMA)", 10, weight=700, anchor="start")
    return s.svg()


def flow_boxes(items, cap, w=300):
    """Vertical flow: list of (kind, text) where kind in box/ell."""
    h = 20 + 52 * len(items)
    s = S(w + 40, h, cap)
    y = 10
    cx = (w + 40) / 2
    for i, (kind, t) in enumerate(items):
        if kind == "box":
            s.box(cx - 120, y, 240, 36, t, 12)
        else:
            s.raw(f'<ellipse cx="{cx}" cy="{y+18}" rx="80" ry="18" fill="#8d9aa8" stroke="#6b7785"/>')
            s.text(cx, y + 19, t, 12, color="#fff", weight=700)
        if i < len(items) - 1:
            s.arrow(cx, y + 36, cx, y + 52, color="#e0a100", sw=3)
        y += 52
    return s, cx


def prog_flow():
    s, cx = flow_boxes(
        [("box", "برنامهٔ مبدأ به زبان سطح بالا"), ("ell", "Compiler"), ("box", "برنامه به زبان اسمبلی"),
         ("ell", "Assembler"), ("box", "برنامه به زبان ماشین")],
        "شکل: روند تبدیل برنامه تا زبان ماشین (کامپایلر می‌تواند مستقیماً کد ماشین هم تولید کند)",
    )
    s.raw('<path d="M 250 80 C 330 100, 330 230, 255 262" fill="none" stroke="#6b3fa0" stroke-width="4"/>')
    s.raw('<polygon points="255,262 268,250 268,268" fill="#6b3fa0"/>')
    return s.svg()


# ------------------------------------------------------------------ chapter 3
def _ff(s, x, y, n, q_out=True):
    s.rect(x, y, 62, 50, "#fff", BLUE, rx=2)
    s.text(x + 31, y + 9, "D", 9)
    s.text(x + 31, y + 23, "D-FF", 11, weight=700)
    s.text(x + 31, y + 36, f"#{n}", 10)
    s.text(x + 55, y + 44, "Q", 8.5)
    s.raw(f'<polyline points="{x},{y+28} {x+7},{y+32} {x},{y+36}" fill="none" stroke="{BLUE}" stroke-width="1"/>')


def register(kind):
    caps = {
        "pipo": "ثبات ۴ بیتی PIPO (ورود موازی، خروج موازی)",
        "sipo": "ثبات ۴ بیتی SIPO (ورود سریال، خروج موازی) — ثبات انتقالی",
        "piso": "ثبات ۴ بیتی PISO (ورود موازی، خروج سریال) — با مالتی‌پلکسر Load/Shift",
        "siso": "ثبات ۴ بیتی SISO (ورود سریال، خروج سریال)",
    }
    s = S(520, 205, caps[kind])
    xs = [100, 200, 300, 400]
    y = 75
    for i, x in enumerate(xs):
        _ff(s, x, y, 3 - i)
    # clock
    s.raw(f'<line x1="60" y1="{y+32}" x2="{xs[-1]}" y2="{y+32}" stroke="#555" stroke-width="1" stroke-dasharray="3,2"/>')
    s.text(40, y + 32, "Clock", 10, weight=700)
    par_in = kind in ("pipo", "piso")
    par_out = kind in ("pipo", "sipo")
    for i, x in enumerate(xs):
        if par_in:
            if kind == "piso" and i > 0:
                s.raw(f'<polygon points="{x+16},{y-30} {x+46},{y-30} {x+40},{y-16} {x+22},{y-16}" fill="{FILL}" stroke="{BLUE}"/>')
                s.text(x + 31, y - 23, "MUX", 7.5)
                s.arrow(x + 40, y - 52, x + 40, y - 30, sw=1.1)
                s.text(x + 40, y - 60, f"I{3-i}", 11, weight=700)
                s.arrow(x + 31, y - 16, x + 31, y, sw=1.1)
                # previous Q into mux input 0
                px = xs[i - 1]
                s.line([(px + 62, y + 44), (px + 72, y + 44), (px + 72, y - 40), (x + 22, y - 40), (x + 22, y - 30)], sw=1)
            else:
                s.arrow(x + 31, y - 40, x + 31, y, sw=1.2)
                s.text(x + 31, y - 50, f"I{3-i}", 11, weight=700)
        if par_out:
            s.arrow(x + 50, y + 50, x + 50, y + 80, sw=1.2)
            s.text(x + 50, y + 92, f"O{3-i}", 11, weight=700)
        if not par_in and i > 0:
            px = xs[i - 1]
            s.line([(px + 62, y + 44), (px + 78, y + 44), (px + 78, y - 12), (x + 31, y - 12), (x + 31, y)], sw=1.1)
    if kind == "piso":
        s.text(40, y - 23, "Load/Shift'", 9, weight=700)
        s.raw(f'<line x1="70" y1="{y-23}" x2="{xs[-1]+20}" y2="{y-23}" stroke="#a33" stroke-width=".8" stroke-dasharray="2,2"/>')
    if not par_in:
        s.line([(30, y - 12), (xs[0] + 31, y - 12), (xs[0] + 31, y)], sw=1.2)
        s.text(30, y - 24, "Serial In", 10, anchor="start", weight=700)
    if not par_out:
        s.arrow(xs[-1] + 62, y + 44, xs[-1] + 110, y + 44, sw=1.2)
        s.text(xs[-1] + 86, y + 58, "Serial Out", 10, weight=700)
    return s.svg()


def regfile():
    s = S(520, 200, "شکل: ثبات‌های یکپارچه (Register File) در برابر ثبات‌های مجزا (Isolated)")
    s.text(120, 15, "Integrated (Register File)", 12, weight=700)
    s.fat(10, 100, 50, 100, both=False)
    s.text(30, 80, "Reg#", 10)
    s.raw(f'<polygon points="52,40 76,52 76,158 52,170" fill="{FILL}" stroke="{BLUE}"/>')
    s.text(64, 105, "DECODER", 9, rot=90, weight=700)
    s.rect(110, 35, 90, 130, "#fff", BLUE, rx=0)
    for i, (lab, y) in enumerate([("R0", 45), ("R1", 63), ("R k-1", 150)]):
        s.arrow(76, y, 110, y, sw=.8)
        s.text(155, y, lab, 10, color="#1f5fbf")
    s.text(155, 105, "⋮", 16)
    s.fat(155, 167, 155, 192)
    s.text(205, 185, "Data (one at a time)", 9.5, anchor="start")
    s.text(400, 15, "Isolated", 12, weight=700)
    for i, x in enumerate([300, 370, 460]):
        s.fat(x + 25, 30, x + 25, 72, both=False, w=10)
        s.rect(x, 74, 50, 26, "#fff", BLUE, rx=2)
        s.text(x + 25, 88, ["R0", "R1", "R k-1"][i], 10, color="#1f5fbf")
        s.fat(x + 25, 102, x + 25, 142, both=False, w=10)
    s.text(440, 88, "⋯", 16)
    s.text(395, 160, "Data In / Data Out (parallel access)", 9.5)
    return s.svg()


def asm_flow():
    s = S(560, 330, "شکل: روند اجرای یک برنامهٔ اسمبلی: اسمبلر ← پیونددهنده ← بارکننده")
    Y = "#e0a100"
    s.box(80, 10, 150, 38, "Assembly program", 11.5)
    s.raw('<ellipse cx="330" cy="29" rx="55" ry="17" fill="#8d9aa8"/>')
    s.text(330, 30, "Compiler", 11, color="#fff", weight=700)
    s.box(420, 12, 130, 34, "High-level program", 11)
    s.arrow(420, 29, 387, 29, color="#6b3fa0", sw=3)
    s.arrow(273, 29, 232, 29, color="#6b3fa0", sw=3)
    s.raw('<ellipse cx="155" cy="85" rx="60" ry="17" fill="#8d9aa8"/>')
    s.text(155, 86, "Assembler", 11, color="#fff", weight=700)
    s.arrow(155, 48, 155, 67, color=Y, sw=3)
    s.box(10, 125, 100, 38, "Listing file", 11)
    s.box(130, 120, 150, 46, "Object file:", 11, sub="machine language module")
    s.box(300, 120, 170, 46, "Object file:", 11, sub="library routines")
    s.arrow(130, 100, 70, 124, color=Y, sw=3)
    s.arrow(180, 100, 200, 119, color=Y, sw=3)
    s.raw('<ellipse cx="290" cy="200" rx="55" ry="17" fill="#8d9aa8"/>')
    s.text(290, 201, "Linker", 11, color="#fff", weight=700)
    s.arrow(215, 166, 250, 186, color=Y, sw=3)
    s.arrow(380, 166, 330, 186, color=Y, sw=3)
    s.box(160, 232, 260, 30, "Executable file: machine language program", 11)
    s.arrow(290, 217, 290, 231, color=Y, sw=3)
    s.raw('<ellipse cx="290" cy="290" rx="50" ry="15" fill="#8d9aa8"/>')
    s.text(290, 291, "Loader", 11, color="#fff", weight=700)
    s.arrow(290, 262, 290, 274, color=Y, sw=3)
    s.box(330, 300, 220, 26, "Program in main memory", 11)
    s.arrow(340, 291, 360, 299, color=Y, sw=2)
    return s.svg()


def linker_fig():
    s = S(540, 250, "شکل: کار پیونددهنده — ترکیب فایل‌های شیء و رفع ارجاع‌های حل‌نشده")
    s.text(85, 15, "Object file", 10.5, weight=700)
    s.rect(40, 25, 95, 140, "#fff", BLUE, rx=0)
    for i, t in enumerate(["main:", "  jal ???", "  ⋮", "  jal ???"]):
        s.text(48, 40 + 20 * i, t, 10, anchor="start", family="JBMono")
    s.raw(f'<line x1="40" y1="120" x2="135" y2="120" stroke="{BLUE}"/>')
    s.text(48, 135, "call, sub", 9.5, anchor="start", family="JBMono")
    s.text(48, 152, "call, printf", 9.5, anchor="start", family="JBMono")
    s.text(5, 130, "Relocation", 8.5, anchor="start")
    s.text(5, 142, "records", 8.5, anchor="start")
    s.text(220, 15, "Object file", 10.5, weight=700)
    s.rect(185, 25, 70, 55, "#fff", BLUE, rx=0)
    s.text(195, 40, "sub:", 10, anchor="start", family="JBMono")
    s.text(220, 60, "⋮", 12)
    s.text(220, 178, "C library", 10.5, weight=700)
    s.rect(185, 188, 70, 55, "#fff", BLUE, rx=0)
    s.text(195, 203, "printf:", 10, anchor="start", family="JBMono")
    s.text(220, 225, "⋮", 12)
    s.raw(f'<rect x="290" y="100" width="100" height="44" rx="22" fill="{FILL}" stroke="{BLUE}"/>')
    s.text(340, 123, "Linker", 12, weight=700)
    s.arrow(135, 120, 290, 122)
    s.arrow(230, 80, 310, 101)
    s.arrow(230, 188, 310, 143)
    s.text(470, 15, "Executable file", 10.5, weight=700)
    s.rect(420, 25, 105, 215, "#fff", BLUE, rx=0)
    for i, t in enumerate(["main:", "  jal printf", "  ⋮", "  jal sub", "printf:", "  ⋮", "sub:", "  ⋮"]):
        s.text(428, 42 + 25 * i, t, 10, anchor="start", family="JBMono")
    s.arrow(390, 122, 420, 122)
    return s.svg()


def stack(items, sp, cap=None, mem=None, n=16, w=330, extra=None):
    """Hardware stack drawing: items list bottom->top (strings), sp pointer value."""
    h = 40 + n * 17
    s = S(w, h, cap)
    x = w - 140
    for i in range(n):
        y = h - 25 - (i + 1) * 17
        s.rect(x, y, 100, 17, "#fff", BLUE, rx=0, sw=.8)
        s.text(x + 110, y + 9, str(i), 9, anchor="start", color=GREEN)
        if i < len(items) and items[i] is not None:
            stale = i >= sp
            s.text(x + 50, y + 9, items[i], 10 if len(items[i]) < 14 else 8, color="#9aa3b5" if stale else "#1f5fbf")
    s.text(x + 50, 10, "Stack", 13, weight=700)
    ysp = h - 25 - sp * 17
    s.rect(20, h - 70, 60, 22, "#fff", BLUE, rx=2)
    s.text(50, h - 59, str(sp), 12, color="#1f5fbf", weight=700)
    s.text(50, h - 38, "SP (4 bits)", 9.5)
    s.arrow(80, h - 59, x - 2, ysp, color="#1f5fbf", sw=1)
    if mem:
        s.rect(20, 25, 120, 60, GREY, "#8892a6")
        s.text(80, 38, "Main Memory", 10, weight=700)
        s.rect(45, 50, 70, 20, "#fff", BLUE, rx=0)
        s.text(80, 61, mem, 11, color=RED, weight=700)
        s.text(80, 78, "Num", 9)
    return s.svg()


def stack_row(states, cap):
    """Several small stack snapshots side by side: list of (title, items, sp)."""
    n = 6
    colw = 118
    s = S(colw * len(states) + 10, 60 + n * 17, cap)
    for k, (title, items, sp) in enumerate(states):
        x = 10 + k * colw
        s.text(x + 50, 12, title, 10.5, weight=700, family="JBMono")
        for i in range(n):
            y = 40 + (n - 1 - i) * 17
            s.rect(x + 10, y, 80, 17, "#fff", BLUE, rx=0, sw=.8)
            s.text(x + 96, y + 9, str(i), 8, anchor="start", color=GREEN)
            if i < len(items) and items[i] is not None:
                s.text(x + 50, y + 9, items[i], 9.5, color="#9aa3b5" if i >= sp else "#1f5fbf",
                       weight=400 if i >= sp else 700)
        s.text(x + 50, 40 + n * 17 + 10, f"SP = {sp}", 10, color=RED, weight=700, family="JBMono")
    return s.svg()


# ------------------------------------------------------------------ chapter 4
def wheel():
    import math

    s = S(520, 300, "شکل: نمایش پیمانه‌ای (دایره‌ای) اعداد ۴ بیتی — مکمل دو (چپ) و بدون علامت (راست)")

    def ring(cx, cy, vals, title):
        r = 105
        s.raw(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BLUE}" stroke-width="1.6"/>')
        for k in range(16):
            ang = -math.pi / 2 + 2 * math.pi * k / 16
            x1, y1 = cx + (r - 5) * math.cos(ang), cy + (r - 5) * math.sin(ang)
            x2, y2 = cx + (r + 5) * math.cos(ang), cy + (r + 5) * math.sin(ang)
            s.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{BLUE}"/>')
            bx, by = cx + (r + 22) * math.cos(ang), cy + (r + 22) * math.sin(ang)
            s.text(bx, by, format(k, "04b"), 9, family="JBMono", color="#5b6475")
            vx, vy = cx + (r - 22) * math.cos(ang), cy + (r - 22) * math.sin(ang)
            v = vals[k]
            s.text(vx, vy, v, 11, weight=700, color=RED if v.startswith("-") else "#1f5fbf")
        s.text(cx, cy, title, 12, weight=700)

    ring(140, 155, [str(k if k < 8 else k - 16) for k in range(16)], "Two's Comp.")
    ring(390, 155, [str(k) for k in range(16)], "Unsigned")
    return s.svg()


# ------------------------------------------------------------------ chapter 5
def segment_fig():
    s = S(420, 230, "شکل: آدرس‌دهی قطعه‌ای — آدرس فیزیکی = محتوای ثبات قطعه + آدرس منطقی")
    s.text(90, 15, "Segment Register", 11, weight=700)
    s.rect(30, 25, 120, 24, "#cfe8b8", "#5a8f3a", rx=2)
    s.text(90, 37, "Segment Address", 10)
    s.text(300, 40, "Address generated in CU", 10)
    s.text(300, 55, "(logical address)", 10)
    s.fat(90, 50, 90, 118, color="#b5523b", both=False, w=16)
    s.fat(300, 65, 300, 118, color="#38b6ff", both=False, w=16)
    s.box(60, 120, 270, 44, "Adder  (+)", 16, weight=700)
    s.fat(195, 166, 195, 200, color="#2fae4b", both=False, w=16)
    s.text(195, 215, "Final (physical) address for memory", 10.5)
    return s.svg()


def page_fig():
    s = S(420, 230, "شکل: آدرس‌دهی صفحه‌ای — آدرس فیزیکی = (ثبات صفحه) ‖ (آدرس منطقی)؛ الحاق بیت‌ها، بدون جمع")
    s.text(90, 15, "Page Register", 11, weight=700)
    s.rect(30, 25, 120, 24, "#cfe8b8", "#5a8f3a", rx=2)
    s.text(90, 37, "Page address", 10)
    s.text(300, 40, "Address generated in CU", 10)
    s.text(300, 55, "(logical address)", 10)
    s.fat(90, 50, 175, 130, color="#a31515", both=False, w=16)
    s.fat(300, 65, 215, 130, color="#38b6ff", both=False, w=16)
    s.text(105, 105, "M−P bits", 10, anchor="end")
    s.text(285, 105, "P bits", 10, anchor="start")
    s.raw('<polygon points="150,135 240,135 240,160 260,160 195,195 130,160 150,160" fill="#7b3fb5" stroke="#5b2a8a"/>')
    s.text(195, 158, "M bits", 11, color="#fff", weight=700)
    s.text(195, 215, "Final (physical) address for memory", 10.5)
    return s.svg()


def multiuser():
    s = S(400, 190, "شکل: سیستم چندکاربره — سیستم‌عامل منابع را میان کاربران فعال تقسیم می‌کند")
    for i, (x, t) in enumerate([(60, "User #1"), (150, "User #2"), (330, "User #N")]):
        s.raw(f'<circle cx="{x}" cy="35" r="28" fill="#1f6fc4"/>')
        s.text(x, 36, t, 10.5, color="#fff", weight=700)
        s.fat(x, 63, 190 + (i - 1) * 25, 105, color="#4fb3ec", both=False, w=10)
    s.text(240, 35, "⋯", 22)
    s.raw('<ellipse cx="200" cy="120" rx="60" ry="18" fill="#2fbf5a"/>')
    s.text(200, 121, "Operating System", 10.5, color="#fff", weight=700)
    s.fat(200, 138, 200, 152, color="#8bd16b", both=False, w=10)
    s.box(140, 153, 120, 32, "Computer System", 11.5, weight=700)
    return s.svg()


def data_tree():
    s = S(520, 250, "شکل: دسته‌بندی اطلاعات در کامپیوتر")
    def node(x, y, t, w=96):
        s.box(x, y, w, 26, t, 11)
    def edge(x1, y1, x2, y2):
        s.arrow(x1, y1, x2, y2, sw=1.1)
    node(10, 110, "Information", 90)
    node(130, 40, "Code (per IF)", 100)
    node(130, 170, "Data", 70)
    edge(100, 123, 130, 53)
    edge(100, 123, 130, 183)
    node(240, 110, "Non-numerical", 100)
    node(240, 205, "Numerical", 90)
    edge(200, 183, 240, 123)
    edge(200, 183, 240, 218)
    node(380, 85, "Bit-string")
    node(380, 120, "Characters")
    edge(340, 123, 380, 98)
    edge(340, 123, 380, 133)
    node(380, 160, "Signed / Unsigned", 130)
    node(380, 192, "Binary / Decimal", 130)
    node(380, 224, "Integer / Real", 130)
    for y in (173, 205, 237):
        edge(330, 218, 380, y)
    s.text(450, 248, "Real: Fixed-point / Floating-point", 9.5, color="#5b6475")
    return s.svg()


def ascii_table():
    ctrl = ["NUL", "SOH", "STX", "ETX", "EOT", "ENQ", "ACK", "BEL", "BS", "HT", "LF", "VT", "FF", "CR", "SO", "SI",
            "DLE", "DC1", "DC2", "DC3", "DC4", "NAK", "SYN", "ETB", "CAN", "EM", "SUB", "ESC", "FS", "GS", "RS", "US"]
    import html as _h
    head = "".join(f"<th>{c:03b}</th>" for c in range(8))
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
                t = _h.escape(chr(code))
            style = ' style="background:#ffe3dc;font-weight:700"' if code == 65 else ""
            cells.append(f'<td{style}>{t}</td>')
        rows.append(f"<tr><th>{r:04b}</th>" + "".join(cells) + "</tr>")
    return ('<table class="ltrt small" style="font-family:JBMono;font-size:.8em"><thead><tr><th>LSBs \\ MSBs</th>'
            + head + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
            '<div class="tcap">جدول کد ASCII هفت‌بیتی: ستون = ۳ بیت پرارزش، سطر = ۴ بیت کم‌ارزش. مثلاً \'A\' = 100 0001 = 65 = 41h</div>')
