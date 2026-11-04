"""Models (assembler + simulator) of the machines in the CSL midterms 1398-1402."""
import math
import re
import struct

from asm import Machine, Sim


def opmode(op):
    """Classify a memory-machine operand: ('imm'|'ind'|'dir', expr)."""
    op = op.strip()
    if op.startswith("#"):
        return "imm", op[1:]
    if op.startswith("(") and op.endswith(")"):
        return "ind", op[1:-1]
    return "dir", op


class Halt(Exception):
    pass


# ======================================================================= 1402
class M1402(Machine):
    """2^24 units x 6 bits, 24-bit word (4 units), PSR z,s.
    I : op3 | addr1 24 | x y z | addr2/data 24   (54 bits = 9 units)
    II: op3 | addr 24  | x 1 1                   (30 bits = 5 units)"""
    name, unit, word_units = "1402", 6, 4
    OPS = {"mov": 0, "and": 1, "or": 2, "xor": 3, "sub": 4, "add": 5}
    JMP = {"jz": (6, 0), "jnz": (6, 1), "jneg": (7, 0), "jmp": (7, 1)}

    def size(self, mnem, ops):
        return 9 if mnem in self.OPS else 5

    def encode(self, mnem, ops, ev):
        f = self.field
        if mnem in self.OPS:
            k1, e1 = opmode(ops[0])
            k2, e2 = opmode(ops[1])
            x = 1 if k1 == "ind" else 0
            yz = {"dir": "00", "ind": "01", "imm": "10"}[k2]
            return f(self.OPS[mnem], 3) + f(ev(e1), 24) + str(x) + yz + f(ev(e2), 24)
        op, x = self.JMP[mnem]
        return f(op, 3) + f(ev(ops[0]), 24) + str(x) + "11"

    def run(self, image, pc=0, maxsteps=10**6, os_addr=None, trace=False):
        s = Sim(self, image)
        z = sgn = 0
        steps = 0
        while steps < maxsteps:
            steps += 1
            if os_addr is not None and pc == os_addr:
                return s, steps
            b = s.bits(pc, 54)
            op = int(b[0:3], 2)
            a1 = int(b[3:27], 2)
            x, yz = b[27], b[28:30]
            if yz == "11":
                pc += 5
                taken = {(6, "0"): z == 1, (6, "1"): z == 0, (7, "0"): sgn == 1, (7, "1"): True}[(op, x)]
                if taken:
                    pc = a1
                continue
            a2 = int(b[30:54], 2)
            pc += 9
            dst = s.rd(a1) if x == "1" else a1
            opr2 = {"00": lambda: s.rd(a2), "01": lambda: s.rd(s.rd(a2)), "10": lambda: a2}[yz]()
            cur = s.rd(dst)
            r = {0: lambda: opr2, 1: lambda: cur & opr2, 2: lambda: cur | opr2, 3: lambda: cur ^ opr2,
                 4: lambda: cur - opr2, 5: lambda: cur + opr2}[op]()
            r &= 0xFFFFFF
            s.wr(dst, r)
            if op != 0:
                z = int(r == 0)
                sgn = r >> 23
        raise Halt("no halt")


