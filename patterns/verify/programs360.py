"""Solved IBM 360 programs used in the notes (chapters 6-8), the catalog and the patterns sheet, with tests."""
import random

from ibm360 import CPU, assemble, s32

P360 = {}


def prog(pid, title, src):
    P360[pid] = (title, src.strip("\n"))


prog("stock", "برنامهٔ نمونهٔ اسلاید (موجودی انبار)", """
STOCK    START 256
BEGIN    BALR  11,0           R11 = نشانی دستور بعد
         USING *,11           به اسمبلر: R11 = همین نقطه
         L     3,OLDOH        R3 = موجودی قبلی
         A     3,RECPT        + دریافتی
         S     3,ISSUE        − صادره
         ST    3,NEWOH        موجودی جدید
         EOJ                  پایان کار و بازگشت به OS
OLDOH    DC    F'9'
RECPT    DC    F'4'
ISSUE    DC    F'6'
NEWOH    DS    F
         END   BEGIN""")

prog("vardef", "تعریف متغیرها با DS و DC (مثال اسلاید)", """
VARS     START X'FE'
VAR1     DS    3F             ۳ کلمه، هم‌تراز
VAR2     DC    F'1'
VAR3     DC    F'1',F'-2',2F'100'
         END""")

prog("vardef2", "هم‌ترازی خودکار با انواع H، F، D، C و X", """
V2       START X'1001'
A        DC    C'AB'          ۲ بایت، بدون هم‌ترازی
B        DC    H'5'           نیم‌کلمه: نشانی زوج
C        DS    F              کلمه: مضرب ۴
D        DC    2F'7'          دو کلمه
E        DC    X'FF'          ۱ بایت
F        DC    H'-1'          نیم‌کلمه
G        DS    D              کلمهٔ مضاعف: مضرب ۸
         END""")

prog("sumarr", "جمع عناصر یک آرایهٔ ۱۰ کلمه‌ای", """
SUMARR   START 0
BEGIN    BALR  12,0
         USING *,12
         SR    3,3            sum = 0
         SR    4,4            اندیس = 0
         LA    5,10           شمارنده = 10
LOOP     A     3,ARR(4)       sum += ARR[i]
         LA    4,4(4)         اندیس += 4
         BCT   5,LOOP         ۱۰ بار
         ST    3,SUM
         EOJ
ARR      DC    F'5',F'-2',F'7',F'10',F'0'
         DC    F'3',F'-8',F'1',F'4',F'6'
SUM      DS    F
         END   BEGIN""")

prog("maxarr", "بیشینهٔ آرایه با C و BNL", """
MAXARR   START 0
BEGIN    BALR  12,0
         USING *,12
         L     3,ARR          max = ARR[0]
         LA    4,4            اندیس ARR[1]
         LA    5,9            ۹ عنصر باقی
LOOP     C     3,ARR(4)       مقایسهٔ max با ARR[i]
         BNL   NEXT           max ≥ ARR[i]: بماند
         L     3,ARR(4)       بیشینهٔ جدید
NEXT     LA    4,4(4)
         BCT   5,LOOP
         ST    3,MAX
         EOJ
ARR      DC    F'5',F'-2',F'7',F'10',F'0'
         DC    F'3',F'-8',F'1',F'4',F'6'
MAX      DS    F
         END   BEGIN""")

prog("cntneg", "شمارش عناصر منفی (افزایش با LA)", """
CNTNEG   START 0
BEGIN    BALR  12,0
         USING *,12
         SR    3,3            count = 0
         SR    7,7            R7 = 0 برای مقایسه
         SR    4,4            اندیس = 0
         LA    5,10
LOOP     C     7,ARR(4)       مقایسهٔ 0 با ARR[i]
         BNH   NEXT           0 ≤ ARR[i]: منفی نیست
         LA    3,1(3)         count += 1
NEXT     LA    4,4(4)
         BCT   5,LOOP
         ST    3,COUNT
         EOJ
ARR      DC    F'5',F'-2',F'7',F'10',F'0'
         DC    F'3',F'-8',F'1',F'4',F'6'
COUNT    DS    F
         END   BEGIN""")

