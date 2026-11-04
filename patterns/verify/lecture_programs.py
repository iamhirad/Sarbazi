"""Every program of the lecture notes (jozveh), transcribed for the lecture machines, with tests.

LECTURE maps id -> (machine class, source, externals).  run_lecture() runs and checks all of them.
"""
import random

from asm import Sim
from lecture import L1, L1A, L2, L3, L4, L5, L6, L7, sgn

LECTURE = {}


def prog(pid, machine, src, externals=()):
    LECTURE[pid] = (machine, src.strip("\n"), tuple(externals))


# ------------------------------------------------------------------ Machine 1
prog("m1_examples", L1, """
        sub  15,10      ; M15 <- (M15) - (M10)
        add  3,100      ; M3 <- (M3) + (M100)
        mov  67,53      ; M67 <- (M53)""")

# ------------------------------------------------------------------ Machine 2
prog("m2_fib7", L2, """
        org  100h
        add  t1,t2      ; جملهٔ ۳ در t1
        add  sum,t1
        add  t2,t1      ; جملهٔ ۴ در t2
        add  sum,t2
        add  t1,t2      ; جملهٔ ۵
        add  sum,t1
        add  t2,t1      ; جملهٔ ۶
        add  sum,t2
        add  t1,t2      ; جملهٔ ۷
        add  sum,t1
        org  200h
sum:    dw   1          ; F0 + F1
t1:     dw   0
t2:     dw   1
        end""")

prog("m2_xorswap", L2, """
        org  100h
        xor  x,y        ; x = x^y
        xor  y,x        ; y = x
        xor  x,y        ; x = y
        org  200h
x:      dw   1234h
y:      dw   0ABCDh
        end""")

prog("m2_expr", L2, """
        org  100h
        mov  r,a        ; r = a
        add  r,b        ; r = a+b
        add  r,r        ; r = 2(a+b)
        sub  r,c        ; r = 2(a+b)-c
        org  200h
a:      dw   ?
b:      dw   ?
c:      dw   ?
r:      dw   ?
        end""")

# ------------------------------------------------------------------ Machine 3
prog("m3_altfib", L3, """
        org  0
loop:   add  sum,curr   ; + جملهٔ زوج
        sub  sum,next   ; - جملهٔ فرد
        add  curr,next  ; جملهٔ بعد
        add  next,curr  ; جملهٔ بعد از آن
        sub  count,one
        jnz  count,loop ; ۵۰ دور
curr:   dw   0
next:   dw   1
sum:    dw   0
count:  dw   50
one:    dw   1
        end""")

prog("m3_arrsum", L3, """
        org  100h
loop:   add  sum,(arrptr)  ; غیرمستقیم
        add  arrptr,two    ; عنصر بعد
        sub  count,two
        jnz  count,loop    ; ۱۰۰ دور
arrptr: dw   array
sum:    dw   0
count:  dw   200
two:    dw   2
array:  dw   100 dup(?)
        end""")

prog("m3_selfmod", L3, """
        org  100h
loop:   add  sum,array     ; addr2 هر دور عوض می‌شود
        add  loop+3,two    ; addr2 = بایت‌های loop+3..4
        sub  count,two
        jnz  count,loop
sum:    dw   0
count:  dw   200
two:    dw   2
array:  dw   100 dup(?)
        end""")

# ------------------------------------------------------------------ Machine 4
prog("m4_vecadd", L4, """
        org  0
        mov  R0,#A      ; R0 -> A
        mov  R1,#B      ; R1 -> B
        mov  R2,#C      ; R2 -> C
        mov  R5,#10     ; شمارنده
loop:   mov  R10,(R0)   ; A[i]
        mov  R11,(R1)   ; B[i]
        add  R10,R11
        mov  (R2),R10   ; C[i] = A[i]+B[i]
        add  R0,#4      ; کلمه = ۴ واحد
        add  R1,#4
        add  R2,#4
        sub  R5,#1
        jnz  R5,loop
A:      dw   10 dup(?)
B:      dw   10 dup(?)
C:      dw   10 dup(?)
        end""")

# ------------------------------------------------------------------ Machine 5
prog("m5_arrsum", L5, """
        org  100h
        xor  R0,R0      ; انباره = 0
        mov  R1,R0      ; شاخص = 0
        mov  R2,#200    ; شاخص پایان
loop:   mov  R3,A(R1)   ; شاخص‌دار
        add  R0,R3
        add  R1,#2
        jne  R1,R2,loop
        mov  sum,R0,R0  ; ذخیره
        call R0,0(R63)  ; بازگشت به OS
sum:    dw   0
A:      dw   100 dup(?)
        end""")

