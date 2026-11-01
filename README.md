# ساختار و زبان کامپیوتر — جزوه و چیت‌شیت

🌐 **نسخهٔ آنلاین:** https://iamhirad.github.io/Sarbazi/

| فایل | توضیح |
|---|---|
| `CSL_Jozveh_Persian.pdf` | جزوهٔ کامل فارسی جلسه‌های ۱ تا ۵ (۱۱۲ صفحه) با حل همهٔ تمرین‌ها |
| `CSL_CheatSheet.pdf` | چیت‌شیت ۸ صفحه‌ای برای امتحان کتاب‌باز |

ساخت دوباره (Python 3، pypdf، Playwright/Chromium، pdftotext):

```
cd jozveh && python3 build.py        # جزوه
cd cheatsheet && python3 build.py    # چیت‌شیت
cd site && python3 build.py          # سایت (خروجی در site/_site، منتشرشده روی شاخهٔ gh-pages)
```
