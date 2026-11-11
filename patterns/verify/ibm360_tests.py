"""Every example of lectures 6-8 (IBM 360): machine code, result and condition code, checked on the model."""
from ibm360 import CCSTR, CPU, assemble, s32

BASES = {12: 0x10000, 11: 0x20000, 10: 0x30000, 9: 0x40000}


def one(line, regs=None, mem=None, syms=None, cc=None, bases=None):
    """Assemble a single statement at 8000h (with USING for the base registers) and execute it once."""
    bases = {**BASES, **(bases or {})}
    presym = {f"B{r}": v for r, v in bases.items()}
    presym.update(syms or {})
    src = "T        START X'8000'\n" + "".join(f"         USING B{r},{r}\n" for r in bases) + line + "\n         END"
    a = assemble(src, presym)
    row = [r for r in a.rows if r["kind"] == "ins"][0]
    R = {r: v for r, v in bases.items()}
    R.update(regs or {})
    cpu = CPU(a.image, R, mem)
    if cc is not None:
        cpu.cc = cc
    cpu.pc = row["loc"]
    cpu.step()
    return row["obj"].hex().upper(), cpu, row


CHECKS = []


def check(name, line, code, expect=None, **kw):
    got, cpu, row = one(line, **kw)
    assert got == code, (name, line, got, code)
    if expect:
        for k, v in expect.items():
            if k == "CC":
                assert CCSTR[cpu.cc] == v, (name, line, CCSTR[cpu.cc], v)
            elif k == "PC":
                assert cpu.pc == v, (name, line, hex(cpu.pc), hex(v))
            elif isinstance(k, int):
                assert s32(cpu.R[k]) == s32(v), (name, line, k, s32(cpu.R[k]), v)
            elif k.startswith("M"):
                assert cpu.rd(int(k[1:], 16)) == v & 0xFFFFFFFF, (name, line, k)
            elif k.startswith("B"):
                assert cpu.mem.get(int(k[1:], 16)) == v, (name, line, k)
    CHECKS.append(name)
    return cpu


