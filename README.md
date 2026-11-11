# ساختار و زبان کامپیوتر — جزوه و چیت‌شیت

🌐 **نسخهٔ آنلاین:** https://iamhirad.github.io/Sarbazi/

| فایل | توضیح |
|---|---|
| `CSL_Jozveh_Persian.pdf` | جزوهٔ کامل فارسی جلسه‌های ۱ تا ۸ (۱۹۳ صفحه، تا IBM 360) با کادرهای «شهود» و حل همهٔ تمرین‌ها |
| `CSL_CheatSheet.pdf` | چیت‌شیت ۱۱ صفحه‌ای برای امتحان کتاب‌باز (با جدول کامل دستورهای IBM 360) |
| `CSL_MachineCode_CheatSheet.pdf` | چیت‌شیت نوشتن کد ماشین: ۷۴ قاعده از ساده تا پیشرفته (با IBM 360) و مثال‌های ساخته‌شده با اسمبلر (۱۰ صفحه) |
| `CSL_Programs_Catalog.pdf` | کاتالوگ ۷۵ برنامهٔ جزوه (با ۲۱ برنامهٔ IBM 360)، میان‌ترم‌ها و الگوها: قالب دستور هر ماشین، کد ماشین، فیلدها و کد اسمبلی (۳۸ صفحه) |
| `CSL_Patterns.pdf` | ایده‌ها و الگوهای حل مسئله (۲۴ الگو + ۲۰ الگوی IBM 360 با کد) + حل کامل میان‌ترم‌های ۹۸ تا ۱۴۰۲ (۱۴ صفحه) |

ساخت دوباره (Python 3، pypdf، Playwright/Chromium، pdftotext):

```
cd jozveh && python3 build.py        # جزوه
cd cheatsheet && python3 build.py    # چیت‌شیت
cd mcode && python3 build.py         # چیت‌شیت نوشتن کد ماشین
cd catalog && python3 build.py       # کاتالوگ برنامه‌ها (همهٔ برنامه‌ها را اجرا و با جزوه مقایسه می‌کند)
cd patterns && python3 build.py      # الگوها و حل میان‌ترم‌ها (اول همهٔ کدها را روی شبیه‌ساز اجرا و بررسی می‌کند)
cd site && python3 build.py          # سایت (خروجی در site/_site، منتشرشده روی شاخهٔ gh-pages)
```

کدهای `patterns/verify/` مدل اسمبلر و شبیه‌ساز ماشین‌های میان‌ترم‌ها هستند؛ `python3 patterns/verify/programs.py` همهٔ برنامه‌های الگوها را اجرا و بررسی می‌کند. `patterns/verify/ibm360.py` اسمبلر و شبیه‌ساز IBM 360 است: `python3 patterns/verify/ibm360_tests.py` ۱۰۱ مثال اسلایدهای ۶ تا ۸ و `python3 patterns/verify/programs360.py` ۲۱ برنامهٔ 360 جزوه را بررسی می‌کند.
