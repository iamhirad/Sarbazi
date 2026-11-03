import random
from machines import *

# ---------------- 1402 Q3
P1402 = """
        org 0
        mov s+4, c+4
        and s+4, c
here:   jz  here+14
        sub s, #FFFFFFh
        add c+4, s-4
        jnz here-18
        jz  OS
        org 100h
c:      dw ?, 1
s:      dw 0, ?
        org 200h
OS:     dw 0
"""
m = M1402(); img, lst = m.assemble(P1402)
print({k: hex(v) for k, v in m.sym.items()})
for cval in [0, 1, 0b1011, 0xFFFFFF, 0x800001, random.getrandbits(24)]:
    im = dict(img); s0 = Sim(m, im); s0.wr(0x100, cval)
    s, steps = m.run(s0.mem, os_addr=m.sym["OS"])
    print("1402 c=%06X s=%d popcount=%d c+4=%d steps=%d" % (cval, s.rd(0x108), bin(cval).count("1"), s.rd(0x104), steps))

# ---------------- 1401 Q3 (43Dh as immediate and as direct)
for variant in ["#43Dh", "43Dh"]:
    P1401 = f"""
        org 1
        xor a, c-3
loop:   add a, #-2
next:   xor loop+1, {variant}
        dec c
        jnz loop
        jmp (1FFFFDh)
        org 100h
a:      dw 123456h
c:      dw 10
arr:    dw 100 dup(?)
k:      dw 13
"""
    m = M1401(); img, lst = m.assemble(P1401)
    s, steps = m.run(img, pc=1)
    print("1401", variant, {k: hex(v) for k, v in m.sym.items()}, "a =", s.signed(s.rd(0x100)), "c =", s.rd(0x103), "steps", steps,
          "loop instr restored:", [s.unit(8 + i) for i in range(7)] == [img[8 + i] for i in range(7)])

# ---------------- 1400 Q3
P1400 = """
        org 100h
        mov B-396, A+400
Arr:    dw 200Bh, 2005h, 1200h
        dw B200h, 5520h, 150h
        dw 130, 29, 4
        add Arr+10, #8
        add Arr+14, #4
        jne Arr+5, #B-8, Arr
        jmp (FFFEh)
A:      dw 100 dup(0)
B:      dw 1
"""
m = M1400(); img, lst = m.assemble(P1400)
print({k: hex(v) for k, v in m.sym.items()})
img, lst = M1400().assemble(P1400.replace("org 100h","org 0")); m=M1400(); m.assemble(P1400.replace("org 100h","org 0")); s, steps = m.run(img, pc=0)
A = [s.signed(s.rd(m.sym["A"] + 4 * i)) for i in range(100)]
print("1400 A[:12] =", A[:12], "steps", steps, "B =", s.rd(m.sym["B"]))
f = [0, 1]
while len(f) < 100: f.append((f[-1] + f[-2]) & 0xFFFF)
print("1400 A == fib mod 2^16 ?", [a & 0xFFFF for a in A] == f)

# ---------------- 1399 Q3
P1399 = """
        org 0
        mov R1,#100
        mov R0,#array
        dw 41006h
        mov R1,#807004h
loop:   subq R1,4
        mov R2,R0
        sub R2,R1
        jneg R2,loop-6
        jmp R31
array:  dw 100 dup(?)
"""
m = M1399(); img, lst = m.assemble(P1399)
print({k: hex(v) for k, v in m.sym.items()})
s0 = Sim(m, img)
vals = list(range(1000, 1100))
for i, v in enumerate(vals): s0.wr(m.sym["array"] + 4 * i, v)
s, R, steps = m.run(s0.mem)
out = [s.rd(m.sym["array"] + 4 * i) for i in range(100)]
print("1399 first 30 after:", out[:30], "rest unchanged:", out[26:] == vals[26:], "R0,R1:", R[0], R[1], "steps", steps)

# ---------------- 1398 Q3
P1398 = """
        org 0
float1: dw -1.0e+109
int1:   dw 3300000h
array:  dw 100 dup(?)
        dw 5000000h,1040000h
        dw 80100h, 3200Ah, 0
        mov R11,R0
loop:   mov R2,array-8(R1)
        dw -40.5e+112
        dw 38BFC22h,39Ah
        loop- R1,R4,loop
out1:   add R10,R5
        loop- R1,R4,loop
out2:   add R11,R5
        loop- R1,R4,loop
        je R0,R0,OS
        org 1000h
OS:     dw 0
"""
m = M1398(); img, lst = m.assemble(P1398)
print({k: hex(v) for k, v in m.sym.items()})
print("float1 bits %08X, -40.5e112 bits %08X" % (fbits(-1.0 * 2**109), fbits(-40.5 * 2**112)))
NAN, DEN = 0x7FC00001, 0x00000005
for case in ["random", "elem0nan", "elem1nan", "elem1den", "none"]:
    random.seed(7)
    arr = [fbits(random.uniform(-5, 5)) for _ in range(100)]
    if case == "random":
        for i in random.sample(range(100), 15): arr[i] = NAN
        for i in random.sample(range(100), 10):
            if arr[i] != NAN: arr[i] = DEN
    if case == "elem0nan": arr[0] = NAN
    if case == "elem1nan": arr[1] = NAN
    if case == "elem1den": arr[1] = DEN
    s0 = Sim(m, img)
    for i, v in enumerate(arr): s0.wr(m.sym["array"] + 8 * i, v)
    s, R, steps = m.run(s0.mem, regs={k: 7 for k in range(1, 16)}, os_addr=m.sym["OS"])
    nn = sum(1 for v in arr[1:] if v == NAN); nd = sum(1 for v in arr[1:] if v == DEN)
    print("1398 %-9s R10=%d R11=%d  (#NaN in A[1..99]=%d, #den=%d)  R1=%d R4=%d R5=%d steps=%d" % (case, R[10], R[11], nn, nd, R[1], R[4], R[5], steps))
