"""Assembler + simulator models of the sample machines in the lecture slides (machines 1-7 and the
one-address accumulator machine)."""
import re

from asm import Machine, Sim
from machines import Halt

REG = re.compile(r"^\(?R(\d+)\)?$", re.I)
IDX = re.compile(r"^(.*)\((R\d+)\)$", re.I)


def isreg(o):
    o = o.strip()
    return bool(re.match(r"^R\d+$", o, re.I))


def regno(o):
    return int(REG.match(o.strip()).group(1))


def isparen(o):
    o = o.strip()
    return o.startswith("(") and o.endswith(")")


def inner(o):
    return o.strip()[1:-1]


def isimm(o):
    return o.strip().startswith("#")


def bare(o):
    o = o.strip()
    if isimm(o):
        return o[1:]
    if isparen(o):
        return inner(o)
    return o


def sgn(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v >> (bits - 1) else v


# ======================================================================= Machine 1
class L1(Machine):
    """128 x 16-bit cells (unit = word = 16 bits).  op 2 | addr1 7 | addr2 7."""
    name, unit, word_units, addr_digits = "M1", 16, 1, 2
    OPS = {"add": 0, "sub": 1, "mov": 2, "nop": 3}

    def size(self, mnem, ops):
        return 1

    def encode(self, mnem, ops, ev):
        a1 = ev(ops[0]) if ops else 0
        a2 = ev(ops[1]) if len(ops) > 1 else 0
        return self.field(self.OPS[mnem], 2) + self.field(a1, 7) + self.field(a2, 7)

    def widths(self, mnem, ops, bits):
        return [2, 7, 7]


# ======================================================================= Machines 2 and 3
class L2(Machine):
    """2^16 bytes, 16-bit word, big endian.  op 8 | addr1 16 | addr2 16  (5 bytes)."""
    name, unit, word_units, addr_digits = "M2", 8, 2, 4
    OPS = {"mov": 0, "add": 1, "sub": 2, "and": 3, "or": 4, "xor": 5}

    def opcode(self, mnem, ops):
        return self.OPS[mnem]

    def size(self, mnem, ops):
        return 5

    def encode(self, mnem, ops, ev):
        f = self.field
        return f(self.opcode(mnem, ops), 8) + f(ev(bare(ops[0])), 16) + f(ev(bare(ops[1])), 16)

    def widths(self, mnem, ops, bits):
        return [8, 16, 16]

    def step(self, s, op, a1, a2, pc):
        cur, val = s.rd(a1), s.rd(a2)
        s.wr(a1, {0: val, 1: cur + val, 2: cur - val, 3: cur & val, 4: cur | val, 5: cur ^ val}[op])
        return pc

    def run(self, image, pc, stop, maxsteps=200000):
        s = Sim(self, image)
        stop = set(stop) if isinstance(stop, (set, list, tuple)) else {stop}
        for _ in range(maxsteps):
            if pc in stop:
                return s, pc
            op = s.unit(pc)
            a1 = (s.unit(pc + 1) << 8) | s.unit(pc + 2)
            a2 = (s.unit(pc + 3) << 8) | s.unit(pc + 4)
            pc = self.step(s, op, a1, a2, pc + 5)
        raise Halt("no halt")


class L3(L2):
    """Machine 2 + memory-indirect operands and conditional jumps."""
    name = "M3"
    J = {"jnz": 0x80, "jz": 0x81, "jneg": 0x82, "jpos": 0x83}

    def opcode(self, mnem, ops):
        if mnem in self.J:
            return self.J[mnem]
        if mnem == "mov":
            return 2 if isparen(ops[0]) else 1 if isparen(ops[1]) else 0
        if mnem == "add":
            return 5 if isparen(ops[1]) else 3
        if mnem == "sub":
            return 6 if isparen(ops[1]) else 4
        raise KeyError(mnem)

    def step(self, s, op, a1, a2, pc):
        if op >= 0x80:
            v = sgn(s.rd(a1), 16)
            take = {0x80: v != 0, 0x81: v == 0, 0x82: v < 0, 0x83: v > 0}[op]
            return a2 if take else pc
        if op == 0:
            s.wr(a1, s.rd(a2))
        elif op == 1:
            s.wr(a1, s.rd(s.rd(a2)))
        elif op == 2:
            s.wr(s.rd(a1), s.rd(a2))
        elif op in (3, 5):
            s.wr(a1, s.rd(a1) + (s.rd(a2) if op == 3 else s.rd(s.rd(a2))))
        elif op in (4, 6):
            s.wr(a1, s.rd(a1) - (s.rd(a2) if op == 4 else s.rd(s.rd(a2))))
        return pc


# ======================================================================= Machine 4
class L4(Machine):
    """2^12 x 4-bit units, 16-bit word (4 units), R0..R15.
    I: op4 r1 r2 (3u)  II: op4 r addr12 (5u)  III: op4 r data16 (6u)"""
    name, unit, word_units, addr_digits = "M4", 4, 4, 3

    def kind(self, mnem, ops):
        a, b = ops[0], ops[1]
        if mnem == "mov":
            if isimm(b):
                return 0xD
            if isreg(a) and isreg(b):
                return 0
            if isreg(a) and isparen(b):
                return 1 if isreg(inner(b)) else 7
            if isparen(a) and isreg(b):
                return 2 if isreg(inner(a)) else 8
            return 5 if isreg(a) else 6
        if mnem == "add":
            return 0xE if isimm(b) else 3
        if mnem == "sub":
            return 0xF if isimm(b) else 4
        return {"jz": 9, "jnz": 0xA, "jneg": 0xB, "jpos": 0xC}[mnem]

    def size(self, mnem, ops):
        k = self.kind(mnem, ops)
        return 3 if k <= 4 else 5 if k <= 0xC else 6

    def encode(self, mnem, ops, ev):
        f, k = self.field, self.kind(mnem, ops)
        if k <= 4:
            return f(k, 4) + f(regno(ops[0]), 4) + f(regno(ops[1]), 4)
        if k >= 0xD:
            return f(k, 4) + f(regno(ops[0]), 4) + f(ev(bare(ops[1])), 16)
        r, a = (ops[1], ops[0]) if k in (6, 8) else (ops[0], ops[1])
        return f(k, 4) + f(regno(r), 4) + f(ev(bare(a)), 12)

    def widths(self, mnem, ops, bits):
        return {12: [4, 4, 4], 20: [4, 4, 12], 24: [4, 4, 16]}[len(bits)]

    def run(self, image, pc, stop, regs=None, maxsteps=200000):
        s = Sim(self, image)
        R = [0] * 16
        for k, v in (regs or {}).items():
            R[k] = v
        M = 0xFFFF
        for _ in range(maxsteps):
            if pc == stop:
                return s, R
            op = s.unit(pc)
            if op <= 4:
                r1, r2 = s.unit(pc + 1), s.unit(pc + 2)
                pc += 3
                if op == 0:
                    R[r1] = R[r2]
                elif op == 1:
                    R[r1] = s.rd(R[r2] & 0xFFF)
                elif op == 2:
                    s.wr(R[r1] & 0xFFF, R[r2])
                elif op == 3:
                    R[r1] = (R[r1] + R[r2]) & M
                else:
                    R[r1] = (R[r1] - R[r2]) & M
            elif op <= 0xC:
                r = s.unit(pc + 1)
                a = (s.unit(pc + 2) << 8) | (s.unit(pc + 3) << 4) | s.unit(pc + 4)
                pc += 5
                if op == 5:
                    R[r] = s.rd(a)
                elif op == 6:
                    s.wr(a, R[r])
                elif op == 7:
                    R[r] = s.rd(s.rd(a) & 0xFFF)
                elif op == 8:
                    s.wr(s.rd(a) & 0xFFF, R[r])
                else:
                    v = sgn(R[r], 16)
                    if {9: v == 0, 0xA: v != 0, 0xB: v < 0, 0xC: v > 0}[op]:
                        pc = a
            else:
                r = s.unit(pc + 1)
                d = s.rd(pc + 2)
                pc += 6
                R[r] = {0xD: d, 0xE: R[r] + d, 0xF: R[r] - d}[op] & M
        raise Halt("no halt")


# ======================================================================= Machine 5
class L5(Machine):
    """2^16 bytes, 16-bit word, R0..R63.
    I: op4 r1 6 r2 6 (2B)   II: op4 r1 6 r2 6 addr16 (4B)   III: 1111 op6 r6 data16 (4B)"""
    name, unit, word_units, addr_digits = "M5", 8, 2, 4
    F1 = {"mov": 0, "add": 1, "sub": 2, "and": 3, "or": 4, "xor": 5}
    J = {"je": 0xA, "jne": 0xB, "jl": 0xC, "jh": 0xD}

    def kind(self, mnem, ops):
        if mnem in self.J:
            return "II", self.J[mnem]
        if mnem == "call":
            return "II", 0xE
        if len(ops) == 3:
            return ("II", 8) if isreg(ops[0]) else ("II", 9)
        a, b = ops
        if isimm(b):
            return "III", self.F1[mnem]
        if mnem == "mov" and not (isreg(a) and isreg(b)):
            return ("II", 6) if isreg(a) else ("II", 7)
        return "I", self.F1[mnem]

    def size(self, mnem, ops):
        return 2 if self.kind(mnem, ops)[0] == "I" else 4

    def encode(self, mnem, ops, ev):
        f = self.field
        fmt, op = self.kind(mnem, ops)
        if fmt == "I":
            return f(op, 4) + f(regno(ops[0]), 6) + f(regno(ops[1]), 6)
        if fmt == "III":
            return "1111" + f(op, 6) + f(regno(ops[0]), 6) + f(ev(bare(ops[1])), 16)
        if op == 6:
            m = IDX.match(ops[1].strip())
            r1, r2, a = ops[0], m.group(2), m.group(1)
        elif op == 7:
            m = IDX.match(ops[0].strip())
            r1, r2, a = ops[1], m.group(2), m.group(1)
        elif op == 8:
            r1, r2, a = ops
        elif op == 9:
            a, r1, r2 = ops
        elif op == 0xE:
            m = IDX.match(ops[1].strip())
            r1, r2, a = ops[0], m.group(2), m.group(1)
        else:
            r1, r2, a = ops
        return f(op, 4) + f(regno(r1), 6) + f(regno(r2), 6) + f(ev(a), 16)

    def widths(self, mnem, ops, bits):
        if len(bits) == 16:
            return [4, 6, 6]
        return [10, 6, 16] if bits[:4] == "1111" else [4, 6, 6, 16]

    def run(self, image, pc, stop, regs=None, maxsteps=500000):
        s = Sim(self, image)
        R = [0] * 64
        for k, v in (regs or {}).items():
            R[k] = v & 0xFFFF
        for _ in range(maxsteps):
            if pc == stop:
                return s, R
            w = s.rd(pc)
            op = w >> 12
            if op <= 5:
                r1, r2 = (w >> 6) & 63, w & 63
                pc += 2
                R[r1] = {0: R[r2], 1: R[r1] + R[r2], 2: R[r1] - R[r2], 3: R[r1] & R[r2],
                         4: R[r1] | R[r2], 5: R[r1] ^ R[r2]}[op] & 0xFFFF
            elif op <= 14:
                r1, r2, a = (w >> 6) & 63, w & 63, s.rd(pc + 2)
                pc += 4
                if op == 6:
                    R[r1] = s.rd((a + R[r2]) & 0xFFFF)
                elif op == 7:
                    s.wr((a + R[r2]) & 0xFFFF, R[r1])
                elif op == 8:
                    R[r1] = R[r2]
                    R[r2] = s.rd(a)
                elif op == 9:
                    s.wr(a, R[r1])
                    R[r1] = R[r2]
                elif op == 14:
                    R[r1] = pc
                    pc = (a + R[r2]) & 0xFFFF
                else:
                    x, y = sgn(R[r1], 16), sgn(R[r2], 16)
                    if {10: x == y, 11: x != y, 12: x < y, 13: x > y}[op]:
                        pc = a
            else:
                sub, r, d = (w >> 6) & 0x3F, w & 63, s.rd(pc + 2)
                pc += 4
                R[r] = {0: d, 1: R[r] + d, 2: R[r] - d, 3: R[r] & d, 4: R[r] | d, 5: R[r] ^ d}[sub] & 0xFFFF
        raise Halt("no halt")


# ======================================================================= one-address machine
class L1A(Machine):
    """2^16 x 4-bit units, 16-bit word (4 units), accumulator.  op 4 | addr/data 16  (5 units)."""
    name, unit, word_units, addr_digits = "1A", 4, 4, 4
    OTHER = {"sub": 5, "and": 6, "or": 7, "xor": 8, "j": 0xB, "jz": 0xC, "jnz": 0xD, "jn": 0xE, "jp": 0xF}

    def opcode(self, mnem, ops):
        a = ops[0] if ops else ""
        if mnem == "load":
            return 0 if isimm(a) else 9 if isparen(a) else 2
        if mnem == "add":
            return 1 if isimm(a) else 4
        if mnem == "store":
            return 0xA if isparen(a) else 3
        return self.OTHER[mnem]

    def size(self, mnem, ops):
        return 5

    def encode(self, mnem, ops, ev):
        return self.field(self.opcode(mnem, ops), 4) + self.field(ev(bare(ops[0])), 16)

    def widths(self, mnem, ops, bits):
        return [4, 16]

    def run(self, image, pc, stop, maxsteps=200000):
        s = Sim(self, image)
        acc = 0
        for _ in range(maxsteps):
            if pc == stop:
                return s, acc
            op = s.unit(pc)
            d = s.rd(pc + 1)
            pc += 5
            if op == 0:
                acc = d
            elif op == 1:
                acc = (acc + d) & 0xFFFF
            elif op == 2:
                acc = s.rd(d)
            elif op == 3:
                s.wr(d, acc)
            elif op in (4, 5, 6, 7, 8):
                v = s.rd(d)
                acc = {4: acc + v, 5: acc - v, 6: acc & v, 7: acc | v, 8: acc ^ v}[op] & 0xFFFF
            elif op == 9:
                acc = s.rd(s.rd(d))
            elif op == 0xA:
                s.wr(s.rd(d), acc)
            else:
                a = sgn(acc, 16)
                if {0xB: True, 0xC: a == 0, 0xD: a != 0, 0xE: a < 0, 0xF: a > 0}[op]:
                    pc = d
        raise Halt("no halt")


# ======================================================================= Machine 6 (stack)
class L6(Machine):
    """2^32 bytes, 32-bit word, 16-word hardware stack.  I: op8 addr/data32 (5B)  II: op8 (1B)"""
    name, unit, word_units, addr_digits = "M6", 8, 4, 8
    OPS2 = {"add": 3, "sub": 4, "swap": 5, "sp++": 6, "sp--": 7, "j": 8, "jz": 9, "jnz": 0xA, "jn": 0xB}

    def size(self, mnem, ops):
        return 5 if mnem in ("push", "pop") else 1

    def encode(self, mnem, ops, ev):
        f = self.field
        if mnem == "push":
            return f(0 if isimm(ops[0]) else 1, 8) + f(ev(bare(ops[0])), 32)
        if mnem == "pop":
            return f(2, 8) + f(ev(ops[0]), 32)
        return f(self.OPS2[mnem], 8)

    def widths(self, mnem, ops, bits):
        return [8, 32] if len(bits) == 40 else [8]

    def run(self, image, pc, stop, maxsteps=200000):
        s = Sim(self, image)
        st, sp = [0] * 16, 0
        M = 0xFFFFFFFF
        for _ in range(maxsteps):
            if pc == stop:
                return s, st, sp
            op = s.unit(pc)
            if op <= 2:
                d = s.rd(pc + 1)
                pc += 5
                if op == 0:
                    st[sp] = d
                    sp += 1
                elif op == 1:
                    st[sp] = s.rd(d)
                    sp += 1
                else:
                    sp -= 1
                    s.wr(d, st[sp])
            else:
                pc += 1
                if op == 3:
                    st[sp - 2] = (st[sp - 2] + st[sp - 1]) & M
                    sp -= 1
                elif op == 4:
                    st[sp - 2] = (st[sp - 2] - st[sp - 1]) & M
                    sp -= 1
                elif op == 5:
                    st[sp - 1], st[sp - 2] = st[sp - 2], st[sp - 1]
                elif op == 6:
                    sp += 1
                elif op == 7:
                    sp -= 1
                elif op == 8:
                    pc = st[sp - 1]
                    sp -= 1
                else:
                    c = sgn(st[sp - 2], 32)
                    if {9: c == 0, 0xA: c != 0, 0xB: c < 0}[op]:
                        pc = st[sp - 1]
                    sp -= 2
            if not 0 <= sp <= 16:
                raise Halt("stack error")
        raise Halt("no halt")


# ======================================================================= Machine 7
class L7(Machine):
    """2^32 bytes, 32-bit word (two's complement), accumulator.
    I: op8 addr/data32 (5B)   II: op8 disp8 (2B), PC-relative"""
    name, unit, word_units, addr_digits = "M7", 8, 4, 8
    F1 = {"add": 4, "sub": 5, "addi": 6, "subi": 7, "jmpl": 8}
    F2 = {"jnz": 0x80, "jz": 0x81, "jneg": 0x82, "jpos": 0x83, "jmp": 0x84}

    def size(self, mnem, ops):
        return 2 if mnem in self.F2 else 5

    def encode(self, mnem, ops, ev):
        f = self.field
        if mnem in self.F2:
            d = ev(ops[0]) - (self.here + 2)
            assert -128 <= d <= 127, (mnem, ops, d)
            return f(self.F2[mnem], 8) + f(d, 8)
        if mnem == "load":
            op = 1 if isparen(ops[0]) else 0
        elif mnem == "store":
            op = 3 if isparen(ops[0]) else 2
        else:
            op = self.F1[mnem]
        return f(op, 8) + f(ev(bare(ops[0])), 32)

    def widths(self, mnem, ops, bits):
        return [8, 32] if len(bits) == 40 else [8, 8]

    def run(self, image, pc, stop, maxsteps=5_000_000):
        s = Sim(self, image)
        acc, M = 0, 0xFFFFFFFF
        for n in range(maxsteps):
            if pc == stop:
                return s, n
            op = s.unit(pc)
            if op < 0x80:
                d = s.rd(pc + 1)
                pc += 5
                if op == 0:
                    acc = s.rd(d)
                elif op == 1:
                    acc = s.rd(s.rd(d))
                elif op == 2:
                    s.wr(d, acc)
                elif op == 3:
                    s.wr(s.rd(d), acc)
                elif op == 8:
                    pc = d
                else:
                    acc = {4: acc + s.rd(d), 5: acc - s.rd(d), 6: acc + d, 7: acc - d}[op] & M
            else:
                disp = sgn(s.unit(pc + 1), 8)
                pc += 2
                a = sgn(acc, 32)
                if {0x80: a != 0, 0x81: a == 0, 0x82: a < 0, 0x83: a >= 0, 0x84: True}[op]:
                    pc = (pc + disp) & M
        raise Halt("no halt")