# ======================================================================= 1401
class M1401(Machine):
    """2^21 units x 7 bits, 21-bit word (3 units), PSR z,s,v.
    I : op4 | i | addr1 21 | xy | addr2/data 21   (49 bits = 7 units)
    II: op4 | i | addr1 21 | 11                    (28 bits = 4 units)"""
    name, unit, word_units = "1401", 7, 3
    OPS = {"mov": 0, "and": 1, "or": 2, "xor": 3, "cmp": 4, "sub": 5, "add": 6}
    OPS2 = {"clr": 0, "inc": 1, "dec": 2, "not": 3, "neg": 4, "call": 5, "jmp": 6, "jz": 7, "jnz": 8,
            "jneg": 9, "jpos": 10, "jover": 11}

    def size(self, mnem, ops):
        return 7 if mnem in self.OPS else 4

    def encode(self, mnem, ops, ev):
        f = self.field
        k1, e1 = opmode(ops[0])
        i = "1" if k1 == "ind" else "0"
        if mnem in self.OPS:
            k2, e2 = opmode(ops[1])
            xy = {"dir": "00", "ind": "01", "imm": "10"}[k2]
            return f(self.OPS[mnem], 4) + i + f(ev(e1), 21) + xy + f(ev(e2), 21)
        return f(self.OPS2[mnem], 4) + i + f(ev(e1), 21) + "11"

    def run(self, image, pc=0, maxsteps=10**6, os_addr=None, ret_mark=0x1FFFFF):
        s = Sim(self, image)
        s.wr(0x1FFFFD, ret_mark)          # return address left by the OS
        z = sg = v = 0
        steps = 0
        M = 0x1FFFFF
        while steps < maxsteps:
            steps += 1
            if pc == ret_mark:
                return s, steps
            b = s.bits(pc, 49)
            op, i, a1, xy = int(b[0:4], 2), b[4], int(b[5:26], 2), b[26:28]
            if xy == "11":
                pc += 4
                if op <= 4:
                    dst = s.rd(a1) if i == "1" else a1
                    cur = s.rd(dst)
                    r = {0: 0, 1: cur + 1, 2: cur - 1, 3: ~cur, 4: -cur}[op] & M
                    s.wr(dst, r)
                    z, sg = int(r == 0), r >> 20
                    v = int((op == 1 and cur == 0x0FFFFF) or (op == 2 and cur == 0x100000) or (op == 4 and cur == 0x100000))
                else:
                    target = s.rd(a1) if i == "1" else a1
                    take = {5: True, 6: True, 7: z == 1, 8: z == 0, 9: sg == 1, 10: (sg | z) == 0, 11: v == 1}[op]
                    if op == 5:
                        s.wr(0x1FFFFD, pc)
                    if take:
                        pc = target
                continue
            a2 = int(b[28:49], 2)
            pc += 7
            dst = s.rd(a1) if i == "1" else a1
            opr2 = {"00": lambda: s.rd(a2), "01": lambda: s.rd(s.rd(a2)), "10": lambda: a2}[xy]()
            cur = s.rd(dst)
            sa, sb = s.signed(cur), s.signed(opr2)
            if op == 0:
                s.wr(dst, opr2)
                continue
            full = {1: cur & opr2, 2: cur | opr2, 3: cur ^ opr2, 4: sa - sb, 5: sa - sb, 6: sa + sb}[op]
            r = full & M
            if op != 4:
                s.wr(dst, r)
            z, sg = int(r == 0), r >> 20
            if op in (4, 5, 6):
                v = int(not (-(1 << 20) <= full < (1 << 20)))
        raise Halt("no halt")


