"""IBM System/360 model for the course: a two-pass assembler (START/END/USING/DC/DS/EQU, base-displacement
resolution, RR/RX/RS/SI/SS formats) and a simulator of the RR/RX instructions taught in lectures 6-8.

Condition code follows the COURSE convention (lecture 7):
  arithmetic / logical-bitwise / multiply / divide : 00 result = 0, 01 result < 0, 10 result > 0, 11 overflow
  add/subtract logical (unsigned)                  : 00 result = 0, 10 result != 0, 11 carry / borrow
  compare                                          : 00 equal, 01 first < second, 10 first > second
  LR, L, ST, LA, BCT, BCTR, BALR do not change CC.
"""
import re

# ---------------------------------------------------------------- opcodes
RR = {"LR": 0x18, "LCR": 0x13, "LNR": 0x11, "LPR": 0x10, "AR": 0x1A, "SR": 0x1B, "MR": 0x1C, "DR": 0x1D,
      "ALR": 0x1E, "SLR": 0x1F, "NR": 0x14, "OR": 0x16, "XR": 0x17, "CR": 0x19, "CLR": 0x15, "BCTR": 0x06,
      "BCR": 0x07, "BALR": 0x05}
RX = {"L": 0x58, "ST": 0x50, "A": 0x5A, "S": 0x5B, "M": 0x5C, "D": 0x5D, "AL": 0x5E, "SL": 0x5F, "C": 0x59,
      "CL": 0x55, "N": 0x54, "O": 0x56, "X": 0x57, "LA": 0x41, "BCT": 0x46, "BC": 0x47}
RS = {"LM": 0x98, "STM": 0x90, "SLL": 0x89, "SRL": 0x88}
SI = {"MVI": 0x92, "OI": 0x96, "NI": 0x94, "XI": 0x97, "CLI": 0x95}
SS1 = {"MVC": 0xD2, "OC": 0xD6, "NC": 0xD4, "XC": 0xD7, "CLC": 0xD5}
SS2 = {"AP": 0xFA}

# extended branch mnemonics -> mask
EXT = {"B": 15, "NOP": 0, "BO": 1, "BH": 2, "BP": 2, "BL": 4, "BM": 4, "BNE": 7, "BNZ": 7, "BE": 8, "BZ": 8,
       "BNL": 11, "BNM": 11, "BNH": 13, "BNP": 13, "BNO": 14}
EXTR = {k + "R": v for k, v in EXT.items() if k not in ("NOP",)}
EXTR["NOPR"] = 0

NO_OPERANDS = {"EOJ"}
ALIGN = {"F": 4, "H": 2, "D": 8, "C": 1, "X": 1, "B": 1}
TLEN = {"F": 4, "H": 2, "D": 8}


class AsmError(Exception):
    pass


class Halt(Exception):
    pass


def ebcdic(s):
    return s.encode("cp037")


# ---------------------------------------------------------------- expressions
class Val:
    """Value of an expression: number + relocatable flag (label-based or absolute)."""

    def __init__(self, v, rel):
        self.v, self.rel = v, rel


def term(tok, sym, lc):
    tok = tok.strip()
    m = re.fullmatch(r"([XBOC])'(.*)'", tok, re.I)
    if m:
        t, body = m.group(1).upper(), m.group(2)
        if t == "X":
            return Val(int(body, 16), False)
        if t == "B":
            return Val(int(body, 2), False)
        if t == "O":
            return Val(int(body, 8), False)
        return Val(int.from_bytes(ebcdic(body), "big"), False)
    if tok == "*":
        return Val(lc, True)
    if re.fullmatch(r"\d+", tok):
        return Val(int(tok), False)
    if tok in sym:
        v, rel = sym[tok]
        return Val(v, rel)
    raise KeyError(tok)


def expr(s, sym, lc):
    s = re.sub(r"('[^']*')|\s+", lambda m: m.group(1) or "", s)
    parts = re.findall(r"[+-]?(?:[XBOC]'[^']*'|\*|[^+-]+)", s)
    total, rel = 0, 0
    for p in parts:
        sign = -1 if p.startswith("-") else 1
        t = term(p.lstrip("+-"), sym, lc)
        total += sign * t.v
        rel += sign * (1 if t.rel else 0)
    return Val(total, rel == 1)


