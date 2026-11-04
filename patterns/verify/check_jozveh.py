"""Compare the hand-written machine code in the jozveh <asm> tables with the assembler output."""
import re
from pathlib import Path

from lecture_programs import LECTURE

JOZ = Path(__file__).resolve().parents[2] / "jozveh" / "src"
ORDER = ["m2_fib7", "m2_xorswap", "m2_expr", "m3_altfib", "m3_arrsum", "m3_selfmod", "m4_vecadd",
         "m5_arrsum", "m5_sumregs_straight", "m5_sumregs_loop", "a1_fib20", "m6_fib_slide",
         "m6_fib_better", "m7_gnome", "m7_primes"]


def unit_hex(m, bits):
    u = m.unit
    out = ""
    for i in range(0, len(bits), u):
        c = bits[i:i + u]
        out += "?" * ((u + 3) // 4) if "?" in c else "%0*X" % ((u + 3) // 4, int(c, 2))
    return out


def check(verbose=True):
    blocks = []
    for f in sorted(JOZ.glob("*.html")):
        blocks += re.findall(r"<asm[^>]*>(.*?)</asm>", f.read_text(encoding="utf-8"), re.S)
    assert len(blocks) == len(ORDER), len(blocks)
    compared = 0
    for pid, blk in zip(ORDER, blocks):
        cls, src, ext = LECTURE[pid]
        m = cls()
        img, lst = m.assemble(src, externals=ext)
        bya = {a: unit_hex(m, b) for a, l, mn, o, r, b in lst}
        for line in blk.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("!") or line == "--":
                continue
            cells = [c.strip() for c in line.split("|")]
            addr, mc = cells[0], re.sub(r"<[^>]+>|\s", "", cells[1])
            if not re.fullmatch(r"[0-9A-Fa-f]+", addr) or not mc or "…" in mc or "×" in mc:
                continue
            a = int(addr, 16)
            mine = bya.get(a)
            assert mine is not None, (pid, addr)
            if "?" in mc:
                mc_cmp, mine_cmp = mc.replace("?", ""), mine.replace("?", "")
                assert mine.startswith(mc_cmp) or mine_cmp == mc_cmp, (pid, addr, mc, mine)
            else:
                assert mine == mc.upper(), (pid, addr, mc, mine)
            compared += 1
    if verbose:
        print("jozveh listings match assembler output: %d rows in %d programs" % (compared, len(ORDER)))
    return compared


if __name__ == "__main__":
    check()
