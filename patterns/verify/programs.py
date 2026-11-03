"""Every program shown in the patterns sheet, with a test that runs it on the machine model.

run_all() asserts all of them; build.py imports PROGRAMS to print the exact verified source.
"""
import math
import random

from asm import Sim
from machines import M1398, M1399, M1400, M1401, M1402, bitsf, fbits

PROGRAMS = {}


def prog(pid, machine, src):
    PROGRAMS[pid] = (machine, src.strip("\n"))
    return pid


def load(m, src, data=None):
    img, lst = m.assemble(src)
    s = Sim(m, img)
    for k, v in (data or {}).items():
        s.wr(m.sym[k] if isinstance(k, str) else k, v)
    return s.mem


def words(s, base, n, signed=True):
    return [s.signed(s.rd(base + s.m.word_units * i)) if signed else s.rd(base + s.m.word_units * i) for i in range(n)]


def setarr(m, mem, base, vals):
    s = Sim(m, mem)
    for i, v in enumerate(vals):
        s.wr(base + m.word_units * i, v)
    return s.mem


def run1402(src, data=None, arrays=None):
    m = M1402()
    mem = load(m, src, data)
    for name, vals in (arrays or {}).items():
        mem = setarr(m, mem, m.sym[name], vals)
    s, steps = m.run(mem, pc=0, os_addr=m.sym["OS"])
    return m, s


OS1402 = "\n        org 7000h\nOS:     dw 0"

# ======================================================================
# Basic patterns (1402 notation: memory-to-memory, PSR z s)
# ======================================================================
prog("swap_xor", M1402, """
        xor  a, b          ; a = a^b
        xor  b, a          ; b = b^(a^b) = a
        xor  a, b          ; a = (a^b)^a = b
        jmp  OS
a:      dw   1234h
b:      dw   0ABCDEh""")

prog("swap_tmp", M1402, """
        mov  t, a
        mov  a, b
        mov  b, t
        jmp  OS
a:      dw   5
b:      dw   9
t:      dw   ?""")

prog("swap_ptr", M1402, """
        xor  (p), (q)      ; swap *p and *q
        xor  (q), (p)
        xor  (p), (q)
        jmp  OS
p:      dw   x
q:      dw   y
x:      dw   7
y:      dw   3""")

prog("zero_inc", M1402, """
        xor  x, x          ; x = 0 (or mov x,#0)
        sub  x, #FFFFFFh   ; x = x - (-1) = x + 1
        add  x, #FFFFFFh   ; x = x + (-1) = x - 1
        add  y, #0         ; PSR <- y, y unchanged
        jneg yneg
        jmp  OS
yneg:   mov  flag, #1
        jmp  OS
x:      dw   77
y:      dw   -5
flag:   dw   0""")

prog("count_loop", M1402, """
        mov  n, #10        ; repeat 10 times
        mov  sum, #0
loop:   add  sum, n        ; body: sum = 10+9+...+1
        sub  n, #1
        jnz  loop
        jmp  OS
n:      dw   ?
sum:    dw   ?""")

prog("arr_sum", M1402, """
        mov  p, #A         ; p -> A[0]
        mov  n, #100
        mov  sum, #0
loop:   add  sum, (p)      ; sum += A[i]
        add  p, #4         ; next word = 4 units
        sub  n, #1
        jnz  loop
        jmp  OS
p:      dw   ?
n:      dw   ?
sum:    dw   ?
A:      dw   100 dup(?)""")

prog("arr_max", M1402, """
        mov  p, #A
        mov  mx, (p)       ; mx = A[0]
        mov  n, #99
loop:   add  p, #4
        mov  t, (p)
        sub  t, mx         ; t = A[i] - mx
        jneg skip
        mov  mx, (p)       ; new maximum
skip:   sub  n, #1
        jnz  loop
        jmp  OS
p:      dw   ?
n:      dw   ?
mx:     dw   ?
t:      dw   ?
A:      dw   100 dup(?)""")

prog("arr_count_neg", M1402, """
        mov  p, #A
        mov  n, #100
        mov  cnt, #0
loop:   mov  t, #0
        or   t, (p)        ; t = A[i], PSR <- A[i]
        jneg neg
        jmp  next
neg:    add  cnt, #1
next:   add  p, #4
        sub  n, #1
        jnz  loop
        jmp  OS
p:      dw   ?
n:      dw   ?
cnt:    dw   ?
t:      dw   ?
A:      dw   100 dup(?)""")