prog("avg", "میانگین و باقی‌مانده (M برای گسترش علامت، سپس D)", """
AVG      START 0
BEGIN    BALR  12,0
         USING *,12
         SR    3,3
         SR    4,4
         L     5,N            شمارنده = N
LOOP     A     3,ARR(4)       R3 = مجموع
         LA    4,4(4)
         BCT   5,LOOP
         M     2,ONE          R2:R3 = sum × 1 (گسترش علامت)
         D     2,N            R3 = خارج‌قسمت، R2 = باقی‌مانده
         ST    3,MEAN
         ST    2,REM
         EOJ
ONE      DC    F'1'
N        DC    F'10'
ARR      DC    F'5',F'-2',F'7',F'10',F'0'
         DC    F'3',F'-8',F'1',F'4',F'6'
MEAN     DS    F
REM      DS    F
         END   BEGIN""")

prog("fib", "۲۰ جملهٔ اول فیبوناچی در آرایه", """
FIB      START 0
BEGIN    BALR  12,0
         USING *,12
         SR    3,3            a = F0 = 0
         LA    4,1            b = F1 = 1
         SR    6,6            اندیس = 0
         LA    7,20           ۲۰ جمله
LOOP     ST    3,F(6)         F[i] = a
         LR    5,3
         AR    5,4            t = a + b
         LR    3,4            a = b
         LR    4,5            b = t
         LA    6,4(6)         اندیس += 4
         BCT   7,LOOP
         EOJ
F        DS    20F
         END   BEGIN""")

prog("sumn", "جمع ۱ تا N با BCT روی خود N", """
SUMN     START 0
BEGIN    BALR  12,0
         USING *,12
         SR    3,3            sum = 0
         L     5,N            R5 = N
LOOP     AR    3,5            sum += R5
         BCT   5,LOOP         R5 = N, N−1, …, 1
         ST    3,SUM
         EOJ
N        DC    F'100'
SUM      DS    F
         END   BEGIN""")

prog("evens", "شمارش اعداد زوج با N (AND) و ماسک ۱", """
EVENS    START 0
BEGIN    BALR  12,0
         USING *,12
         SR    3,3            count = 0
         SR    4,4
         LA    5,10
LOOP     L     6,ARR(4)
         N     6,ONE          فقط بیت ۰ بماند
         BNZ   NEXT           بیت ۰ = 1: فرد
         LA    3,1(3)         زوج: count += 1
NEXT     LA    4,4(4)
         BCT   5,LOOP
         ST    3,COUNT
         EOJ
ONE      DC    F'1'
ARR      DC    F'5',F'-2',F'7',F'10',F'0'
         DC    F'3',F'-8',F'1',F'4',F'6'
COUNT    DS    F
         END   BEGIN""")

prog("swap", "جابه‌جایی دو ثبات با XR و دو کلمهٔ حافظه", """
SWAP     START 0
BEGIN    BALR  12,0
         USING *,12
         L     3,X
         L     4,Y
         XR    3,4            R3 = x ⊕ y
         XR    4,3            R4 = x
         XR    3,4            R3 = y
         ST    3,X            حافظه جابه‌جا شد
         ST    4,Y
         EOJ
X        DC    F'1234'
Y        DC    F'-77'
         END   BEGIN""")

prog("gnome", "مرتب‌سازی Gnome روی ۱۰ کلمه", """
SORT     START 0
BEGIN    BALR  12,0
         USING *,12
         SR    4,4            i = 0 (فاصله بر حسب بایت)
         SR    8,8            R8 = 0
         LA    9,36           فاصلهٔ آخرین عنصر
         LA    10,4           R10 = 4
LOOP     L     5,A(4)         A[i]
         L     6,A+4(4)       A[i+1]
         CR    5,6
         BNH   NEXT           A[i] ≤ A[i+1]: مرتب است
         ST    6,A(4)         جابه‌جایی
         ST    5,A+4(4)
         CR    4,8            آیا i = 0 ؟
         BE    LOOP           بله: بماند
         SR    4,10           i = i − 1
         B     LOOP
NEXT     LA    4,4(4)         i = i + 1
         CR    4,9
         BL    LOOP           تا i = آخر
         EOJ
A        DC    F'5',F'-2',F'7',F'10',F'0'
         DC    F'3',F'-8',F'1',F'4',F'6'
         END   BEGIN""")