_straight = "        org  100h\n" + "\n".join(
    f"        add  R62,R{k}" + ("      ; R62 += R0" if k == 0 else "") for k in range(62)
) + "\n        call R0,0(R63)  ; بازگشت به OS\n        end"
prog("m5_sumregs_straight", L5, _straight)

prog("m5_sumregs_loop", L5, """
        org  100h
        add  R62,R61       ; R61 آزاد شد
        mov  ret,R63,R63   ; ذخیرهٔ R63
        mov  R63,#1FBDh    ; کد add R62,R61
loop:   add  R62,R0        ; هر دور عوض می‌شود
        mov  R61,R61,loop  ; R61 = کلمهٔ دستور
        add  R61,#1        ; ثبات بعدی
        mov  loop,R61,R61  ; بازنویسی دستور
        jne  R61,R63,loop
        mov  R63,R63,ret   ; بازیابی R63
        call R0,0(R63)
ret:    dw   0
        end""")

# ------------------------------------------------------------------ one-address machine
prog("a1_fib20", L1A, """
        org  0
loop:   load  (pointer_1)  ; A[i]
        store sum
        load  (pointer_2)  ; A[i+1]
        add   sum
        store (pointer_3)  ; A[i+2]
        load  pointer_1
        add   #4
        store pointer_1
        add   #4
        store pointer_2
        add   #4
        store pointer_3
        load  counter
        add   #-1
        store counter
        jnz   loop
        j     OS_return_addr
pointer_1: dw  array
pointer_2: dw  array+4
pointer_3: dw  array+8
counter:   dw  18
sum:       dw  ?
array:     dw  0,1,18 dup(?)
        end""", externals=("OS_return_addr",))

# ------------------------------------------------------------------ Machine 6 (stack)
prog("m6_pushpop", L6, """
        org  0
        push #-10       ; [-10]
        push Num        ; [-10,100]
        push #77        ; [-10,100,77]
        pop  Num        ; Num = 77
        add             ; [90]
Num:    dw   100
        end""")

prog("m6_expr", L6, """
        org  0
        push a
        push b
        add             ; [a+b]
        push c
        push d
        sub             ; [a+b, c-d]
        sub             ; [(a+b)-(c-d)]
        pop  r
a:      dw   2
b:      dw   3
c:      dw   7
d:      dw   1
r:      dw   ?
        end""")

prog("m6_fib_slide", L6, """
        org  0
loop:   push x
        push y
        add
        pop  x          ; x = x+y
        sp++
        push sum
        add
        pop  sum        ; sum += x
        push x
        push y
        add
        pop  y          ; y = x+y
        sp++
        push sum
        add
        pop  sum        ; sum += y
        push counter
        push #1
        sub
        pop  counter
        sp++
        push #loop
        jnz             ; counter != 0
        push #OS_return_addr
        j
sum:    dw   1
counter: dw  10
x:      dw   0
y:      dw   1
        end""", externals=("OS_return_addr",))

prog("m6_fib_better", L6, """
        org  0
loop:   push x
        push y
        add
        pop  x          ; x = x+y
        sp++
        push y
        add
        pop  y          ; y = x+y
        push counter
        push #1
        sub
        pop  counter
        sp++
        push #loop
        jnz
        push y          ; y = F21
        push #1
        sub
        pop  sum        ; sum = F21 - 1
        push #OS_return_addr
        j
sum:    dw   0
counter: dw  10
x:      dw   0
y:      dw   1
        end""", externals=("OS_return_addr",))

# ------------------------------------------------------------------ Machine 7
prog("m7_gnome", L7, """
        org  100h
loop:   load  (p)          ; ACC = A[i]
        store temp1
        load  p
        addi  4
        store p            ; p -> A[i+1]
        load  (p)
        store temp2
        sub   temp1        ; A[i+1]-A[i]
        jpos  continue     ; مرتب: i++
        load  temp1        ; جابه‌جایی
        store (p)
        load  p
        subi  4
        store p
        load  temp2
        store (p)
        load  p
        subi  4
        store p            ; i--
        jmp   loop
continue: load p
        subi  array+396
        jnz   loop
        jmpl  OS_return_point
p:      dw    array
temp1:  dw    ?
temp2:  dw    ?
        dw    80000000h    ; نگهبان
array:  dw    100 dup(?)
        end""", externals=("OS_return_point",))