def split_ops(s):
    out, depth, cur, q = [], 0, "", False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "'" :
            q = not q
        if not q and ch == "(":
            depth += 1
        elif not q and ch == ")":
            depth -= 1
        if ch == "," and depth == 0 and not q:
            out.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    out.append(cur)
    return [o.strip() for o in out]


def split_paren(op):
    """'D(X,B)' -> ('D', ['X','B']);  'S' -> ('S', None)."""
    op = op.strip()
    depth, q = 0, False
    for i, ch in enumerate(op):
        if ch == "'":
            q = not q
        if not q and ch == "(" and depth == 0:
            if op.endswith(")"):
                inner = op[i + 1:-1]
                return op[:i], [x.strip() for x in inner.split(",")]
        if not q and ch == "(":
            depth += 1
        elif not q and ch == ")":
            depth -= 1
    return op, None


# ---------------------------------------------------------------- source parsing
def parse_line(raw):
    """Columns: label at column 1, then mnemonic, operands, comment (separated by blanks)."""
    if not raw.strip():
        return None
    if raw.startswith("*"):
        return ("comment", None, None, None, raw[1:].strip())
    label = None
    rest = raw
    if not raw[0].isspace():
        label, rest = (raw.split(None, 1) + [""])[:2]
    rest = rest.strip()
    if not rest:
        return ("stmt", label, None, "", "")
    mnem, rest = (rest.split(None, 1) + [""])[:2]
    if mnem.upper() in NO_OPERANDS:
        return ("stmt", label, mnem.upper(), "", rest.strip())
    # operand field ends at the first blank outside quotes
    ops, q, i = "", False, 0
    while i < len(rest):
        ch = rest[i]
        if ch == "'":
            q = not q
        if ch.isspace() and not q:
            break
        ops += ch
        i += 1
    comment = rest[i:].strip()
    return ("stmt", label, mnem.upper(), ops, comment)


def dc_items(ops):
    """Split a DC/DS operand into (dup, type, nominal-or-None)."""
    items = []
    for op in split_ops(ops):
        m = re.fullmatch(r"(\d*)([FHDCXB])(?:L(\d+))?(?:'(.*)')?", op, re.I)
        if not m:
            raise AsmError("bad DC/DS operand " + op)
        dup = int(m.group(1)) if m.group(1) else 1
        items.append((dup, m.group(2).upper(), int(m.group(3)) if m.group(3) else None, m.group(4)))
    return items


def item_len(t, explicit, nominal):
    if explicit:
        return explicit
    if t in TLEN:
        return TLEN[t]
    if nominal is None:
        return 1
    if t == "C":
        return len(nominal)
    if t == "X":
        return (len(nominal) + 1) // 2
    if t == "B":
        return (len(nominal) + 7) // 8
    return 1


def dc_bytes(t, length, nominal, sym, lc):
    out = b""
    for part in nominal.split(","):
        if t in ("F", "H", "D"):
            v = expr(part, sym, lc).v
            out += (v & ((1 << (8 * length)) - 1)).to_bytes(length, "big")
        elif t == "C":
            out += ebcdic(part).ljust(length, b"\x40")[:length]
        elif t == "X":
            out += int(part, 16).to_bytes(length, "big")
        elif t == "B":
            out += int(part, 2).to_bytes(length, "big")
    return out


