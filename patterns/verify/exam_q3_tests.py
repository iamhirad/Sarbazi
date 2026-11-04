"""Run the midterm Q3 programs (as printed) and check the claimed behaviour."""
import random

from asm import Sim
from machines import M1398, M1399, M1400, M1401, M1402, Halt, fbits
from programs import PROGRAMS


def run_exam_q3(verbose=True):
    rnd = random.Random(1399)
    R = {}

    # 1402: s = popcount(c)
    m = M1402()
    img, _ = m.assemble(PROGRAMS["e1402"][1], presym={"OS_Control_Point": 0x7000})
    for c in [0, 1, 0xB, 0xFFFFFF, 0x800001] + [rnd.getrandbits(24) for _ in range(5)]:
        s0 = Sim(m, img)
        s0.wr(m.sym["c"], c)
        s, _ = m.run(s0.mem, os_addr=0x7000)
        assert s.rd(m.sym["s"]) == bin(c).count("1"), c
    R["e1402"] = "s = تعداد بیت‌های ۱ عدد c (مثلاً c = 5BE6A3h ⇒ s = 14)"

    # 1401: printed (direct 43Dh, M[43Dh] = 0) -> a = -20 ; with '#43Dh' -> a = -10
    m = M1401()
    img, _ = m.assemble(PROGRAMS["e1401"][1])
    s, _ = m.run(img, pc=1)
    assert s.signed(s.rd(m.sym["a"])) == -20
    img2, _ = m.assemble(PROGRAMS["e1401"][1].replace("43Dh", "#43Dh"))
    s2, _ = m.run(img2, pc=1)
    assert s2.signed(s2.rd(m.sym["a"])) == -10 and s2.rd(m.sym["c"]) == 0
    R["e1401"] = "با #43Dh: a = −10 و c = 0 (دستور add یک دور در میان jmp next می‌شود)؛ اگر مستقیم و M[43Dh] = 0: a = −20"

    # 1400: org 0 -> Fibonacci in A; printed org 100h never halts
    f = [0, 1]
    while len(f) < 100:
        f.append((f[-1] + f[-2]) & 0xFFFF)
    m = M1400()
    img, _ = m.assemble(PROGRAMS["e1400"][1].replace("org  100h", "org  0"))
    s, _ = m.run(img, pc=0)
    assert [s.rd(m.sym["A"] + 4 * i) for i in range(100)] == f
    img, _ = m.assemble(PROGRAMS["e1400"][1])
    try:
        m.run(img, pc=0x100, maxsteps=20000)
        raise AssertionError("printed 1400 program should not halt")
    except Halt:
        pass
    R["e1400"] = "A[0..99] = ۱۰۰ جملهٔ اول فیبوناچی (اعداد Arr برای org 0 ساخته شده‌اند؛ با org 100h چاپ‌شده حلقه بی‌پایان است)"

    # 1399: reverses A[0..25]
    m = M1399()
    img, _ = m.assemble(PROGRAMS["e1399"][1])
    vals = [rnd.randint(0, 9999) for _ in range(100)]
    s0 = Sim(m, img)
    for i, v in enumerate(vals):
        s0.wr(m.sym["array"] + 4 * i, v)
    s, regs, _ = m.run(s0.mem)
    out = [s.rd(m.sym["array"] + 4 * i) for i in range(100)]
    assert out == vals[:26][::-1] + vals[26:]
    R["e1399"] = "ترتیب ۲۶ کلمهٔ اول آرایه (A[0..25]) وارونه می‌شود"

    # 1398: R10 = #NaN, R11 = #denormal in A[1..99] (A[1] is normal here)
    m = M1398()
    img, _ = m.assemble(PROGRAMS["e1398"][1], presym={"OS_control_point": 0x1000})
    NAN, DEN = 0x7FC00001, 0x00000005
    arr = [fbits(rnd.uniform(-5, 5)) for _ in range(100)]
    for i in rnd.sample(range(2, 100), 12):
        arr[i] = NAN
    for i in rnd.sample([k for k in range(2, 100) if arr[k] != NAN], 7):
        arr[i] = DEN
    s0 = Sim(m, img)
    for i, v in enumerate(arr):
        s0.wr(m.sym["array"] + 8 * i, v)
    s, regs, _ = m.run(s0.mem, regs={k: 7 for k in range(1, 16)}, os_addr=0x1000)
    assert regs[10] == 12 + 1 and regs[11] == 7 + 1, (regs[10], regs[11])
    R["e1398"] = "R10 = تعداد NaNها و R11 = تعداد غیرنرمال‌ها در A[1..99] (به‌علاوهٔ ۱ هنگام خروج اگر A[1] عادی باشد)"

    if verbose:
        print("exam Q3 verified:", ", ".join(R))
    return R


if __name__ == "__main__":
    run_exam_q3()
