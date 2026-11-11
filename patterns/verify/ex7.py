"""Traces for the chapter-7 exercises (RR instructions)."""
from ibm360 import CPU, CCSTR, assemble, s32, Halt


def trace(lines, regs, show):
    src = "T        START X'1000'\n" + "\n".join("         " + l for l in lines) + "\n         END"
    a = assemble(src)
    cpu = CPU(a.image, regs)
    cpu.pc = 0x1000
    out = []
    for r in [r for r in a.rows if r["kind"] == "ins"]:
        try:
            cpu.step()
            out.append((r["mn"] + " " + r["ops"], r["obj"].hex().upper(),
                        {k: ("%08X" % cpu.R[k]) if k in show.get("hex", ()) else s32(cpu.R[k]) for k in show["regs"]},
                        CCSTR[cpu.cc]))
        except Halt as h:
            out.append((r["mn"] + " " + r["ops"], r["obj"].hex().upper(), str(h), "-"))
            break
    return out


EX = {
    "seq": (["LR    5,2", "AR    5,3", "SR    5,4", "LPR   6,5", "LCR   7,6", "XR    7,5", "MR    2,4", "DR    2,6"],
            {2: 7, 3: -3, 4: 10}, {"regs": [2, 3, 5, 6, 7]}),
    "ovf": (["AR    1,1", "LCR   2,3", "LPR   4,3", "ALR   5,6", "SR    7,8"],
            {1: 0x7FFFFFFF, 3: 0x80000000, 5: 0x7FFFFFFF, 6: 1, 7: 0x80000000, 8: 1}, {"regs": [1, 2, 4, 5, 7], "hex": (1, 2, 4, 5, 7)}),
    "cmp": (["CR    1,2", "CLR   1,2", "CR    3,4", "CLR   3,4"], {1: -1, 2: 1, 3: 5, 4: 0x80000000}, {"regs": [1, 2]}),
    "mul": (["MR    4,5"], {5: 100000}, {"regs": [4, 5], "hex": (4, 5)}),
    "div": (["DR    4,6"], {4: -1, 5: -7, 6: 2}, {"regs": [4, 5]}),
    "swap": (["XR    1,2", "XR    2,1", "XR    1,2"], {1: 0x0F, 2: 0x35}, {"regs": [1, 2], "hex": (1, 2)}),
    "sext": (["LA    4,1", "MR    2,4", "DR    2,6"], {3: -47, 6: 5, 2: 0x12345678}, {"regs": [2, 3]}),
    "bad": (["DR    3,5"], {3: 1, 5: 1}, {"regs": [3]}),
    "zero": (["DR    2,6"], {2: 0, 3: 9, 6: 0}, {"regs": [3]}),
    "bctr": (["BCTR  5,0", "BCTR  5,0"], {5: 1}, {"regs": [5], "hex": (5,)}),
}

if __name__ == "__main__":
    for k, (lines, regs, show) in EX.items():
        print("==", k)
        for row in trace(lines, regs, show):
            print("  ", row)
    a = assemble("T        START 0\n         AR    3,15\n         MR    6,7\n         BCR   15,14\n         BCTR  0,0\n         END")
    print([r["obj"].hex().upper() for r in a.rows if r["kind"] == "ins"])