prog("reverse", M1402, """
        mov  p, #A         ; p -> first
        mov  q, #A+396     ; q -> last (99 x 4)
loop:   mov  t, q
        sub  t, p          ; t = q - p
        jneg done          ; pointers crossed
        jz   done          ; or met
        xor  (p), (q)      ; swap A[i], A[j]
        xor  (q), (p)
        xor  (p), (q)
        add  p, #4
        sub  q, #4
        jmp  loop
done:   jmp  OS
p:      dw   ?
q:      dw   ?
t:      dw   ?
A:      dw   100 dup(?)""")

prog("fib_sum", M1402, """
        mov  a, #0         ; F0
        mov  b, #1         ; F1
        mov  sum, #1       ; F0 + F1
        mov  n, #49        ; 2 terms per pass
loop:   add  a, b          ; a = F2, F4, ...
        add  sum, a
        add  b, a          ; b = F3, F5, ...
        add  sum, b
        sub  n, #1
        jnz  loop
        jmp  OS
a:      dw   ?
b:      dw   ?
sum:    dw   ?
n:      dw   ?""")

prog("fib_fill", M1402, """
        mov  p, #A
        mov  (p), #0       ; A[0] = 0
        add  p, #4
        mov  (p), #1       ; A[1] = 1
        mov  n, #98
loop:   mov  t, (p)        ; t = A[i-1]
        sub  p, #4
        add  t, (p)        ; t = A[i-1] + A[i-2]
        add  p, #8
        mov  (p), t        ; A[i] = t
        sub  n, #1
        jnz  loop
        jmp  OS
p:      dw   ?
n:      dw   ?
t:      dw   ?
A:      dw   100 dup(?)""")

prog("mul_add", M1402, """
        mov  r, #0         ; r = a*b  (b >= 0)
        mov  t, #0
        or   t, b          ; test b
        jz   done
loop:   add  r, a
        sub  b, #1
        jnz  loop
done:   jmp  OS
a:      dw   -7
b:      dw   12
r:      dw   ?
t:      dw   ?""")

prog("mul_shift", M1402, """
        mov  r, #0         ; r = a*b, shift-and-add
        mov  mask, #1
loop:   mov  t, b
        and  t, mask       ; is this bit of b set?
        jz   skip
        add  r, a          ; r += a * 2^k
skip:   add  a, a          ; a <<= 1
        add  mask, mask    ; mask <<= 1
        jnz  loop          ; 24 passes (mask -> 0)
        jmp  OS
a:      dw   1234
b:      dw   567
r:      dw   ?
mask:   dw   ?
t:      dw   ?""")

prog("divmod", M1402, """
        mov  q, #0         ; x / y  (x >= 0, y > 0)
loop:   sub  x, y          ; repeated subtraction
        jneg done
        add  q, #1
        jmp  loop
done:   add  x, y          ; x = remainder
        jmp  OS
x:      dw   100
y:      dw   7
q:      dw   ?""")

prog("popcount", M1402, """
        mov  cnt, #0
        mov  mask, #1
loop:   mov  t, x
        and  t, mask       ; z=1 if bit is 0
        jz   skip
        add  cnt, #1
skip:   add  mask, mask    ; next bit
        jnz  loop          ; 24 bits (mask -> 0)
        jmp  OS
x:      dw   0B5A3h
cnt:    dw   ?
mask:   dw   ?
t:      dw   ?""")

prog("pow2", M1402, """
        mov  t, x          ; x & (x-1) == 0 ?
        sub  t, #1
        and  t, x
        jz   yes
        mov  res, #0
        jmp  OS
yes:    mov  res, #1
        jmp  OS
x:      dw   4096
res:    dw   ?
t:      dw   ?""")

prog("abs", M1402, """
        add  x, #0         ; PSR <- x
        jneg negx
        jmp  OS
negx:   xor  x, #FFFFFFh   ; -x = not(x) + 1
        add  x, #1
        jmp  OS
x:      dw   -37""")

prog("max2", M1402, """
        mov  mx, a
        mov  t, b
        sub  t, a          ; t = b - a
        jneg done
        mov  mx, b
done:   jmp  OS
a:      dw   -4
b:      dw   9
mx:     dw   ?
t:      dw   ?""")