# ======================================================================= 1400
class M1400(Machine):
    """2^16 units x 4 bits (2^14 words of 16 bits).
    I  : op3 | addr1 16 | d | addr2/data 16                (36 bits = 9 units)
    II : op3 | addr1 16 | x                                (20 bits = 5 units)
    III: op3 | addr1 16 | d | addr2/data 16 | addr3 16     (52 bits = 13 units)"""
    name, unit, word_units = "1400", 4, 4
    OPS = {"mov": 0, "add": 1, "sub": 2}
    OPS2 = {"inc": (3, 0), "dec": (3, 1), "jmp": (4, 0), "call": (4, 1)}
    OPS3 = {"je": 5, "jne": 6, "jl": 7}

    def size(self, mnem, ops):
        return 9 if mnem in self.OPS else 5 if mnem in self.OPS2 else 13

    def encode(self, mnem, ops, ev):
        f = self.field
        if mnem in self.OPS2:
            op, x = self.OPS2[mnem]
            k, e = opmode(ops[0])
            return f(op, 3) + f(ev(e), 16) + str(x)
        k2, e2 = opmode(ops[1])
        d = "1" if k2 == "imm" else "0"
        if mnem in self.OPS:
            return f(self.OPS[mnem], 3) + f(ev(ops[0]), 16) + d + f(ev(e2), 16)
        return f(self.OPS3[mnem], 3) + f(ev(ops[0]), 16) + d + f(ev(e2), 16) + f(ev(ops[2]), 16)

    def run(self, image, pc=0, maxsteps=10**6, ret_mark=0xFFF0):
        s = Sim(self, image)
        s.wr(0xFFFE, ret_mark)
        steps = 0
        while steps < maxsteps:
            steps += 1
            if pc == ret_mark:
                return s, steps
            b = s.bits(pc, 52)
            op, a1 = int(b[0:3], 2), int(b[3:19], 2)
            if op in (3, 4):
                x = b[19]
                pc += 5
                if op == 3:
                    s.wr(a1, s.rd(a1) + (1 if x == "0" else -1))
                elif x == "0":
                    pc = s.rd(a1)
                else:
                    s.wr(0xFFFE, pc)
                    pc = a1
                continue
            d, a2 = b[19], int(b[20:36], 2)
            opr2 = a2 if d == "1" else s.rd(a2)
            if op <= 2:
                pc += 9
                cur = s.rd(a1)
                s.wr(a1, [opr2, cur + opr2, cur - opr2][op])
                continue
            a3 = int(b[36:52], 2)
            pc += 13
            l, r = s.signed(s.rd(a1)), s.signed(opr2)
            if {5: l == r, 6: l != r, 7: l < r}[op]:
                pc = a3
        raise Halt("no halt")