prog("add64", "جمع دو عدد ۶۴ بیتی با AL و نقلی", """
ADD64    START 0
BEGIN    BALR  12,0
         USING *,12
         L     2,AHI          نیمهٔ بالای A
         L     3,ALO          نیمهٔ پایین A
         AL    3,BLO          جمع پایین‌ها (بدون علامت)
         BNO   NOCARRY        CC ≠ 11: نقلی نداشت
         A     2,ONE          نقلی: +1 به بالا
NOCARRY  A     2,BHI          جمع بالاها
         ST    2,SHI
         ST    3,SLO
         EOJ
ONE      DC    F'1'
AHI      DC    X'00000001'
ALO      DC    X'FFFFFFFF'
BHI      DC    X'00000002'
BLO      DC    X'00000005'
SHI      DS    F
SLO      DS    F
         END   BEGIN""")

prog("divneg", "تقسیم یک عدد منفی: آماده‌کردن جفت ثبات", """
DIVNEG   START 0
BEGIN    BALR  12,0
         USING *,12
         L     3,X            R3 = x (منفی)
         LA    4,1            R4 = 1
         MR    2,4            R2:R3 = x × 1 (گسترش علامت)
         D     2,Y            R3 = x / y ، R2 = باقی‌مانده
         ST    3,Q
         ST    2,R
         EOJ
X        DC    F'-47'
Y        DC    F'5'
Q        DS    F
R        DS    F
         END   BEGIN""")

prog("pow2", "محاسبهٔ ۲ به توان n با دوبرابر کردن (AR r,r)", """
POW2     START 0
BEGIN    BALR  12,0
         USING *,12
         LA    3,1            p = 1
         L     5,EXP          شمارنده = n
LOOP     AR    3,3            p = 2p
         BCT   5,LOOP
         ST    3,P
         EOJ
EXP      DC    F'10'
P        DS    F
         END   BEGIN""")

prog("ifmax", "ترجمهٔ if-else: بزرگ‌تر دو عدد", """
IFMAX    START 0
BEGIN    BALR  12,0
         USING *,12
         L     3,A            R3 = a
         C     3,B            مقایسهٔ a با b
         BNH   ELSE           شرط برعکس: a ≤ b ⇒ برو به else
         ST    3,MAX          then: max = a
         B     ENDIF          از روی else بپر
ELSE     L     3,B            else: max = b
         ST    3,MAX
ENDIF    EOJ
A        DC    F'-8'
B        DC    F'13'
MAX      DS    F
         END   BEGIN""")

prog("search", "جست‌وجوی خطی: اندیس اولین KEY یا −1", """
SEARCH   START 0
BEGIN    BALR  12,0
         USING *,12
         L     3,KEY          R3 = کلید
         SR    4,4            فاصله = 0 بایت
         SR    6,6            i = 0
         LA    5,10           ۱۰ عنصر
LOOP     C     3,ARR(4)       KEY = ARR[i] ؟
         BE    FOUND
         LA    4,4(4)         عنصر بعد
         LA    6,1(6)         i += 1
         BCT   5,LOOP
         L     6,MINUS1       پیدا نشد: −1
FOUND    ST    6,POS
         EOJ
MINUS1   DC    F'-1'
KEY      DC    F'1'
ARR      DC    F'5',F'-2',F'7',F'10',F'0'
         DC    F'3',F'-8',F'1',F'4',F'6'
POS      DS    F
         END   BEGIN""")

prog("reverse", "وارونه کردن آرایه در جا با دو اندیس", """
REVERSE  START 0
BEGIN    BALR  12,0
         USING *,12
         SR    4,4            i = 0 (ابتدا)
         LA    5,36           j = 9 × 4 (انتها)
LOOP     CR    4,5            تا وقتی i < j
         BNL   DONE
         L     6,ARR(4)       t1 = ARR[i]
         L     7,ARR(5)       t2 = ARR[j]
         ST    7,ARR(4)       ARR[i] = t2
         ST    6,ARR(5)       ARR[j] = t1
         LA    4,4(4)         i += 1
         S     5,FOUR         j −= 1
         B     LOOP
DONE     EOJ
FOUR     DC    F'4'
ARR      DC    F'5',F'-2',F'7',F'10',F'0'
         DC    F'3',F'-8',F'1',F'4',F'6'
         END   BEGIN""")