prog("altsum", M1402, """
        mov  s, #0         ; s = running sum
        mov  p, #A
        mov  n, #50        ; two elements per pass
loop:   add  s, (p)        ; even j: +A[j]
        mov  (p), s
        add  p, #4
        sub  s, (p)        ; odd j:  -A[j]
        mov  (p), s
        add  p, #4
        sub  n, #1
        jnz  loop
        jmp  OS
s:      dw   ?
p:      dw   ?
n:      dw   ?
A:      dw   100 dup(?)""")

prog("prefix", M1402, """
        mov  s, #0         ; A[i] = A[0]+...+A[i]
        mov  p, #A
        mov  n, #100
loop:   add  s, (p)
        mov  (p), s
        add  p, #4
        sub  n, #1
        jnz  loop
        jmp  OS
s:      dw   ?
p:      dw   ?
n:      dw   ?
A:      dw   100 dup(?)""")

prog("gnome", M1402, """
        mov  p, #A         ; p -> A[i]
loop:   mov  q, p
        add  q, #4         ; q -> A[i+1]
        mov  t, (q)
        sub  t, (p)        ; t = A[i+1] - A[i]
        jneg swap          ; out of order?
        add  p, #4         ; in order: i = i + 1
        mov  t, p
        sub  t, #A+396     ; at last element?
        jnz  loop
        jmp  OS
swap:   xor  (p), (q)      ; xor swap A[i], A[i+1]
        xor  (q), (p)
        xor  (p), (q)
        mov  t, p
        sub  t, #A         ; i = 0 ?  then stay
        jz   loop
        sub  p, #4         ; else i = i - 1
        jmp  loop
p:      dw   ?
q:      dw   ?
t:      dw   ?
A:      dw   100 dup(?)""")

prog("bubble", M1402, """
        mov  pass, #99
outer:  mov  p, #A
        mov  n, pass       ; compare pass pairs
inner:  mov  q, p
        add  q, #4
        mov  t, (q)
        sub  t, (p)        ; A[i+1] - A[i]
        jneg swap
        jmp  next
swap:   xor  (p), (q)
        xor  (q), (p)
        xor  (p), (q)
next:   add  p, #4
        sub  n, #1
        jnz  inner
        sub  pass, #1      ; largest is now in place
        jnz  outer
        jmp  OS
pass:   dw   ?
n:      dw   ?
p:      dw   ?
q:      dw   ?
t:      dw   ?
A:      dw   100 dup(?)""")

prog("selfmod_walk", M1402, """
        mov  n, #100
loop:   add  sum, A        ; addr2 field walks A
        add  loop+5, #4    ; addr2 = units 5..8
        sub  n, #1
        jnz  loop
        jmp  OS
n:      dw   ?
sum:    dw   0
A:      dw   100 dup(?)""")

prog("toggle", M1402, """
        mov  n, #10
loop:   add  x, #1         ; data: 1,0,1,0,...
        xor  loop+5, #1    ; flip bit 0 of data
        sub  n, #1
        jnz  loop
        jmp  OS
n:      dw   ?
x:      dw   0""")


# ======================================================================
# Past midterms: Q2 solutions
# ======================================================================
prog("q1402", M1402, """
        org  0
        mov  s, #0         ; running alternating sum
        mov  p, #A
        mov  n, #50
loop:   add  s, (p)        ; j even: s += A[j]
        mov  (p), s        ; A[j] = s
        add  p, #4
        sub  s, (p)        ; j odd:  s -= A[j]
        mov  (p), s
        add  p, #4
        sub  n, #1
        jnz  loop
        jmp  OS_Control_Point
s:      dw   ?
p:      dw   ?
n:      dw   ?
A:      dw   100 dup(?)""")

prog("q1401_template", M1401, """
        org  100h
loop1:  mov  ptr2, ptr1      ; ptr2 = ptr1
        add  ptr2, #3        ; next word (3 units)
loop2:  cmp  (ptr2), (ptr1)  ; A[i+1] - A[i]
        jpos cont            ; > 0 : in order
        xor  (ptr1), (ptr2)  ; xor swap
        xor  (ptr2), (ptr1)
        xor  (ptr1), (ptr2)
        dec  ptr1            ; ptr1 -= 3
        sub  ptr1, #2
        jmp  loop1
cont:   add  ptr1, #3
        cmp  ptr1, #A+297    ; at A[99]? (99x3)
        jnz  loop1
        jmp  (1FFFFDh)
A:      dw   100 dup(0)
ptr1:   dw   A
ptr2:   dw   ?""")

