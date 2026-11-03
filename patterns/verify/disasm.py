"""Disassemble the instruction actually found at an address (for the 'hidden instruction' tables)."""
from asm import Sim
from machines import M1398, M1399, M1400, M1401, M1402


def dis1398(s, pc):
    b = s.bits(pc, 48); n0 = int(b[:4], 2)
    if n0 == 0:
        return 10, "mov R%d,#%Xh" % (int(b[4:8], 2), int(b[8:40], 2))
    if n0 != 15:
        names = {v: k for k, v in M1398.F2.items()}
        return 3, "%s R%d,R%d" % (names[n0], int(b[4:8], 2), int(b[8:12], 2))
    op = int(b[4:8], 2); r1, r2, a = int(b[8:12], 2), int(b[12:16], 2), int(b[16:48], 2)
    if op == 0:
        return 12, "mov R%d,%Xh(R%d)" % (r1, a, r2)
    if op == 1:
        return 12, "mov %Xh(R%d),R%d" % (a, r2, r1)
    names = {v: k for k, v in M1398.F3.items()}
    return 12, "%s R%d,R%d,%Xh" % (names[op], r1, r2, a)


def dis1399(s, pc):
    b = s.bits(pc, 36)
    if b[0] == "1":
        return 5, "mov R%d,#%Xh" % (int(b[1:6], 2), int(b[6:30], 2))
    if b[:2] == "00":
        names = {v: k for k, v in M1399.F1.items()}
        op = int(b[2:6], 2)
        o1 = ("(R%d)" if b[6] == "1" else "R%d") % int(b[7:12], 2)
        if op in (7, 8, 9):
            return 3, "%s %s,%d" % (names[op], o1, int(b[12:18], 2))
        o2 = ("(R%d)" if b[12] == "1" else "R%d") % int(b[13:18], 2)
        return 3, "%s %s,%s" % (names[op], o1, o2)
    if b[:3] == "010":
        names = {v: k for k, v in M1399.F2.items()}
        return 2, "%s R%d" % (names[int(b[3:7], 2)], int(b[7:12], 2))
    op = int(b[3:7], 2); r = int(b[7:12], 2); a = int(b[12:36], 2)
    names = {0: "mov R%d,%Xh", 1: "mov %Xh,R%d", 2: "mov R%d,(%Xh)", 3: "mov (%Xh),R%d"}
    if op == 1 or op == 3:
        return 6, names[op] % (a, r)
    if op in names:
        return 6, names[op] % (r, a)
    inv = {v: k for k, v in M1399.F3.items()}
    return 6, "%s R%d,%Xh" % (inv[op], r, a)


def dis1400(s, pc):
    b = s.bits(pc, 52); op = int(b[:3], 2); a1 = int(b[3:19], 2)
    if op in (3, 4):
        x = b[19]
        return 5, {("3", "0"): "inc %Xh", ("3", "1"): "dec %Xh", ("4", "0"): "jmp (%Xh)", ("4", "1"): "call %Xh"}[(str(op), x)] % a1
    d = b[19]; a2 = int(b[20:36], 2)
    o2 = ("#%Xh" if d == "1" else "%Xh") % a2
    if op <= 2:
        return 9, "%s %Xh,%s" % (["mov", "add", "sub"][op], a1, o2)
    return 13, "%s %Xh,%s,%Xh" % ({5: "je", 6: "jne", 7: "jl"}[op], a1, o2, int(b[36:52], 2))


def dis1401(s, pc):
    b = s.bits(pc, 49); op = int(b[:4], 2); i = b[4]; a1 = int(b[5:26], 2); xy = b[26:28]
    o1 = ("(%Xh)" if i == "1" else "%Xh") % a1
    if xy == "11":
        inv = {v: k for k, v in M1401.OPS2.items()}
        return 4, "%s %s" % (inv[op], o1)
    a2 = int(b[28:49], 2)
    o2 = {"00": "%Xh", "01": "(%Xh)", "10": "#%Xh"}[xy] % a2
    inv = {v: k for k, v in M1401.OPS.items()}
    return 7, "%s %s,%s" % (inv[op], o1, o2)
