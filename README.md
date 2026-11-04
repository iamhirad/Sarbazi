# ساختار و زبان کامپیوتر — جزوه و چیت‌شیت

🌐 **نسخهٔ آنلاین:** https://iamhirad.github.io/Sarbazi/

| فایل | توضیح |
|---|---|
| `CSL_Jozveh_Persian.pdf` | جزوهٔ کامل فارسی جلسه‌های ۱ تا ۵ (۱۱۲ صفحه) با حل همهٔ تمرین‌ها |
| `CSL_CheatSheet.pdf` | چیت‌شیت ۹ صفحه‌ای برای امتحان کتاب‌باز |
| `CSL_MachineCode_CheatSheet.pdf` | چیت‌شیت نوشتن کد ماشین: ۵۶ قاعده از ساده تا پیشرفته با مثال‌های ساخته‌شده با اسمبلر (۸ صفحه) |
| `CSL_Programs_Catalog.pdf` | کاتالوگ ۵۴ برنامهٔ جزوه، میان‌ترم‌ها و الگوها: قالب دستور هر ماشین، کد ماشین، فیلدها و کد اسمبلی (۲۷ صفحه) |
| `CSL_Patterns.pdf` | ایده‌ها و الگوهای حل مسئله (۲۴ الگو با کد) + حل کامل میان‌ترم‌های ۹۸ تا ۱۴۰۲ (۱۰ صفحه) |

ساخت دوباره (Python 3، pypdf، Playwright/Chromium، pdftotext):

```
cd jozveh && python3 build.py        # جزوه
cd cheatsheet && python3 build.py    # چیت‌شیت
cd mcode && python3 build.py         # چیت‌شیت نوشتن کد ماشین
cd catalog && python3 build.py       # کاتالوگ برنامه‌ها (همهٔ برنامه‌ها را اجرا و با جزوه مقایسه می‌کند)
cd patterns && python3 build.py      # الگوها و حل میان‌ترم‌ها (اول همهٔ کدها را روی شبیه‌ساز اجرا و بررسی می‌کند)
cd site && python3 build.py          # سایت (خروجی در site/_site، منتشرشده روی شاخهٔ gh-pages)
```

کدهای `patterns/verify/` مدل اسمبلر و شبیه‌ساز ماشین‌های میان‌ترم‌ها هستند؛ `python3 patterns/verify/programs.py` همهٔ برنامه‌های الگوها را اجرا و بررسی می‌کند.