# ======================================================================= 1399
class M1399(Machine):
    """2^24 units x 6 bits, 24-bit word (4 units), R0..R31 (R31 = OS return address).
    I  : 00 op4 | i1 r1 | i2 r2 / qdata6       (18 bits = 3 units)
    II : 010 op4 | r5                          (12 bits = 2 units)
    III: 011 op4 | r5 | addr 24                (36 bits = 6 units)
    V  : 1 | r5 | data 24                      (30 bits = 5 units)"""
    name, unit, word_units = "1399", 6, 4
    F1 = {"mov": 0, "add": 1, "sub": 2, "and": 3, "or": 4, "xor": 5, "swap": 6, "addq": 7, "subq": 8, "movq": 9}
    F2 = {"jmp": 0, "inc": 1, "dec": 2, "clr": 3, "not": 4, "neg": 5, "inc4": 6, "dec4": 7}
    F3 = {"jnz": 4, "jz": 5, "jneg": 6, "jpos": 7, "loop": 8, "jmp+": 9, "call": 10}

    @staticmethod
    def reg(op):
        op = op.strip()
        ind = op.startswith("(")
        r = int(op.strip("()").upper().lstrip("R"))
        return ind, r

    def kind(self, mnem, ops):
        if mnem in self.F2:
            return 2
        if mnem == "mov":
            a, b = ops
            if b.startswith("#"):
                return 5
            isreg = lambda o: re.match(r"^\(?R\d+\)?$", o.strip(), re.I)
            if isreg(a) and isreg(b):
                return 1
            return 3
        if mnem in self.F1:
            return 1
        return 3

    def size(self, mnem, ops):
        return {1: 3, 2: 2, 3: 6, 5: 5}[self.kind(mnem, ops)]

    def encode(self, mnem, ops, ev):
        f = self.field
        k = self.kind(mnem, ops)
        if k == 5:
            _, r = self.reg(ops[0])
            return "1" + f(r, 5) + f(ev(ops[1][1:]), 24)
        if k == 2:
            _, r = self.reg(ops[0])
            return "010" + f(self.F2[mnem], 4) + f(r, 5)
        if k == 1:
            i1, r1 = self.reg(ops[0])
            first = "00" + f(self.F1[mnem], 4) + str(int(i1)) + f(r1, 5)
            if mnem in ("addq", "subq", "movq"):
                return first + f(ev(ops[1]), 6)
            i2, r2 = self.reg(ops[1])
            return first + str(int(i2)) + f(r2, 5)
        # format III
        if mnem == "mov":
            a, b = ops
            if re.match(r"^R\d+$", a.strip(), re.I):
                kind_b, e = opmode(b)
                sub = 2 if kind_b == "ind" else 0
                r = self.reg(a)[1]
            else:
                kind_a, e = opmode(a)
                sub = 3 if kind_a == "ind" else 1
                r = self.reg(b)[1]
            return "011" + f(sub, 4) + f(r, 5) + f(ev(e), 24)
        r = self.reg(ops[0])[1]
        return "011" + f(self.F3[mnem], 4) + f(r, 5) + f(ev(ops[1]), 24)

    def run(self, image, pc=0, maxsteps=10**6, regs=None, ret_mark=0xFFFFF0):
        s = Sim(self, image)
        R = [0] * 32
        if regs:
            for k, v in regs.items():
                R[k] = v
        R[31] = ret_mark
        M = 0xFFFFFF
        sg = lambda v: (v & M) - (1 << 24) if (v & M) >> 23 else v & M
        steps = 0
        while steps < maxsteps:
            steps += 1
            if pc == ret_mark:
                return s, R, steps
            b = s.bits(pc, 36)
            if b[0] == "1":
                R[int(b[1:6], 2)] = int(b[6:30], 2)
                pc += 5
            elif b[:2] == "00":
                op = int(b[2:6], 2)
                i1, r1 = b[6] == "1", int(b[7:12], 2)
                pc += 3
                get1 = (lambda: s.rd(R[r1])) if i1 else (lambda: R[r1])

                def put1(v):
                    if i1:
                        s.wr(R[r1], v)
                    else:
                        R[r1] = v & M
                if op in (7, 8, 9):
                    q = int(b[12:18], 2)
                    put1({7: get1() + q, 8: get1() - q, 9: q}[op])
                    continue
                i2, r2 = b[12] == "1", int(b[13:18], 2)
                v2 = s.rd(R[r2]) if i2 else R[r2]
                if op == 6:
                    v1 = get1()
                    put1(v2)
                    if i2:
                        s.wr(R[r2], v1)
                    else:
                        R[r2] = v1
                    continue
                v1 = get1()
                put1({0: v2, 1: v1 + v2, 2: v1 - v2, 3: v1 & v2, 4: v1 | v2, 5: v1 ^ v2}[op])
            elif b[:3] == "010":
                op, r = int(b[3:7], 2), int(b[7:12], 2)
                pc += 2
                if op == 0:
                    pc = R[r]
                else:
                    R[r] = {1: R[r] + 1, 2: R[r] - 1, 3: 0, 4: ~R[r], 5: -R[r], 6: R[r] + 4, 7: R[r] - 4}[op] & M
            else:
                op, r, a = int(b[3:7], 2), int(b[7:12], 2), int(b[12:36], 2)
                pc += 6
                if op == 0:
                    R[r] = s.rd(a)
                elif op == 1:
                    s.wr(a, R[r])
                elif op == 2:
                    R[r] = s.rd(s.rd(a))
                elif op == 3:
                    s.wr(s.rd(a), R[r])
                elif op == 4:
                    pc = a if R[r] != 0 else pc
                elif op == 5:
                    pc = a if R[r] == 0 else pc
                elif op == 6:
                    pc = a if sg(R[r]) < 0 else pc
                elif op == 7:
                    pc = a if sg(R[r]) >= 0 else pc
                elif op == 8:
                    R[r] = (R[r] - 1) & M
                    pc = a if R[r] != 0 else pc
                elif op == 9:
                    R[r] = (R[r] + 1) & M
                    pc = a
                elif op == 10:
                    R[r] = pc
                    pc = a
        raise Halt("no halt")


# ======================================================================= 1398
def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def fbits(x):
    return struct.unpack(">I", struct.pack(">f", x))[0]