# ---------------------------------------------------------------- assembler
class Assembler:
    def __init__(self, src, presym=None):
        self.src = src
        self.presym = dict(presym or {})

    def size(self, mn, ops):
        if mn in RR or mn in EXTR or mn == "EOJ":
            return 2
        if mn in RX or mn in EXT or mn in RS or mn in SI:
            return 4
        if mn in SS1 or mn in SS2:
            return 6
        raise AsmError("unknown mnemonic " + mn)

    def run(self):
        lines = [parse_line(r) for r in self.src.strip("\n").splitlines()]
        sym = {k: (v, True) for k, v in self.presym.items()}
        lc, start, layout, entry = 0, 0, [], None
        # ---- pass 1
        for ln, raw in zip(lines, self.src.strip("\n").splitlines()):
            if ln is None:
                continue
            kind, label, mn, ops, comment = ln
            if kind == "comment":
                layout.append(("comment", None, raw))
                continue
            if mn == "START":
                lc = start = expr(ops, sym, 0).v if ops else 0
                if label:
                    sym[label] = (lc, True)
                layout.append(("dir", lc, raw))
                continue
            if mn == "EQU":
                v = expr(ops, sym, lc)
                sym[label] = (v.v, v.rel)
                layout.append(("equ", v.v, raw))
                continue
            if mn in ("USING", "END", "DROP"):
                layout.append(("dir", lc, raw))
                continue
            if mn in ("DC", "DS"):
                items = dc_items(ops)
                al = ALIGN.get(items[0][1], 1) if items[0][2] is None else 1
                lc = (lc + al - 1) // al * al
                if label:
                    sym[label] = (lc, True)
                n = 0
                for dup, t, ln_, nom in items:
                    per = item_len(t, ln_, nom) * (len(nom.split(",")) if (nom is not None and t in "FHD") else 1)
                    n += dup * per
                layout.append((mn, lc, raw, n))
                lc += n
                continue
            if label:
                sym[label] = (lc, True)
            n = self.size(mn, ops)
            layout.append(("ins", lc, raw, n))
            lc += n
        self.sym = sym
        # ---- pass 2
        using = []
        rows, image = [], {}
        for item, ln in zip(layout, [l for l in lines if l is not None]):
            kind = item[0]
            raw = item[2]
            if kind == "comment":
                rows.append(dict(kind="comment", raw=raw))
                continue
            _, label, mn, ops, comment = ln
            if kind == "dir":
                lc = item[1]
                if mn == "USING":
                    a, r = split_ops(ops)
                    base = expr(a, sym, lc).v
                    using = [u for u in using if u[1] != expr(r, sym, lc).v] + [(base, expr(r, sym, lc).v)]
                if mn == "DROP":
                    using = [u for u in using if u[1] != expr(ops, sym, lc).v]
                if mn == "END" and ops:
                    entry = expr(ops, sym, lc).v
                rows.append(dict(kind="dir", loc=lc, label=label, mn=mn, ops=ops, comment=comment, raw=raw))
                continue
            if kind == "equ":
                rows.append(dict(kind="equ", loc=item[1], label=label, mn=mn, ops=ops, comment=comment, raw=raw))
                continue
            loc = item[1]
            if kind in ("DC", "DS"):
                data = b""
                if kind == "DC":
                    for dup, t, ln_, nom in dc_items(ops):
                        data += dc_bytes(t, item_len(t, ln_, nom), nom, sym, loc) * dup
                    for k, b in enumerate(data):
                        image[loc + k] = b
                rows.append(dict(kind=kind.lower(), loc=loc, label=label, mn=mn, ops=ops, comment=comment, raw=raw,
                                 size=item[3], obj=data))
                continue
            obj, fields, eff = self.encode(mn, ops, sym, loc, using)
            for k, b in enumerate(obj):
                image[loc + k] = b
            rows.append(dict(kind="ins", loc=loc, label=label, mn=mn, ops=ops, comment=comment, raw=raw, obj=obj,
                             fields=fields, eff=eff))
        self.rows, self.image, self.entry, self.start = rows, image, entry, start
        return self

    # -------------------------------------------------- operand helpers
    def base_disp(self, v, using):
        best = None
        for base, reg in using:
            d = v - base
            if 0 <= d <= 4095:
                if best is None or d < best[1] or (d == best[1] and reg > best[0]):
                    best = (reg, d)
        if best is None:
            raise AsmError("no base register covers %Xh" % v)
        return best

    def storage(self, op, sym, lc, using, allow_index=True):
        """RX/RS/SI/SS storage operand -> (X, B, D, effective-address-expression-text)."""
        head, inner = split_paren(op)
        v = expr(head, sym, lc) if head else Val(0, False)
        if v.rel:
            b, d = self.base_disp(v.v, using)
            x = expr(inner[0], sym, lc).v if inner and inner[0] else 0
            return x, b, d, v.v
        d = v.v
        if not 0 <= d <= 4095:
            raise AsmError("displacement out of range")
        if inner is None:
            return 0, 0, d, None
        if len(inner) == 1:
            return (expr(inner[0], sym, lc).v, 0, d, None) if allow_index else (0, expr(inner[0], sym, lc).v, d, None)
        x = expr(inner[0], sym, lc).v if inner[0] else 0
        b = expr(inner[1], sym, lc).v if inner[1] else 0
        return x, b, d, None

    def encode(self, mn, ops, sym, lc, using):
        o = split_ops(ops) if ops else []
        E = lambda s: expr(s, sym, lc).v
        if mn == "EOJ":
            return bytes([0x0A, 0x0E]), [("SVC", "0A"), ("I", "0E")], None
        if mn in RR or mn in EXTR:
            if mn in EXTR:
                op, r1, r2 = 0x07, EXTR[mn], E(o[0])
            else:
                op, r1, r2 = RR[mn], E(o[0]), E(o[1])
            return bytes([op, (r1 << 4) | r2]), [("op", "%02X" % op), ("M1" if op == 7 else "r1", "%X" % r1), ("r2", "%X" % r2)], None
        if mn in RX or mn in EXT:
            if mn in EXT:
                op, r1, st = 0x47, EXT[mn], o[0]
            else:
                op, r1, st = RX[mn], E(o[0]), o[1]
            x, b, d, sv = self.storage(st, sym, lc, using)
            obj = bytes([op, (r1 << 4) | x, (b << 4) | (d >> 8), d & 0xFF])
            return obj, [("op", "%02X" % op), ("M1" if op == 0x47 else "r1", "%X" % r1), ("X2", "%X" % x), ("B2", "%X" % b),
                         ("D2", "%03X" % d)], sv
        if mn in RS:
            op = RS[mn]
            if mn in ("SLL", "SRL"):
                r1, r3 = E(o[0]), 0
                x, b, d, sv = self.storage(o[1], sym, lc, using, allow_index=False)
            else:
                r1, r3 = E(o[0]), E(o[1])
                x, b, d, sv = self.storage(o[2], sym, lc, using, allow_index=False)
            obj = bytes([op, (r1 << 4) | r3, (b << 4) | (d >> 8), d & 0xFF])
            return obj, [("op", "%02X" % op), ("r1", "%X" % r1), ("r3", "%X" % r3), ("B2", "%X" % b), ("D2", "%03X" % d)], sv
        if mn in SI:
            op = SI[mn]
            x, b, d, sv = self.storage(o[0], sym, lc, using, allow_index=False)
            i2 = E(o[1])
            obj = bytes([op, i2, (b << 4) | (d >> 8), d & 0xFF])
            return obj, [("op", "%02X" % op), ("I2", "%02X" % i2), ("B1", "%X" % b), ("D1", "%03X" % d)], sv
        if mn in SS1:
            op = SS1[mn]
            head, inner = split_paren(o[0])
            L = E(inner[0])
            base_txt = head if len(inner) == 1 else "%s(,%s)" % (head, inner[1])
            _, b1, d1, sv = self.storage(base_txt, sym, lc, using, allow_index=False)
            _, b2, d2, _ = self.storage(o[1], sym, lc, using, allow_index=False)
            obj = bytes([op, L - 1, (b1 << 4) | (d1 >> 8), d1 & 0xFF, (b2 << 4) | (d2 >> 8), d2 & 0xFF])
            return obj, [("op", "%02X" % op), ("L-1", "%02X" % (L - 1)), ("B1", "%X" % b1), ("D1", "%03X" % d1),
                         ("B2", "%X" % b2), ("D2", "%03X" % d2)], sv
        if mn in SS2:
            op = SS2[mn]
            h1, i1 = split_paren(o[0])
            h2, i2_ = split_paren(o[1])
            L1, L2 = E(i1[0]), E(i2_[0])
            _, b1, d1, _ = self.storage(h1, sym, lc, using, allow_index=False)
            _, b2, d2, _ = self.storage(h2, sym, lc, using, allow_index=False)
            obj = bytes([op, ((L1 - 1) << 4) | (L2 - 1), (b1 << 4) | (d1 >> 8), d1 & 0xFF, (b2 << 4) | (d2 >> 8), d2 & 0xFF])
            return obj, [("op", "%02X" % op), ("L1-1", "%X" % (L1 - 1)), ("L2-1", "%X" % (L2 - 1)), ("B1", "%X" % b1),
                         ("D1", "%03X" % d1), ("B2", "%X" % b2), ("D2", "%03X" % d2)], None
        raise AsmError(mn)