prog("m7_gnome_safe", L7, """
        org  100h
loop:   load  (p)
        store temp1
        load  p
        addi  4
        store p
        load  (p)
        store temp2
        sub   temp1        ; A[i+1]-A[i]
        jpos  continue     ; >= 0 : مرتب
        load  temp1
        store (p)
        load  p
        subi  4
        store p
        load  temp2
        store (p)
        load  p
        subi  array        ; i = 0 ?
        jz    loop
        load  p
        subi  4
        store p            ; i--
        jmp   loop
continue: load p
        subi  array+396
        jnz   loop
        jmpl  OS_return_point
p:      dw    array
temp1:  dw    ?
temp2:  dw    ?
array:  dw    100 dup(?)
        end""", externals=("OS_return_point",))

prog("m7_primes", L7, """
        org  100h
next:   load  (ip)         ; flags[i]
        jnz   notprime
        load  sum
        add   i
        store sum          ; sum += i
        load  count
        subi  1
        store count
        jz    done
        load  i
        add   i
        store step
        add   step
        store step         ; step = 4i
        load  ip
        add   step
mark:   store jp
        subi  flags+2168   ; انتهای آرایه
        jpos  notprime
        load  one
        store (jp)         ; علامت مضرب
        load  jp
        add   step
        jmp   mark
notprime: load ip
        addi  4
        store ip
        load  i
        addi  1
        store i
        jmpl  next         ; خارج از بازهٔ نسبی
done:   jmpl  OS_return_point
ip:     dw    flags+8
i:      dw    2
step:   dw    ?
jp:     dw    ?
sum:    dw    0
count:  dw    100
one:    dw    1
flags:  dw    542 dup(0)
        end""", externals=("OS_return_point",))


# ------------------------------------------------------------------ tests
def asm(pid, presym=None):
    cls, src, ext = LECTURE[pid]
    m = cls()
    img, lst = m.assemble(src, presym=presym)
    return m, img, lst


def setw(m, img, base, vals):
    s = Sim(m, img)
    for i, v in enumerate(vals):
        s.wr(base + m.word_units * i, v)
    return s.mem


def getw(s, base, n, bits):
    return [sgn(s.rd(base + s.m.word_units * i), bits) for i in range(n)]