prog("popcnt", "شمارش بیت‌های ۱ با ترفند x AND (x−1)", """
POPCNT   START 0
BEGIN    BALR  12,0
         USING *,12
         L     4,X            R4 = x
         SR    3,3            count = 0
         OR    4,4            فقط برای تنظیم CC
         BZ    DONE           x = 0: تمام
LOOP     LA    3,1(3)         count += 1
         LR    5,4
         BCTR  5,0            R5 = x − 1
         NR    4,5            x = x AND (x−1): پاک شدن پایین‌ترین ۱
         BNZ   LOOP
DONE     ST    3,COUNT
         EOJ
X        DC    F'46833'       = 0000B6F1h
COUNT    DS    F
         END   BEGIN""")

prog("callsub", "زیربرنامه با BALR 14,15 و بازگشت با BR 14", """
CALLSUB  START 0
BEGIN    BALR  12,0
         USING *,12
         LA    15,SQR         R15 = نشانی زیربرنامه
         L     1,X
         BALR  14,15          R14 = نشانی بازگشت؛ پرش به SQR
         ST    1,X2           X2 = x²
         L     1,Y
         BALR  14,15          فراخوانی دوباره
         ST    1,Y2
         EOJ
SQR      MR    0,1            R0:R1 = R1 × R1
         BR    14             بازگشت به نشانی داخل R14
X        DC    F'12'
Y        DC    F'-7'
X2       DS    F
Y2       DS    F
         END   BEGIN""")

prog("fact", "فاکتوریل با MR روی جفت R2:R3 و BCT", """
FACT     START 0
BEGIN    BALR  12,0
         USING *,12
         LA    3,1            R3 = حاصل‌ضرب = 1
         L     5,N            شمارنده = n
LOOP     MR    2,5            R2:R3 = R3 × R5
         BCT   5,LOOP         R5 = n, n−1, …, 1
         ST    3,F            F = n!
         EOJ
N        DC    F'6'
F        DS    F
         END   BEGIN""")

ARR = [5, -2, 7, 10, 0, 3, -8, 1, 4, 6]


def run(pid, patch=None):
    title, src = P360[pid]
    a = assemble(src)
    cpu = CPU(a.image)
    if patch:
        patch(a, cpu)
    if a.entry is not None:
        cpu.run(a.entry)
    return a, cpu


def word(a, cpu, name, k=0):
    return s32(cpu.rd(a.sym[name][0] + 4 * k))


RESULTS360 = {}