def assemble(src, presym=None):
    return Assembler(src, presym).run()


# ---------------------------------------------------------------- simulator
M32 = 0xFFFFFFFF


def s32(v):
    v &= M32
    return v - (1 << 32) if v >> 31 else v


def cc_signed(v):
    return 0 if v == 0 else 1 if v < 0 else 2


class CPU:
    def __init__(self, image=None, regs=None, mem=None):
        self.mem = dict(image or {})
        for a, v in (mem or {}).items():
            self.wr(a, v)
        self.R = [0] * 16
        for k, v in (regs or {}).items():
            self.R[k] = v & M32
        self.cc = 0
        self.pc = 0
        self.steps = 0

    # memory (big endian, aligned words)
    def rd(self, a, n=4):
        if a % n:
            raise Halt("specification exception: address %Xh not aligned" % a)
        return int.from_bytes(bytes(self.mem.get(a + k, 0) for k in range(n)), "big")

    def wr(self, a, v, n=4):
        if a % n:
            raise Halt("specification exception: address %Xh not aligned" % a)
        for k, b in enumerate((v & ((1 << (8 * n)) - 1)).to_bytes(n, "big")):
            self.mem[a + k] = b

    def ea(self, x, b, d):
        return (d + (self.R[b] if b else 0) + (self.R[x] if x else 0)) & 0xFFFFFF

    def set_arith(self, full):
        if not -(1 << 31) <= full < (1 << 31):
            self.cc = 3
        else:
            self.cc = cc_signed(full)
        return full & M32

    def step(self):
        pc = self.pc
        op = self.mem.get(pc, 0)
        b1 = self.mem.get(pc + 1, 0)
        r1, r2 = b1 >> 4, b1 & 15
        R = self.R
        if op == 0x0A:                                   # EOJ (SVC 14)
            raise Halt("EOJ")
        if op < 0x40:                                    # RR
            self.pc = pc + 2
            a, b = s32(R[r1]), s32(R[r2])
            if op == 0x18:
                R[r1] = R[r2]
            elif op == 0x13:
                R[r1] = self.set_arith(-b)
            elif op == 0x11:
                R[r1] = self.set_arith(-abs(b))
            elif op == 0x10:
                R[r1] = self.set_arith(abs(b))
            elif op == 0x1A:
                R[r1] = self.set_arith(a + b)
            elif op == 0x1B:
                R[r1] = self.set_arith(a - b)
            elif op in (0x1E, 0x1F):
                self.logical(r1, R[r2], op == 0x1E)
            elif op in (0x14, 0x16, 0x17):
                v = {0x14: R[r1] & R[r2], 0x16: R[r1] | R[r2], 0x17: R[r1] ^ R[r2]}[op]
                R[r1] = v
                self.cc = cc_signed(s32(v))
            elif op == 0x19:
                self.cc = 0 if a == b else 1 if a < b else 2
            elif op == 0x15:
                self.cc = 0 if R[r1] == R[r2] else 1 if R[r1] < R[r2] else 2
            elif op == 0x1C:
                self.mul(r1, R[r2])
            elif op == 0x1D:
                self.div(r1, R[r2])
            elif op == 0x06:
                R[r1] = (R[r1] - 1) & M32
                if R[r1] != 0 and r2 != 0:
                    self.pc = R[r2] & 0xFFFFFF
            elif op == 0x07:
                if (r1 >> (3 - self.cc)) & 1 and r2 != 0:
                    self.pc = R[r2] & 0xFFFFFF
            elif op == 0x05:
                target = R[r2] & 0xFFFFFF
                R[r1] = self.pc
                if r2 != 0:
                    self.pc = target
            else:
                raise Halt("unimplemented RR %02X" % op)
            return
        b2 = self.mem.get(pc + 2, 0)
        b3 = self.mem.get(pc + 3, 0)
        x, b, d = r2, b2 >> 4, ((b2 & 15) << 8) | b3
        if 0x40 <= op < 0x80:                            # RX
            self.pc = pc + 4
            ea = self.ea(x, b, d)
            if op == 0x41:
                R[r1] = ea
                return
            if op == 0x46:
                R[r1] = (R[r1] - 1) & M32
                if R[r1] != 0:
                    self.pc = ea
                return
            if op == 0x47:
                if (r1 >> (3 - self.cc)) & 1:
                    self.pc = ea
                return
            if op == 0x50:
                self.wr(ea, R[r1])
                return
            m = self.rd(ea)
            a = s32(R[r1])
            if op == 0x58:
                R[r1] = m
            elif op == 0x5A:
                R[r1] = self.set_arith(a + s32(m))
            elif op == 0x5B:
                R[r1] = self.set_arith(a - s32(m))
            elif op in (0x5E, 0x5F):
                self.logical(r1, m, op == 0x5E)
            elif op == 0x59:
                self.cc = 0 if a == s32(m) else 1 if a < s32(m) else 2
            elif op == 0x55:
                self.cc = 0 if R[r1] == m else 1 if R[r1] < m else 2
            elif op in (0x54, 0x56, 0x57):
                v = {0x54: R[r1] & m, 0x56: R[r1] | m, 0x57: R[r1] ^ m}[op]
                R[r1] = v
                self.cc = cc_signed(s32(v))
            elif op == 0x5C:
                self.mul(r1, m)
            elif op == 0x5D:
                self.div(r1, m)
            else:
                raise Halt("unimplemented RX %02X" % op)
            return
        if op in (0x98, 0x90):                           # LM / STM
            self.pc = pc + 4
            a = self.ea(0, b, d)
            r = r1
            while True:
                if op == 0x98:
                    R[r] = self.rd(a)
                else:
                    self.wr(a, R[r])
                if r == r2:
                    break
                r, a = (r + 1) % 16, a + 4
            return
        if op in (0x89, 0x88):                           # SLL / SRL
            self.pc = pc + 4
            n = self.ea(0, b, d) & 63
            R[r1] = ((R[r1] << n) if op == 0x89 else (R[r1] >> n)) & M32
            return
        if op in (0x92, 0x96, 0x94, 0x97):               # SI
            self.pc = pc + 4
            a = self.ea(0, b, d)
            v = self.mem.get(a, 0)
            nv = {0x92: b1, 0x96: v | b1, 0x94: v & b1, 0x97: v ^ b1}[op]
            self.mem[a] = nv
            if op != 0x92:
                self.cc = 0 if nv == 0 else 1
            return
        if op in (0xD2, 0xD6, 0xD4, 0xD7):               # SS1
            self.pc = pc + 6
            L = b1 + 1
            a1 = self.ea(0, b, d)
            b4, b5 = self.mem.get(pc + 4, 0), self.mem.get(pc + 5, 0)
            a2 = self.ea(0, b4 >> 4, ((b4 & 15) << 8) | b5)
            nz = False
            for k in range(L):
                s, t = self.mem.get(a2 + k, 0), self.mem.get(a1 + k, 0)
                v = {0xD2: s, 0xD6: t | s, 0xD4: t & s, 0xD7: t ^ s}[op]
                self.mem[a1 + k] = v
                nz |= v != 0
            if op != 0xD2:
                self.cc = 1 if nz else 0
            return
        raise Halt("unimplemented %02X" % op)

    def logical(self, r1, v, add):
        a = self.R[r1]
        if add:
            full = a + v
            carry = full >> 32
        else:
            full = a - v
            carry = 1 if a < v else 0
        res = full & M32
        self.R[r1] = res
        self.cc = 3 if carry else (0 if res == 0 else 2)

    def mul(self, r1, v):
        if r1 % 2:
            raise Halt("specification exception: odd register in multiply")
        p = s32(self.R[r1 + 1]) * s32(v)
        self.R[r1] = (p >> 32) & M32
        self.R[r1 + 1] = p & M32
        self.cc = cc_signed(p)

    def div(self, r1, v):
        if r1 % 2:
            raise Halt("specification exception: odd register in divide")
        dividend = (self.R[r1] << 32) | self.R[r1 + 1]
        if dividend >> 63:
            dividend -= 1 << 64
        dv = s32(v)
        if dv == 0:
            raise Halt("fixed-point divide exception")
        q = abs(dividend) // abs(dv)
        if (dividend < 0) != (dv < 0):
            q = -q
        r = dividend - q * dv
        if not -(1 << 31) <= q < (1 << 31):
            raise Halt("fixed-point divide exception (quotient too large)")
        self.R[r1 + 1] = q & M32
        self.R[r1] = r & M32
        self.cc = cc_signed(q)

    def run(self, pc, maxsteps=200000):
        self.pc = pc
        for _ in range(maxsteps):
            try:
                self.step()
            except Halt as h:
                if str(h) == "EOJ":
                    return self
                raise
            self.steps += 1
        raise Halt("no EOJ")


CCSTR = {0: "00", 1: "01", 2: "10", 3: "11"}