prog("q1401_safe", M1401, """
        org  100h
loop1:  mov  ptr2, ptr1
        add  ptr2, #3
        cmp  (ptr2), (ptr1)  ; A[i+1] - A[i]
        jneg swap            ; real inversion only
        add  ptr1, #3
        cmp  ptr1, #A+297
        jnz  loop1
        jmp  (1FFFFDh)
swap:   xor  (ptr1), (ptr2)
        xor  (ptr2), (ptr1)
        xor  (ptr1), (ptr2)
        cmp  ptr1, #A        ; at A[0]: stay
        jz   loop1
        sub  ptr1, #3
        jmp  loop1
A:      dw   100 dup(0)
ptr1:   dw   A
ptr2:   dw   ?""")

prog("q1400", M1400, """
        org  0
        mov  a, #0         ; F0
        mov  b, #1         ; F1
        mov  sum, #1       ; F0 + F1
        mov  n, #49        ; 2 terms per pass
loop:   add  a, b          ; a = F2, F4, ...
        add  sum, a
        add  b, a          ; b = F3, F5, ...
        add  sum, b
        dec  n
        jne  n, #0, loop
        jmp  (FFFEh)       ; return address
a:      dw   ?
b:      dw   ?
sum:    dw   ?
n:      dw   ?""")

prog("q1399", M1399, """
        org  0
        mov  R1,#array       ; p -> A[i]
        mov  R5,#array+396   ; -> A[99] (99x4)
        mov  R6,#array
loop:   mov  R2,R1
        inc4 R2              ; q -> A[i+1]
        mov  R3,(R2)
        sub  R3,(R1)         ; A[i+1] - A[i]
        jpos R3,next         ; >= 0 : in order
        swap (R1),(R2)       ; one instruction swap
        mov  R3,R1
        sub  R3,R6
        jz   R3,loop         ; i = 0 : stay
        dec4 R1              ; i = i - 1
        jnz  R6,loop         ; R6 != 0: always
next:   inc4 R1
        mov  R3,R1
        sub  R3,R5
        jneg R3,loop         ; p < last
        jmp  R31             ; back to the OS
array:  dw   100 dup(?)""")

prog("q1398", M1398, """
        org  0
        mov  R1,x(R0)        ; R0=0 -> direct
        mov  R2,#3F800000h   ; term = 1.0
        mov  R3,R2           ; sum  = 1.0
        mov  R4,R2           ; i    = 1.0
        mov  R5,R2           ; 1.0
        mov  R6,#3A800000h   ;  2^-10
        mov  R7,#BA800000h   ; -2^-10
loop:   fmul R2,R1           ; term = term * x
        fdiv R2,R4           ;        / i
        fadd R3,R2           ; sum += term
        fadd R4,R5           ; i += 1
        fjh  R2,R6,loop      ; term >  2^-10
        fjl  R2,R7,loop      ; term < -2^-10
        mov  ex(R0),R3       ; store e^x
        je   R0,R0,OS
x:      dw   ?
ex:     dw   ?""")

# Q3 programs exactly as printed (used for the Q4 listings)
prog("e1402", M1402, """
        org  0
        mov  s+4, c+4
        and  s+4, c
here:   jz   here+14
        sub  s, #FFFFFFh
        add  c+4, s-4
        jnz  here-18
        jz   OS_Control_Point
        org  100h
c:      dw   ?, 1
s:      dw   0, ?""")

prog("e1401", M1401, """
        org  1
        xor  a, c-3
loop:   add  a, #-2
next:   xor  loop+1, 43Dh
        dec  c
        jnz  loop
        jmp  (1FFFFDh)
        org  100h
a:      dw   123456h
c:      dw   10
arr:    dw   100 dup(?)
k:      dw   13""")

prog("e1400", M1400, """
        org  100h
        mov  B-396, A+400
Arr:    dw   200Bh, 2005h, 1200h
        dw   B200h, 5520h, 150h
        dw   130, 29, 4
        add  Arr+10, #8
        add  Arr+14, #4
        jne  Arr+5, #B-8, Arr
        jmp  (FFFEh)
A:      dw   100 dup(0)
B:      dw   1""")

prog("e1399", M1399, """
        org  0
        mov  R1,#100
        mov  R0,#array
        dw   41006h
        mov  R1,#807004h
loop:   subq R1,4
        mov  R2,R0
        sub  R2,R1
        jneg R2,loop-6
        jmp  R31
array:  dw   100 dup(?)""")

