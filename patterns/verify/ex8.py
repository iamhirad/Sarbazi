"""Checks and traces for the chapter-8 exercises (RX instructions and branches)."""
from ibm360 import CPU, CCSTR, assemble, s32, Halt
from ibm360_tests import one
import programs360 as P

# 8-1 encoding (TAB = (R12)+3A0h, LOOP = (R12)+20h)
SY = {"TAB": 0x10000 + 0x3A0, "LOOP": 0x10000 + 0x20}
ENC = ["L     5,TAB(6)", "ST    7,0(,9)", "LA    1,4095(2,3)", "BC    4,LOOP", "BNE   8(14)",
       "BCT   6,LOOP", "C     0,TAB+8", "A     3,12(0,5)", "BR    14", "NOPR  0"]
for l in ENC:
    code, cpu, row = one("         " + l, syms=SY)
    print("ENC", l, code)

# 8-3 address calculation and effects
print("L", one("         L     2,20(4,3)", regs={3: 0x12000, 4: 0x10}, mem={0x12024: 77})[1].R[2])
c = one("         LA    5,1(5)", regs={5: 0xFFFFFFFF})[1]
print("LA wrap %08X" % c.R[5])
c = one("         LA    5,8")[1]
print("LA 5,8 ->", c.R[5])
c = one("         L     5,8", mem={8: 1234})[1]
print("L 5,8 ->", c.R[5])
# D using the same register as index and dividend
c = one("         D     2,0(2,9)", regs={2: 0, 3: 100, 9: 0x40000}, mem={0x40000: 7})[1]
print("D 2,0(2,9)", s32(c.R[3]), s32(c.R[2]), CCSTR[c.cc])
c = one("         M     4,0(4,9)", regs={4: 8, 5: -3, 9: 0x40000}, mem={0x40008: 11})[1]
print("M 4,0(4,9)", s32(c.R[4]), s32(c.R[5]), CCSTR[c.cc])
# masks
for cc in range(4):
    print("CC", CCSTR[cc], "taken masks", [m for m in range(16) if m & (8 >> cc)])
# trace of sumarr
a = assemble(P.P360["sumarr"][1])
cpu = CPU(a.image)
cpu.pc = a.entry
rows = {r["loc"]: r for r in a.rows if r["kind"] == "ins"}
n = 0
try:
    while n < 60:
        r = rows[cpu.pc]
        cpu.step()
        n += 1
        if n <= 14 or r["mn"] in ("ST", "EOJ"):
            print("%04X %-6s %-10s R3=%d R4=%d R5=%d PC=%04X" % (r["loc"], r["mn"], r["ops"], s32(cpu.R[3]), cpu.R[4], s32(cpu.R[5]), cpu.pc))
except Halt as h:
    print("halt", h, n)
P.run_programs360()
