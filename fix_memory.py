import json
import re
import shutil
import os

def fix_json(file_path):
    """
    🩺 تعمیر خودکار فایل JSON خراب بدون حذف داده‌ها.
    اگر فایل درست شد → True
    اگر نشد → False
    """

    if not os.path.exists(file_path):
        print(f"⚠️ فایل '{file_path}' وجود ندارد، قابل تعمیر نیست.")
        return False

    try:
        # تست باز کردن فایل
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        print(f"✅ {file_path} سالم است، نیازی به تعمیر ندارد.")
        return True

    except json.JSONDecodeError as e:
        print(f"🚨 خطای JSON در {file_path}: {e}")

        # بک‌آپ از فایل خراب
        backup_path = file_path + ".bak"
        shutil.copy(file_path, backup_path)
        print(f"💾 نسخه پشتیبان ساخته شد: {backup_path}")

        # خواندن کل محتوا
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # ✅ رفع ایرادهای رایج
        fixed = content.strip()

        # حذف کاراکترهای غیرضروری در ابتدا و انتها
        fixed = re.sub(r'^[^\{\[]+', '', fixed)
        fixed = re.sub(r'[^\}\]]+$', '', fixed)

        # اگر چیزی شبیه JSON نیست، یه ساختار خالی بسازه
        if not fixed.startswith("{") and not fixed.startswith("["):
            print(f"⚠️ ساختار JSON در {file_path} نامعتبر بود، بازسازی از صفر.")
            fixed = '{"data": {}, "users": []}'

        # حذف کاماهای اضافی قبل از بسته شدن
        fixed = re.sub(r',\s*([\}\]])', r'\1', fixed)

        # اگر آکولاد باز بدون بسته بود
        if fixed.count("{") > fixed.count("}"):
            fixed += "}" * (fixed.count("{") - fixed.count("}"))

        # اگر براکت باز بدون بسته بود
        if fixed.count("[") > fixed.count("]"):
            fixed += "]" * (fixed.count("[") - fixed.count("]"))

        # ذخیره فایل تعمیرشده
        try:
            data = json.loads(fixed)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ فایل {file_path} با موفقیت تعمیر شد.")
            return True

        except Exception as e2:
            print(f"❌ خطا در ذخیره فایل تعمیرشده: {e2}")
            print("⛔ فایل همچنان خراب است.")
            return False
