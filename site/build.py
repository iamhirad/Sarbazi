#!/usr/bin/env python3
"""Assemble the GitHub Pages site into site/_site (published on the gh-pages branch)."""
import datetime
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OUT = ROOT / "_site"
FONTS = REPO / "jozveh" / "fonts"
PDFS = {"JOZ": REPO / "CSL_Jozveh_Persian.pdf", "CS": REPO / "CSL_CheatSheet.pdf"}
FA = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


def jalali(d):
    """Gregorian date -> (y, m, d) in the Persian calendar."""
    gy, gm, gd = d.year, d.month, d.day
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + g_d_m[gm - 1]
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def pdf_pages(p):
    out = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True, check=True).stdout
    return int(next(line.split()[-1] for line in out.splitlines() if line.startswith("Pages:")))


def thumb(pdf, dest, width=840, ratio=150 / 210):
    tmp = OUT / "_tmp"
    subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "110", "-png", "-singlefile", str(pdf), str(tmp)], check=True)
    im = Image.open(f"{tmp}.png").convert("RGB")
    w, h = im.size
    im = im.resize((width, round(h * width / w)), Image.LANCZOS)
    im = im.crop((0, 0, width, round(width * ratio)))
    im.save(dest, "WEBP", quality=80, method=6)
    Path(f"{tmp}.png").unlink()


OG_HTML = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>
@font-face{font-family:V;src:url(fonts/Vazirmatn-Black.woff2);font-weight:900}
@font-face{font-family:V;src:url(fonts/Vazirmatn-Regular.woff2);font-weight:400}
body{margin:0;width:1200px;height:630px;font-family:V;color:#fff;
background:linear-gradient(140deg,#0f2a57 0%,#1f5fbf 62%,#3d86e6 100%);display:flex;align-items:center}
.w{padding:0 90px}.k{font-size:30px;opacity:.85}.t{font-size:78px;font-weight:900;line-height:1.35;margin:10px 0 18px}
.s{font-size:34px;opacity:.92}.bar{width:180px;height:10px;background:#ffd36b;border-radius:6px;margin:28px 0}
</style></head><body><div class="w"><div class="k">دانشکدهٔ مهندسی کامپیوتر — دانشگاه صنعتی شریف</div>
<div class="t">ساختار و زبان کامپیوتر</div><div class="bar"></div>
<div class="s">جزوهٔ کامل ۱۱۲ صفحه‌ای + چیت‌شیت امتحان — جلسه‌های ۱ تا ۵</div></div></body></html>"""

OG_JS = """const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});
await p.goto('file://'+process.argv[2]);await p.evaluate(()=>document.fonts.ready);
await p.screenshot({path:process.argv[3]});await b.close();})();"""

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1f5fbf"/>
<rect x="18" y="18" width="28" height="28" rx="4" fill="none" stroke="#fff" stroke-width="4"/>
<path d="M24 10v8M32 10v8M40 10v8M24 46v8M32 46v8M40 46v8M10 24h8M10 32h8M10 40h8M46 24h8M46 32h8M46 40h8" stroke="#ffd36b" stroke-width="4" stroke-linecap="round"/></svg>"""


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets" / "fonts").mkdir(parents=True)
    for w in ("Regular", "Bold", "Black"):
        shutil.copy(FONTS / f"Vazirmatn-{w}.woff2", OUT / "assets" / "fonts")
    for p in PDFS.values():
        shutil.copy(p, OUT / p.name)
    (OUT / ".nojekyll").write_text("")
    (OUT / "assets" / "favicon.svg").write_text(FAVICON)

    thumb(PDFS["JOZ"], OUT / "assets" / "jozveh.webp")
    thumb(PDFS["CS"], OUT / "assets" / "cheatsheet.webp")

    og_dir = OUT / "assets"
    (og_dir / "og.html").write_text(OG_HTML, encoding="utf-8")
    js = OUT / "_og.js"
    js.write_text(OG_JS)
    subprocess.run(["node", str(js), str(og_dir / "og.html"), str(og_dir / "og.png")], check=True, cwd="/tmp")
    js.unlink()
    (og_dir / "og.html").unlink()

    page = (ROOT / "index.html").read_text(encoding="utf-8")
    for key, p in PDFS.items():
        mb = p.stat().st_size / 1_000_000
        size = f"{mb:.1f} مگابایت".translate(FA)
        page = page.replace("{{%s_PAGES}}" % key, str(pdf_pages(p)).translate(FA))
        page = page.replace("{{%s_SIZE}}" % key, size)
    jy, jm, jd = jalali(datetime.date.today())
    page = page.replace("{{UPDATED}}", f"{str(jd).translate(FA)} {MONTHS[jm - 1]} {str(jy).translate(FA)}")
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print("built", OUT)


if __name__ == "__main__":
    main()