prog("e1398", M1398, """
        org  0
float1: dw   -1.0e+109     ; -1.0 x 2^109
int1:   dw   3300000h
array:  dw   100 dup(?)
        dw   5000000h,1040000h
        dw   80100h,3200Ah,0
        mov  R11,R0
loop:   mov  R2,array-8(R1)
        dw   -40.5e+112    ; -40.5 x 2^112
        dw   38BFC22h,39Ah
        loop- R1,R4,loop
out1:   add  R10,R5
        loop- R1,R4,loop
out2:   add  R11,R5
        loop- R1,R4,loop
        je   R0,R0,OS_control_point""")


# ======================================================================
# tests
# ======================================================================
def with_os(src):
    return src + OS1402


def T(cond, msg):
    if not cond:
        raise AssertionError(msg)


def run_all(verbose=True):
    rnd = random.Random(1402)
    S = lambda v: v - (1 << 24) if v >> 23 else v
    ok = []

    def r(pid, data=None, arrays=None):
        return run1402(with_os(PROGRAMS[pid][1]), data, arrays)

    m, s = r("swap_xor"); T((s.rd(m.sym["a"]), s.rd(m.sym["b"])) == (0xABCDE, 0x1234), "swap_xor"); ok.append("swap_xor")
    m, s = r("swap_tmp"); T((s.rd(m.sym["a"]), s.rd(m.sym["b"])) == (9, 5), "swap_tmp"); ok.append("swap_tmp")
    m, s = r("swap_ptr"); T((s.rd(m.sym["x"]), s.rd(m.sym["y"])) == (3, 7), "swap_ptr"); ok.append("swap_ptr")
    m, s = r("zero_inc"); T(s.rd(m.sym["x"]) == 0 and s.rd(m.sym["flag"]) == 1, "zero_inc"); ok.append("zero_inc")
    m, s = r("count_loop"); T(s.rd(m.sym["sum"]) == 55, "count_loop"); ok.append("count_loop")
    A = [rnd.randint(-5000, 5000) for _ in range(100)]
    m, s = r("arr_sum", arrays={"A": A}); T(S(s.rd(m.sym["sum"])) == sum(A), "arr_sum"); ok.append("arr_sum")
    m, s = r("arr_max", arrays={"A": A}); T(S(s.rd(m.sym["mx"])) == max(A), "arr_max"); ok.append("arr_max")
    m, s = r("arr_count_neg", arrays={"A": A}); T(s.rd(m.sym["cnt"]) == sum(1 for v in A if v < 0), "count_neg"); ok.append("arr_count_neg")
    for n_ in (100,):
        m, s = r("reverse", arrays={"A": A}); T(words(s, m.sym["A"], 100) == A[::-1], "reverse"); ok.append("reverse")
    f = [0, 1]
    while len(f) < 100:
        f.append(f[-1] + f[-2])
    m, s = r("fib_sum"); T(s.rd(m.sym["sum"]) == sum(f) % (1 << 24), "fib_sum"); ok.append("fib_sum")
    m, s = r("fib_fill"); T(words(s, m.sym["A"], 100, False) == [v % (1 << 24) for v in f], "fib_fill"); ok.append("fib_fill")
    m, s = r("mul_add"); T(S(s.rd(m.sym["r"])) == -84, "mul_add"); ok.append("mul_add")
    m, s = r("mul_shift"); T(s.rd(m.sym["r"]) == 1234 * 567, "mul_shift"); ok.append("mul_shift")
    m, s = r("divmod"); T((s.rd(m.sym["q"]), s.rd(m.sym["x"])) == (14, 2), "divmod"); ok.append("divmod")
    m, s = r("popcount"); T(s.rd(m.sym["cnt"]) == bin(0xB5A3).count("1"), "popcount"); ok.append("popcount")
    m, s = r("pow2"); T(s.rd(m.sym["res"]) == 1, "pow2")
    m, s = r("pow2", data={"x": 4095}); T(s.rd(m.sym["res"]) == 0, "pow2b"); ok.append("pow2")
    m, s = r("abs"); T(s.rd(m.sym["x"]) == 37, "abs"); ok.append("abs")
    m, s = r("max2"); T(s.rd(m.sym["mx"]) == 9, "max2"); ok.append("max2")
    exp = []
    acc = 0
    for j, v in enumerate(A):
        acc += v if j % 2 == 0 else -v
        exp.append(acc)
    m, s = r("altsum", arrays={"A": A}); T(words(s, m.sym["A"], 100) == exp, "altsum"); ok.append("altsum")
    acc, exp2 = 0, []
    for v in A:
        acc += v
        exp2.append(acc)
    m, s = r("prefix", arrays={"A": A}); T(words(s, m.sym["A"], 100) == exp2, "prefix"); ok.append("prefix")
    for trial in range(3):
        B = [rnd.randint(-20, 20) for _ in range(100)]       # many duplicates
        m, s = r("gnome", arrays={"A": B}); T(words(s, m.sym["A"], 100) == sorted(B), "gnome")
        m, s = r("bubble", arrays={"A": B}); T(words(s, m.sym["A"], 100) == sorted(B), "bubble")
    ok += ["gnome", "bubble"]
    m, s = r("selfmod_walk", arrays={"A": A}); T(S(s.rd(m.sym["sum"])) == sum(A), "selfmod_walk"); ok.append("selfmod_walk")
    m, s = r("toggle"); T(s.rd(m.sym["x"]) == 5, "toggle"); ok.append("toggle")

    # ---- exam Q2 solutions
    m = M1402()
    mem = load(m, PROGRAMS["q1402"][1] + "\n        org 7000h\nOS_Control_Point: dw 0")
    mem = setarr(m, mem, m.sym["A"], A)
    s, _ = m.run(mem, os_addr=m.sym["OS_Control_Point"])
    T(words(s, m.sym["A"], 100) == exp, "q1402"); ok.append("q1402")

    for pid in ("q1401_template", "q1401_safe"):
        m = M1401()
        img, _ = m.assemble(PROGRAMS[pid][1])
        vals = rnd.sample(range(-8, 3000), 100) if pid == "q1401_template" else [rnd.randint(-50, 50) for _ in range(100)]
        mem = setarr(m, img, m.sym["A"], vals)
        s, steps = m.run(mem, pc=0x100)
        T(words(s, m.sym["A"], 100) == sorted(vals), pid)
        ok.append(pid)
    # template version with duplicates loops forever
    m = M1401()
    img, _ = m.assemble(PROGRAMS["q1401_template"][1])
    try:
        m.run(img, pc=0x100, maxsteps=200000)
        T(False, "template should not halt on equal values")
    except Exception as e:
        T("no halt" in str(e), "template dup")
    # word just before A (tail of the jmp instruction) seen as a number
    s0 = Sim(m, img)
    TEMPLATE_GUARD[0] = s0.signed(s0.rd(m.sym["A"] - 3))

    m = M1400()
    img, _ = m.assemble(PROGRAMS["q1400"][1])
    s, _ = m.run(img, pc=0)
    T(s.rd(m.sym["sum"]) == sum(f) % (1 << 16), "q1400"); ok.append("q1400")

    m = M1399()
    img, _ = m.assemble(PROGRAMS["q1399"][1])
    for trial in range(3):
        B = [rnd.randint(-30, 30) for _ in range(100)]
        mem = setarr(m, img, m.sym["array"], B)
        s, R, _ = m.run(mem)
        T(words(s, m.sym["array"], 100) == sorted(B), "q1399")
    ok.append("q1399")

    m = M1398()
    worst = 0
    for xv in (-6.0, -2.5, -1.0, 0.0, 0.3, 1.0, 2.0, 4.5, 7.0):
        src = PROGRAMS["q1398"][1] + "\n        org 9000h\nOS:     dw 0"
        img, _ = m.assemble(src)
        mem = Sim(m, img)
        mem.wr(m.sym["x"], fbits(xv))
        s, R, _ = m.run(mem.mem, os_addr=m.sym["OS"])
        got = bitsf(s.rd(m.sym["ex"]))
        worst = max(worst, abs(got - math.exp(xv)))
        T(abs(got - math.exp(xv)) < 2 ** -10, "q1398 x=%s got %s" % (xv, got))
    ok.append("q1398")
    if verbose:
        print("verified:", ", ".join(ok))
        print("template guard word = %d, e^x worst abs err = %.2e" % (TEMPLATE_GUARD[0], worst))
    return ok


TOGGLE_X = [None]
TEMPLATE_GUARD = [None]

if __name__ == "__main__":
    run_all()
