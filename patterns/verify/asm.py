"""Tiny two-pass assembler core shared by the exam-machine models.

A program is plain text in the exam's notation:  `label: mnem op1, op2 ; comment`.
Each machine supplies: unit bits, word units, size(mnem, ops) and encode(mnem, ops, value).
"""
import re

HEX_RE = re.compile(r"^[0-9A-Fa-f]+h$", re.I)


def split_ops(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def parse(src):
    lines = []
    for raw in src.splitlines():
        line = raw.split(";")[0].rstrip()
        if not line.strip():
            continue
        label = None
        m = re.match(r"^\s*([A-Za-z_][\w]*)\s*:\s*(.*)$", line)
        if m:
            label, line = m.group(1), m.group(2)
        parts = line.strip().split(None, 1)
        mnem = parts[0].lower() if parts else None
        ops = split_ops(parts[1]) if len(parts) > 1 else []
        lines.append((label, mnem, ops, raw.strip()))
    return lines


class Expr:
    def __init__(self, symtab):
        self.sym = symtab

    def num(self, tok):
        tok = tok.strip()
        if tok in self.sym:
            return self.sym[tok]
        if HEX_RE.match(tok):
            return int(tok[:-1], 16)
        if re.match(r"^\d+$", tok):
            return int(tok)
        raise KeyError(tok)

    def __call__(self, s):
        s = s.replace(" ", "")
        if not s:
            return 0
        terms = re.findall(r"[+-]?[^+-]+", s)
        total = 0
        for t in terms:
            sign = -1 if t.startswith("-") else 1
            t = t.lstrip("+-")
            total += sign * self.num(t)
        return total


class Machine:
    unit = 8          # bits per addressable unit
    word_units = 1    # units per word
    name = "?"

    # --- to be provided by subclasses
    def size(self, mnem, ops):
        raise NotImplementedError

    def encode(self, mnem, ops, ev):
        raise NotImplementedError

    def dw_values(self, ops, ev):
        """Return list of word values (None for '?')."""
        vals = []
        for op in ops:
            m = re.match(r"^(.+?)\s*dup\s*\((.*)\)$", op, re.I)
            if m:
                n = ev(m.group(1))
                v = None if m.group(2).strip() == "?" else ev(m.group(2))
                vals += [v] * n
            elif op.strip() == "?":
                vals.append(None)
            else:
                vals.append(self.dw_literal(op, ev))
        return vals

    def dw_literal(self, op, ev):
        return ev(op)

    def dw_count(self, ops):
        n = 0
        for op in ops:
            m = re.match(r"^(.+?)\s*dup\s*\((.*)\)$", op, re.I)
            n += int(Expr({})(m.group(1))) if m else 1
        return n

    # --- assembler
    def assemble(self, src, presym=None, externals=()):
        """Two-pass assembly. Symbols named in `externals` may stay undefined: their fields print as '?'."""
        lines = parse(src)
        sym, lc, layout = dict(presym or {}), 0, []
        for label, mnem, ops, raw in lines:
            if mnem == "org":
                lc = Expr({})(ops[0])
                if label:
                    sym[label] = lc
                continue
            if label:
                sym[label] = lc
            if mnem in (None, "end"):
                continue
            if mnem == "dw":
                n = self.dw_count(ops) * self.word_units
            else:
                n = self.size(mnem, ops)
            layout.append((lc, label, mnem, ops, raw, n))
            lc += n
        ev0 = Expr(sym)
        ext = set(externals)

        def ev(e):
            try:
                return ev0(e)
            except KeyError as k:
                if k.args and k.args[0] in ext:
                    return None
                raise

        listing, image = [], {}
        for addr, label, mnem, ops, raw, n in layout:
            self.here = addr
            if mnem == "dw":
                vals = self.dw_values(ops, ev)
                bits = ""
                for v in vals:
                    bits += "?" * (self.unit * self.word_units) if v is None else self.field(v, self.unit * self.word_units)
            else:
                bits = self.encode(mnem, ops, ev)
            assert len(bits) == n * self.unit, (raw, len(bits), n * self.unit)
            for k in range(n):
                chunk = bits[k * self.unit:(k + 1) * self.unit]
                image[addr + k] = None if "?" in chunk else int(chunk, 2)
            listing.append((addr, label, mnem, ops, raw, bits))
        self.sym = sym
        return image, listing

    @staticmethod
    def field(v, w):
        if v is None:
            return "?" * w
        return format(v & ((1 << w) - 1), f"0{w}b")


class Sim:
    """Unit-addressed memory plus helpers for big-endian words."""

    def __init__(self, m, image, fill=0):
        self.m = m
        self.mem = {}
        for a, v in image.items():
            self.mem[a] = fill if v is None else v
        self.fill = fill

    def unit(self, a):
        return self.mem.get(a, self.fill)

    def bits(self, a, nbits):
        u = self.m.unit
        n = -(-nbits // u)
        s = "".join(format(self.unit(a + k), f"0{u}b") for k in range(n))
        return s[:nbits]

    def rd(self, a):
        u, k = self.m.unit, self.m.word_units
        v = 0
        for i in range(k):
            v = (v << u) | self.unit(a + i)
        return v

    def wr(self, a, v):
        u, k = self.m.unit, self.m.word_units
        v &= (1 << (u * k)) - 1
        for i in reversed(range(k)):
            self.mem[a + i] = v & ((1 << u) - 1)
            v >>= u

    def wbits(self):
        return self.m.unit * self.m.word_units

    def signed(self, v):
        w = self.wbits()
        v &= (1 << w) - 1
        return v - (1 << w) if v >> (w - 1) else v