def bitsf(u):
    return struct.unpack(">f", struct.pack(">I", u & 0xFFFFFFFF))[0]


class M1398(Machine):
    """2^29 words x 32 bits, 4-bit units (2^32 units), R0..R15 (R0 == 0).
    I  : 0000 | r | data32                    (40 bits = 10 units)
    II : op4 | r1 | r2                        (12 bits = 3 units)
    III: 1111 op4 | r1 | r2 | addr32          (48 bits = 12 units)"""
    name, unit, word_units = "1398", 4, 8
    F2 = {"mov": 1, "add": 2, "sub": 3, "and": 4, "or": 5, "xor": 6, "ctf": 7, "cti": 8, "efp": 9,
          "fadd": 10, "fsub": 11, "fmul": 12, "fdiv": 13, "fsqrt": 14}
    F3 = {"loop-": 2, "loop+": 3, "jl": 4, "jh": 5, "je": 6, "jne": 7, "fjl": 8, "fjh": 9, "fjnan1": 10,
          "fjnan2": 11, "fjden1": 12, "fjden2": 13, "fjinf1": 14, "fjinf2": 15}

    def dw_literal(self, op, ev):
        m = re.match(r"^([+-]?\d+(\.\d+)?)e([+-]\d+)$", op.strip())
        if m:  # "-1.0e+109 ; e = +109" means -1.0 x 2^109 stored as IEEE single
            return fbits(float(m.group(1)) * 2.0 ** int(m.group(3)))
        return ev(op)

    def kind(self, mnem, ops):
        if mnem == "mov":
            if ops[1].startswith("#"):
                return 1
            if all(re.match(r"^R\d+$", o.strip(), re.I) for o in ops):
                return 2
            return 3
        return 2 if mnem in self.F2 else 3

    def size(self, mnem, ops):
        return {1: 10, 2: 3, 3: 12}[self.kind(mnem, ops)]

    def encode(self, mnem, ops, ev):
        f = self.field
        R = lambda o: int(o.strip().upper().lstrip("R"))
        k = self.kind(mnem, ops)
        if k == 1:
            return "0000" + f(R(ops[0]), 4) + f(ev(ops[1][1:]), 32)
        if k == 2:
            return f(self.F2[mnem], 4) + f(R(ops[0]), 4) + f(R(ops[1]), 4)
        if mnem == "mov":
            a, b = ops
            if re.match(r"^R\d+$", a.strip(), re.I):
                m = re.match(r"^(.*)\((R\d+)\)$", b.strip(), re.I)
                return "1111" + "0000" + f(R(a), 4) + f(R(m.group(2)), 4) + f(ev(m.group(1)), 32)
            m = re.match(r"^(.*)\((R\d+)\)$", a.strip(), re.I)
            return "1111" + "0001" + f(R(b), 4) + f(R(m.group(2)), 4) + f(ev(m.group(1)), 32)
        return "1111" + f(self.F3[mnem], 4) + f(R(ops[0]), 4) + f(R(ops[1]), 4) + f(ev(ops[2]), 32)

    def run(self, image, pc=0, maxsteps=10**6, regs=None, os_addr=None):
        s = Sim(self, image)
        R = [0] * 16
        for k, v in (regs or {}).items():
            R[k] = v & 0xFFFFFFFF
        M = 0xFFFFFFFF
        sg = lambda v: (v & M) - (1 << 32) if (v & M) >> 31 else v & M
        steps = 0
        while steps < maxsteps:
            steps += 1
            R[0] = 0
            if os_addr is not None and pc == os_addr:
                return s, R, steps
            b = s.bits(pc, 48)
            n0 = int(b[0:4], 2)
            if n0 == 0:
                R[int(b[4:8], 2)] = int(b[8:40], 2)
                pc += 10
            elif n0 != 15:
                r1, r2 = int(b[4:8], 2), int(b[8:12], 2)
                pc += 3
                a, c = R[r1], R[r2]
                fa, fc = bitsf(a), bitsf(c)
                if n0 == 1:
                    v = c
                elif n0 in (2, 3, 4, 5, 6):
                    v = {2: a + c, 3: a - c, 4: a & c, 5: a | c, 6: a ^ c}[n0]
                elif n0 == 7:
                    v = fbits(float(sg(c)))
                elif n0 == 8:
                    v = int(fc) if math.isfinite(fc) else 0
                elif n0 == 9:
                    v = fbits(f32(fc - math.trunc(fc)))
                elif n0 == 14:
                    v = fbits(f32(math.sqrt(fc))) if fc >= 0 else 0x7FC00000
                else:
                    try:
                        v = fbits(f32({10: lambda: fa + fc, 11: lambda: fa - fc, 12: lambda: fa * fc, 13: lambda: fa / fc}[n0]()))
                    except (OverflowError, ZeroDivisionError):
                        v = 0x7FC00000
                R[r1] = v & M
            else:
                op, r1, r2, a = int(b[4:8], 2), int(b[8:12], 2), int(b[12:16], 2), int(b[16:48], 2)
                pc += 12
                x, y = R[r1], R[r2]
                isnan = lambda u: ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) != 0
                isden = lambda u: ((u >> 23) & 0xFF) == 0 and (u & 0x7FFFFF) != 0
                isinf = lambda u: ((u >> 23) & 0xFF) == 0xFF and (u & 0x7FFFFF) == 0
                if op == 0:
                    R[r1] = s.rd((a + R[r2]) & M)
                elif op == 1:
                    s.wr((a + R[r2]) & M, R[r1])
                elif op == 2:
                    R[r1] = (x - y) & M
                    pc = a if sg(R[r1]) > sg(y) else pc
                elif op == 3:
                    R[r1] = (x + 1) & M
                    pc = a if sg(R[r1]) < sg(y) else pc
                else:
                    cond = {4: sg(x) < sg(y), 5: sg(x) > sg(y), 6: x == y, 7: x != y,
                            8: bitsf(x) < bitsf(y), 9: bitsf(x) > bitsf(y),
                            10: isnan(x) or isnan(y), 11: isnan(x) and isnan(y),
                            12: isden(x) or isden(y), 13: isden(x) and isden(y),
                            14: isinf(x) or isinf(y), 15: isinf(x) and isinf(y)}[op]
                    if cond:
                        pc = a
        raise Halt("no halt")