def run_ibm360_tests(verbose=True):
    W = lambda a, v: {a: v & 0xFFFFFFFF}
    # ---------------- lecture 6: one example per format
    check("6 SR", "         SR    12,5", "1BC5", {12: 30 - 8}, regs={12: 30, 5: 8})
    check("6 NR", "         NR    6,10", "146A", {6: 0b1100 & 0b1010}, regs={6: 0b1100, 10: 0b1010})
    from ibm360 import assemble as _a  # encoding-only checks for misaligned slide addresses
    for line, code, syms in [("         S     10,NUM", "5BA0C01A", {"NUM": 0x1001A}),
                             ("         L     15,N10", "58F0B11B", {"N10": 0x2011B}),
                             ("         SLL   5,3", "89500003", {}),
                             ("         LM    2,5,A", "9825C01B", {"A": 0x1001B}),
                             ("         MVI   T1,X'5F'", "925FC0BA", {"T1": 0x100BA}),
                             ("         OI    100(3),C'*'", "965C3064", {}),
                             ("         MVC   DST(100),SRC", "D263C00AC110", {"DST": 0x1000A, "SRC": 0x10110}),
                             ("         OC    AREA(10),10(4)", "D609911B400A", {"AREA": 0x4011B}),
                             ("         AP    NUM1(6),NUM2(5)", "FA54C10ACF10", {"NUM1": 0x1010A, "NUM2": 0x10F10})]:
        presym = {f"B{r}": v for r, v in BASES.items()}
        presym.update(syms)
        src = "T        START X'8000'\n" + "".join(f"         USING B{r},{r}\n" for r in BASES) + line + "\n         END"
        got = [r for r in _a(src, presym).rows if r["kind"] == "ins"][0]["obj"].hex().upper()
        assert got == code, (line, got, code)
        CHECKS.append("6 " + line.split()[0])
    # semantics of SLL / LM / MVI / OI / MVC / OC
    check("6 SLL run", "         SLL   5,3", "89500003", {5: 40}, regs={5: 5})
    check("6 LM run", "         LM    2,5,A", "9825C010", {2: 1, 3: 2, 4: 3, 5: 4}, syms={"A": 0x10010},
                mem={0x10010: 1, 0x10014: 2, 0x10018: 3, 0x1001C: 4})
    check("6 MVI run", "         MVI   T1,X'5F'", "925FC0BA", {"B100BA": 0x5F}, syms={"T1": 0x100BA})
    check("6 OI run", "         OI    100(3),C'*'", "965C3064", {"B30064": 0x5C}, regs={3: 0x30000})
    check("6 MVC run", "         MVC   DST(4),SRC", "D203C00AC110", {"B1000A": 0xAB, "B1000D": 0x12}, syms={"DST": 0x1000A, "SRC": 0x10110},
          mem={0x10110: 0xAB000012})

    # ---------------- lecture 7: RR instructions
    check("7 LR", "         LR    3,5", "1835", {3: 77}, regs={5: 77})
    check("7 LR2", "         LR    B'101',X'D'", "185D", {5: -9}, regs={13: -9})
    check("7 LCR1", "         LCR   2,2", "1322", {2: 33, "CC": "10"}, regs={2: -33})
    check("7 LCR2", "REG5     EQU   5\n         LCR   REG5,1", "1351", {5: 0, "CC": "00"}, regs={1: 0})
    check("7 LNR1", "         LNR   2,4", "1124", {2: -123, "CC": "01"}, regs={4: -123})
    check("7 LNR2", "         LNR   5,5", "1155", {5: -13, "CC": "01"}, regs={5: 13})
    check("7 LPR1", "         LPR   B'010',7", "1027", {2: 123, "CC": "10"}, regs={7: -123})
    check("7 LPR2", "         LPR   5,B'101'", "1055", {5: 13, "CC": "10"}, regs={5: 13})
    check("7 AR1", "         AR    2,7", "1A27", {2: -118, "CC": "01"}, regs={2: -123, 7: 5})
    check("7 AR2", "         AR    5,6", "1A56", {5: 7, "CC": "10"}, regs={5: -13, 6: 20})
    check("7 SR1", "         SR    8,8", "1B88", {8: 0, "CC": "00"}, regs={8: -50000})
    check("7 SR2", "         SR    5,6", "1B56", {5: 9, "CC": "10"}, regs={5: -13, 6: -22})
    check("7 MR1", "         MR    8,4", "1C84", {8: -1, 9: -35, "CC": "01"}, regs={8: -5, 9: 5, 4: -7})
    check("7 MR2", "         MR    4,5", "1C45", {4: 0, 5: 4, "CC": "10"}, regs={4: -10, 5: -2})
    check("7 DR1", "         DR    8,4", "1D84", {9: 100, 8: 3, "CC": "10"}, regs={8: 0, 9: 503, 4: 5})
    check("7 DR2", "         DR    4,6", "1D46", {5: -3, 4: -2, "CC": "01"}, regs={4: -1, 5: -11, 6: 3})
    check("7 ALR1", "         ALR   2,7", "1E27", {2: 3, "CC": "11"}, regs={2: 0xFFFFFFFE, 7: 5})
    check("7 ALR2", "         ALR   5,6", "1E56", {5: 33, "CC": "10"}, regs={5: 13, 6: 20})
    check("7 SLR1", "         SLR   8,8", "1F88", {8: 0, "CC": "00"}, regs={8: 0xFFF78955})
    check("7 SLR2", "         SLR   5,6", "1F56", {5: 0xFFFFFFF4, "CC": "11"}, regs={5: 20, 6: 32})
    check("7 NR1", "         NR    4,9", "1449", {4: 0, "CC": "00"}, regs={4: 0xFFFFFFFE, 9: 1})
    check("7 NR2", "         NR    5,6", "1456", {5: 4, "CC": "10"}, regs={5: 20, 6: 36})
    check("7 OR1", "         OR    4,6", "1646", {4: -1, "CC": "01"}, regs={4: 0xFFFFFFFE, 6: 1})
    check("7 OR2", "         OR    5,6", "1656", {5: 52, "CC": "10"}, regs={5: 20, 6: 36})
    check("7 XR1", "         XR    4,6", "1746", {4: -11, "CC": "01"}, regs={4: 0xFFFFFFFE, 6: 11})
    check("7 XR2", "         XR    5,6", "1756", {5: 9, "CC": "10"}, regs={5: -1, 6: -10})
    check("7 CR1", "         CR    8,8", "1988", {"CC": "00"}, regs={8: -50780})
    check("7 CR2", "         CR    5,6", "1956", {"CC": "10"}, regs={5: -13, 6: -22})
    check("7 CLR1", "         CLR   8,8", "1588", {"CC": "00"}, regs={8: 0xFFF78901})
    check("7 CLR2", "         CLR   5,6", "1556", {"CC": "10"}, regs={5: -1, 6: 31})
    check("7 BCTR1", "         BCTR  8,7", "0687", {8: 1, "PC": 0x1FFFF0}, regs={8: 2, 7: 0x011FFFF0})
    check("7 BCTR2", "         BCTR  5,0", "0650", {5: 22, "PC": 0x8002}, regs={5: 23, 0: -22})

    # ---------------- lecture 8: RX instructions
    check("8 L1", "         L     2,ARR(4)", "5824C123", {2: 555}, syms={"ARR": 0x10123}, regs={4: 1}, mem=W(0x10124, 555))
    check("8 L2", "         L     2,ARR", "5820C123", {2: 556}, syms={"ARR": 0x10124}, bases={12: 0x10001},
          mem=W(0x10124, 556))
    check("8 L3", "         L     2,20(4,3)", "58243014", {2: 7}, regs={3: 0x50000, 4: 0}, mem=W(0x50014, 7))
    check("8 L4", "         L     2,0(5)", "58250000", {2: 9}, regs={5: 0x50000}, mem=W(0x50000, 9))
    check("8 L5", "         L     2,10(,5)", "5820500A", {2: 4}, regs={5: 0x50002}, mem=W(0x5000C, 4))
    check("8 ST1", "         ST    2,ARR(4)", "5024C100", {"M10104": 66}, syms={"ARR": 0x10100}, regs={2: 66, 4: 4})
    check("8 ST2", "         ST    2,ARR", "5020C100", {"M10100": 67}, syms={"ARR": 0x10100}, regs={2: 67})
    check("8 ST3", "         ST    2,20(4,3)", "50243014", {"M50014": 5}, regs={2: 5, 3: 0x50000, 4: 0})
    check("8 ST4", "         ST    6,0(5)", "50650000", {"M50000": 6}, regs={6: 6, 5: 0x50000})
    check("8 ST5", "         ST    3,10(,5)", "5030500A", {"M5000C": 3}, regs={3: 3, 5: 0x50002})
    check("8 A1", "         A     7,ABS(6)", "5A76B234", {7: 77, "CC": "10"}, syms={"ABS": 0x20234}, regs={6: 0, 7: 200},
          mem=W(0x20234, -123))
    check("8 A2", "         A     4,5(6,7)", "5A467005", {4: -67, "CC": "01"}, regs={6: 0x30000, 7: 3, 4: -400},
          mem=W(0x30008, 333))
    check("8 A3", "         A     6,0(10)", "5A6A0000", {6: 0, "CC": "00"}, regs={10: 0x30010, 6: -25}, mem=W(0x30010, 25))
    check("8 S1", "         S     3,AAA(6)", "5B36A0C8", {3: 0x80000000, "CC": "11"}, syms={"AAA": 0x300C8},
          regs={6: 0, 3: 0x7FFFFFFF}, mem=W(0x300C8, -1))
    check("8 S2", "         S     2,33(7)", "5B270021", {2: -30, "CC": "01"}, regs={7: 0x30003, 2: -10}, mem=W(0x30024, 20))
    check("8 S3", "         S     0,0(1)", "5B010000", {0: 5, "CC": "10"}, regs={1: 0x30100, 0: 5}, mem=W(0x30100, 0))
    check("8 M1", "         M     2,Hamid(6)", "5C26C27F", {2: -1, 3: 0x80000001, "CC": "01"}, syms={"Hamid": 0x1027F},
          regs={6: 1, 3: 0x7FFFFFFF, 2: 0}, mem=W(0x10280, -1))
    check("8 M2", "         M     2,33(7)", "5C270021", {2: -1, 3: -200, "CC": "01"}, regs={7: 0x30003, 3: -10, 2: 0x45F2},
          mem=W(0x30024, 20))
    check("8 M3", "         M     0,0(10)", "5C0A0000", {0: 0, 1: 42, "CC": "10"}, regs={10: 0x30010, 0: 5, 1: 2},
          mem=W(0x30010, 21))
    check("8 D1", "         D     2,Hokm(2)", "5D22C00F", {3: -10, 2: 3, "CC": "01"}, syms={"Hokm": 0x10010},
          bases={12: 0x10001}, regs={2: 0, 3: 173}, mem=W(0x10010, -17))
    check("8 D2", "         D     2,33(7)", "5D270021", {3: -2, 2: 0, "CC": "01"}, regs={7: 0x30003, 3: -20, 2: -1},
          mem=W(0x30024, 10))
    check("8 D3", "         D     0,0(10)", "5D0A0000", {1: 0, 0: 2, "CC": "00"}, regs={10: 0x30010, 0: 0, 1: 2},
          mem=W(0x30010, 21))
    check("8 AL1", "         AL    8,SOS+2(7)", "5E87C202", {8: 323, "CC": "10"}, syms={"SOS": 0x10200}, regs={7: 2, 8: 200},
          mem=W(0x10204, 123))
    check("8 AL2", "         AL    4,X'555'(6,7)", "5E467555", {4: 1733, "CC": "10"}, regs={6: 0x30000, 7: 3, 4: 1400},
          mem=W(0x30558, 333))
    check("8 AL3", "         AL    2,0(1)", "5E210000", {2: 0, "CC": "11"}, regs={1: 0x30100, 2: -25}, mem=W(0x30100, 25))
    check("8 SL1", "         SL    8,SIX-16(7)", "5F87C1F0", {8: 77, "CC": "10"}, syms={"SIX": 0x10200}, regs={7: 0, 8: 200},
          mem=W(0x101F0, 123))
    check("8 SL2", "         SL    4,B'111'(6,7)", "5F467007", {4: 1067, "CC": "10"}, regs={6: 0x30000, 7: 1, 4: 1400},
          mem=W(0x30008, 333))
    check("8 SL3", "         SL    2,0(1)", "5F210000", {2: 0, "CC": "00"}, regs={1: 0x30100, 2: 35}, mem=W(0x30100, 35))
    check("8 C1", "         C     2,HEY(11)", "592BC070", {"CC": "01"}, syms={"HEY": 0x10070}, regs={11: 0x10, 2: -120},
          mem=W(0x10080, -100))
    check("8 C2", "         C     4,B'11'(B'10',X'A')", "5942A003", {"CC": "10"}, regs={2: 1, 10: 0x30000, 4: 140},
          mem=W(0x30004, 33))
    check("8 C3", "         C     2,0(1)", "59210000", {"CC": "00"}, regs={1: 0x30100, 2: 35}, mem=W(0x30100, 35))
    check("8 CL1", "         CL    2,HEY(11)", "552BC070", {"CC": "10"}, syms={"HEY": 0x10070}, regs={11: 0x10, 2: -120},
          mem=W(0x10080, 100))
    check("8 CL2", "         CL    4,B'11'(B'10',X'A')", "5542A003", {"CC": "01"}, regs={2: 1, 10: 0x30000, 4: 1},
          mem=W(0x30004, 3))
    check("8 CL3", "         CL    2,0(1)", "55210000", {"CC": "00"}, regs={1: 0x30100, 2: -5}, mem=W(0x30100, -5))
    for op, code, r0, cc0, r3, cc3, r2, cc2 in [("N", "54", 0x74, "10", 1, "10", -5, "01"),
                                                ("O", "56", -1, "01", -13, "01", -5, "01"),
                                                ("X", "57", 0xFFFFFF8B, "01", -14, "01", 0, "00")]:
        check("8 %s1" % op, "         %-5s 0,ME(11)" % op, code + "0BC070", {0: r0, "CC": cc0}, syms={"ME": 0x10070},
              regs={11: 0x10, 0: -4}, mem=W(0x10080, 0x77))
        check("8 %s2" % op, "         %-5s 3,4(5,6)" % op, code + "356004", {3: r3, "CC": cc3}, regs={5: 0x30000, 6: 0, 3: 1},
              mem=W(0x30004, -13))
        check("8 %s3" % op, "         %-5s 2,0(1)" % op, code + "210000", {2: r2, "CC": cc2}, regs={1: 0x30100, 2: -5},
              mem=W(0x30100, -5))
    check("8 LA1", "         LA    3,4(5,6)", "41356004", {3: 0x001AF234}, regs={5: 0x1AF000, 6: 0x230})
    check("8 LA2", "         LA    1,1(1)", "41110001", {1: 78}, regs={1: 77})
    check("8 BCT1", "         BCT   3,LOOP", "4630C1FF", {3: 1, "PC": 0x101FF}, syms={"LOOP": 0x101FF}, regs={3: 2})
    check("8 BCT2", "         BCT   1,2(3,4)", "46134002", {1: 0, "PC": 0x8004}, regs={1: 1})
    check("8 BC1", "         BC    3,LOOP", "4730C1FF", {"PC": 0x101FF}, syms={"LOOP": 0x101FF}, cc=3)
    check("8 BC2", "         BC    B'1011',2(3,4)", "47B34002", {"PC": 0x50000 + 8 + 2}, regs={3: 0x50000, 4: 8}, cc=2)
    check("8 BC3", "         BNE   LOP1", "4770C100", {"PC": 0x8004}, syms={"LOP1": 0x10100}, cc=0)
    check("8 BC4", "         BNO   12(3,4)", "47E3400C", {"PC": 0x50000 + 8 + 12}, regs={3: 0x50000, 4: 8}, cc=2)
    check("8 BCR1", "         BCR   8,7", "0787", {"PC": 0x60000}, regs={7: 0x60000}, cc=0)
    check("8 BCR2", "         BOR   5", "0715", {"PC": 0x8002}, regs={5: 0x60000}, cc=1)
    if verbose:
        print("IBM360 slide examples verified:", len(CHECKS))
    return CHECKS


def stock():
    src = """STOCK    START 256
BEGIN    BALR  11,0
         USING *,11
         L     3,OLDOH
         A     3,RECPT
         S     3,ISSUE
         ST    3,NEWOH
         EOJ
OLDOH    DC    F'9'
RECPT    DC    F'4'
ISSUE    DC    F'6'
NEWOH    DS    F
         END   BEGIN"""
    a = assemble(src)
    cpu = CPU(a.image).run(a.entry)
    return a, cpu


if __name__ == "__main__":
    run_ibm360_tests()
    a, cpu = stock()
    for r in a.rows:
        if r["kind"] in ("ins", "dc", "ds"):
            print("%06X %-12s %s" % (r["loc"], r.get("obj", b"").hex().upper(), r["raw"]))
    print("NEWOH =", cpu.rd(a.sym["NEWOH"][0]), "R11 =", hex(cpu.R[11]))