def code_end(lst):
    return max(a + len(b) // 1 for a, l, mn, o, r, b in lst if mn != "dw")  # placeholder (not used)


RESULTS = {}


def run_lecture(verbose=True):
    rnd = random.Random(98)
    T = {}

    def ok(pid, cond, res):
        assert cond, pid
        T[pid] = res

    m, img, lst = asm("m1_examples")
    codes = ["%04X" % int(b, 2) for a, l, mn, o, r, b in lst]
    ok("m1_examples", codes == ["478A", "01E4", "A1B5"], "کدها: 478Ah، 01E4h، A1B5h")

    m, img, lst = asm("m2_fib7")
    s, _ = m.run(img, 0x100, 0x132)
    ok("m2_fib7", s.rd(0x200) == 20, "sum = 20 (0+1+1+2+3+5+8)")

    m, img, lst = asm("m2_xorswap")
    s, _ = m.run(img, 0x100, 0x10F)
    ok("m2_xorswap", (s.rd(0x200), s.rd(0x202)) == (0xABCD, 0x1234), "x = ABCDh، y = 1234h")

    m, img, lst = asm("m2_expr")
    mem = setw(m, img, 0x200, [9, 4, 5])
    s, _ = m.run(mem, 0x100, 0x114)
    ok("m2_expr", sgn(s.rd(0x206), 16) == 2 * (9 + 4) - 5, "a=9, b=4, c=5 ⇒ r = 21")

    m, img, lst = asm("m3_altfib")
    s, _ = m.run(img, 0, 0x1E)
    f = [0, 1]
    while len(f) < 100:
        f.append(f[-1] + f[-2])
    true = sum((-1) ** i * f[i] for i in range(100))
    ok("m3_altfib", sgn(s.rd(m.sym["sum"]), 16) == sgn(true, 16), "sum = −18114 (حاصل واقعی به پیمانهٔ 2^16)")

    A = [rnd.randint(0, 300) for _ in range(100)]
    for pid in ("m3_arrsum", "m3_selfmod"):
        m, img, lst = asm(pid)
        mem = setw(m, img, m.sym["array"], A)
        s, _ = m.run(mem, 0x100, 0x114)
        ok(pid, s.rd(m.sym["sum"]) == sum(A) & 0xFFFF, "مجموع ۱۰۰ عدد تصادفی درست است")

    m, img, lst = asm("m4_vecadd")
    X = [rnd.randint(0, 999) for _ in range(10)]
    Y = [rnd.randint(0, 999) for _ in range(10)]
    mem = setw(m, img, m.sym["A"], X)
    mem = setw(m, mem, m.sym["B"], Y)
    s, R = m.run(mem, 0, m.sym["A"])
    ok("m4_vecadd", getw(s, m.sym["C"], 10, 16) == [a + b for a, b in zip(X, Y)], "C[i] = A[i] + B[i] برای ۱۰ عنصر")

    m, img, lst = asm("m5_arrsum")
    mem = setw(m, img, m.sym["A"], A)
    s, R = m.run(mem, 0x100, 0xABCD, regs={63: 0xABCD})
    ok("m5_arrsum", s.rd(m.sym["sum"]) == sum(A) & 0xFFFF, "مجموع ۱۰۰ عدد درست است")

    regs = {k: rnd.randint(0, 500) for k in range(63)}
    regs[63] = 0xABCD
    for pid in ("m5_sumregs_straight", "m5_sumregs_loop"):
        m, img, lst = asm(pid)
        s, R = m.run(img, 0x100, 0xABCD, regs=regs)
        ok(pid, R[62] == sum(regs[k] for k in range(63)) & 0xFFFF, "R62 = R0 + … + R62")

    m, img, lst = asm("a1_fib20", presym={"OS_return_addr": 0xFFF0})
    s, acc = m.run(img, 0, 0xFFF0)
    ok("a1_fib20", getw(s, m.sym["array"], 20, 16) == f[:20], "آرایه = ۲۰ جملهٔ اول فیبوناچی (… 4181)")

    m, img, lst = asm("m6_pushpop")
    s, st, sp = m.run(img, 0, m.sym["Num"])
    ok("m6_pushpop", s.rd(m.sym["Num"]) == 77 and sp == 1 and st[0] == 90, "Num = 77، پشته [90]، SP = 1")

    m, img, lst = asm("m6_expr")
    s, st, sp = m.run(img, 0, m.sym["a"])
    ok("m6_expr", sgn(s.rd(m.sym["r"]), 32) == (2 + 3) - (7 - 1) and sp == 0, "r = (2+3) − (7−1) = −1")

    m, img, lst = asm("m6_fib_slide", presym={"OS_return_addr": 0xFFFF})
    s, st, sp = m.run(img, 0, 0xFFFF)
    ok("m6_fib_slide", s.rd(m.sym["sum"]) == sum(f[:22]) and sp == 0, "sum = 28656 (۲۲ جمله؛ برای ۲۰ جمله counter = 9)")

    m, img, lst = asm("m6_fib_better", presym={"OS_return_addr": 0xFFFF})
    s, st, sp = m.run(img, 0, 0xFFFF)
    ok("m6_fib_better", s.rd(m.sym["sum"]) == sum(f[:20]) and sp == 0, "sum = 10945 = F21 − 1 (دقیقاً ۲۰ جمله)")

    for pid, gen in (("m7_gnome", lambda: [rnd.randint(-1000, -1) for _ in range(100)]),
                     ("m7_gnome_safe", lambda: [rnd.randint(-30, 30) for _ in range(100)])):
        for _ in range(3):
            V = gen()
            m, img, lst = asm(pid, presym={"OS_return_point": 0xFFFFFFF0})
            mem = setw(m, img, m.sym["array"], V)
            s, n = m.run(mem, 0x100, 0xFFFFFFF0)
            assert getw(s, m.sym["array"], 100, 32) == sorted(V), pid
    T["m7_gnome"] = "آرایه صعودی شد (آزمون با عددهای منفی؛ با عددهای مثبت نگهبان سرریز می‌کند)"
    T["m7_gnome_safe"] = "آرایهٔ ۱۰۰ عضوی با عددهای مثبت، منفی و تکراری صعودی شد"

    m, img, lst = asm("m7_primes", presym={"OS_return_point": 0xFFFFFFF0})
    s, n = m.run(img, 0x100, 0xFFFFFFF0)
    ok("m7_primes", s.rd(m.sym["sum"]) == 24133, "sum = 24133 (۱۰۰ عدد اول تا 541)")

    RESULTS.update(T)
    if verbose:
        print("lecture verified:", ", ".join(T))
    return T


if __name__ == "__main__":
    run_lecture()