def run_programs360(verbose=True):
    R = RESULTS360
    a, c = run("stock")
    assert word(a, c, "NEWOH") == 7
    R["stock"] = "NEWOH = 9 + 4 − 6 = 7"
    a, c = run("vardef")
    assert [a.sym[k][0] for k in ("VAR1", "VAR2", "VAR3")] == [0x100, 0x10C, 0x110]
    assert [s32(c.rd(0x10C + 4 * k)) for k in range(5)] == [1, 1, -2, 100, 100]
    R["vardef"] = "VAR1 = 100h، VAR2 = 10Ch، VAR3 = 110h؛ حافظه مثل شکل اسلاید"
    a, c = run("vardef2")
    assert [a.sym[k][0] for k in "ABCDEFG"] == [0x1001, 0x1004, 0x1008, 0x100C, 0x1014, 0x1016, 0x1018]
    R["vardef2"] = "A = 1001h، B = 1004h، C = 1008h، D = 100Ch، E = 1014h، F = 1016h، G = 1018h"
    a, c = run("sumarr")
    assert word(a, c, "SUM") == sum(ARR)
    R["sumarr"] = "SUM = %d" % sum(ARR)
    a, c = run("maxarr")
    assert word(a, c, "MAX") == max(ARR)
    R["maxarr"] = "MAX = %d" % max(ARR)
    a, c = run("cntneg")
    assert word(a, c, "COUNT") == sum(1 for v in ARR if v < 0)
    R["cntneg"] = "COUNT = %d" % sum(1 for v in ARR if v < 0)
    a, c = run("avg")
    assert (word(a, c, "MEAN"), word(a, c, "REM")) == (2, 6)
    R["avg"] = "MEAN = 26 / 10 = 2، REM = 6"
    a, c = run("fib")
    f = [0, 1]
    while len(f) < 20:
        f.append(f[-1] + f[-2])
    assert [word(a, c, "F", k) for k in range(20)] == f
    R["fib"] = "F = 0, 1, 1, 2, …, 4181"
    a, c = run("sumn")
    assert word(a, c, "SUM") == 5050
    R["sumn"] = "SUM = 5050"
    a, c = run("evens")
    assert word(a, c, "COUNT") == sum(1 for v in ARR if v % 2 == 0)
    R["evens"] = "COUNT = %d (−2، 10، 0، −8، 4، 6)" % sum(1 for v in ARR if v % 2 == 0)
    a, c = run("swap")
    assert (word(a, c, "X"), word(a, c, "Y")) == (-77, 1234)
    R["swap"] = "X = −77، Y = 1234"
    a, c = run("gnome")
    assert [word(a, c, "A", k) for k in range(10)] == sorted(ARR)
    rnd = random.Random(360)
    for _ in range(20):
        vals = [rnd.randint(-9, 9) for _ in range(10)]

        def patch(a, cpu, vals=vals):
            for k, v in enumerate(vals):
                cpu.wr(a.sym["A"][0] + 4 * k, v)
        a, c = run("gnome", patch)
        assert [word(a, c, "A", k) for k in range(10)] == sorted(vals)
    R["gnome"] = "آرایه صعودی شد (و ۲۰ آرایهٔ تصادفی با عددهای تکراری)"
    a, c = run("add64")
    assert (c.rd(a.sym["SHI"][0]), c.rd(a.sym["SLO"][0])) == (4, 4)
    R["add64"] = "(1:FFFFFFFF) + (2:00000005) = 4:00000004"
    a, c = run("divneg")
    assert (word(a, c, "Q"), word(a, c, "R")) == (-9, -2)
    R["divneg"] = "−47 / 5 ⇒ Q = −9، R = −2"
    a, c = run("pow2")
    assert word(a, c, "P") == 1024
    R["pow2"] = "P = 1024"
    a, c = run("ifmax")
    assert word(a, c, "MAX") == 13
    for x, y in ((20, 13), (13, 13), (-5, -9)):
        def patch(a, cpu, x=x, y=y):
            cpu.wr(a.sym["A"][0], x)
            cpu.wr(a.sym["B"][0], y)
        a, c = run("ifmax", patch)
        assert word(a, c, "MAX") == max(x, y)
    R["ifmax"] = "MAX = max(−8, 13) = 13"
    a, c = run("search")
    assert word(a, c, "POS") == ARR.index(1)
    for key in (5, 6, -8, 99):
        def patch(a, cpu, key=key):
            cpu.wr(a.sym["KEY"][0], key)
        a, c = run("search", patch)
        assert word(a, c, "POS") == (ARR.index(key) if key in ARR else -1)
    R["search"] = "KEY = 1 ⇒ POS = 7 (و KEY = 99 ⇒ POS = −1)"
    a, c = run("reverse")
    assert [word(a, c, "ARR", k) for k in range(10)] == ARR[::-1]
    R["reverse"] = "ARR = 6, 4, 1, −8, 3, 0, 10, 7, −2, 5"
    a, c = run("popcnt")
    assert word(a, c, "COUNT") == bin(0xB6F1).count("1")
    for x in (0, 1, -1, 0x80000000, 0x12345678):
        def patch(a, cpu, x=x):
            cpu.wr(a.sym["X"][0], x)
        a, c = run("popcnt", patch)
        assert word(a, c, "COUNT") == bin(x & 0xFFFFFFFF).count("1")
    R["popcnt"] = "B6F1h ⇒ COUNT = %d" % bin(0xB6F1).count("1")
    a, c = run("callsub")
    assert (word(a, c, "X2"), word(a, c, "Y2")) == (144, 49)
    R["callsub"] = "X2 = 144، Y2 = 49"
    a, c = run("fact")
    assert word(a, c, "F") == 720
    R["fact"] = "6! = 720"
    if verbose:
        print("IBM360 programs verified:", ", ".join(R))
    return R


if __name__ == "__main__":
    run_programs360()
    for pid in ("sumarr", "gnome"):
        a, c = run(pid)
        for r in a.rows:
            if r["kind"] in ("ins", "dc", "ds"):
                print("%06X %-14s %s" % (r["loc"], r.get("obj", b"").hex().upper(), r["raw"]))