def listing_rows(m, listing):
    """(addr, raw source, bit string) rows for printing."""
    return [(a, raw, bits) for a, label, mnem, ops, raw, bits in listing]


# ---------------------------------------------------------------- field layouts (for listings)
def _w1402(self, mnem, ops, bits):
    return [3, 24, 3, 24] if len(bits) == 54 else [3, 24, 3]


def _w1401(self, mnem, ops, bits):
    return [4, 1, 21, 2, 21] if len(bits) == 49 else [4, 1, 21, 2]


def _w1400(self, mnem, ops, bits):
    return {36: [3, 16, 1, 16], 20: [3, 16, 1], 52: [3, 16, 1, 16, 16]}[len(bits)]


def _w1399(self, mnem, ops, bits):
    if bits[0] == "1":
        return [1, 5, 24]
    if bits[:2] == "00":
        return [2, 4, 1, 5, 6] if mnem in ("addq", "subq", "movq") else [2, 4, 1, 5, 1, 5]
    if bits[:3] == "010":
        return [3, 4, 5]
    return [3, 4, 5, 24]


def _w1398(self, mnem, ops, bits):
    if bits[:4] == "0000":
        return [4, 4, 32]
    if bits[:4] == "1111":
        return [4, 4, 4, 4, 32]
    return [4, 4, 4]


M1402.widths, M1401.widths, M1400.widths, M1399.widths, M1398.widths = _w1402, _w1401, _w1400, _w1399, _w1398
M1402.addr_digits, M1401.addr_digits, M1400.addr_digits, M1399.addr_digits, M1398.addr_digits = 6, 6, 4, 6, 8
