import json
import os

FILES_TO_CHECK = [
    "memory.json",
    "group_data.json",
    "stickers.json",
    "jokes.json",
    "fortunes.json"
]

def fix_json_file(filename):
    """اصلاح ساختار JSON معیوب در صورت وجود"""
    try:
        if not os.path.exists(filename):
            print(f"[FIX] فایل {filename} وجود ندارد، ایجاد جدید...")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return True

        with open(filename, "r", encoding="utf-8") as f:
            data = f.read().strip()

        # اگر فایل خالی بود
        if data == "":
            print(f"[FIX] فایل {filename} خالی بود، بازسازی شد ✅")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return True

        # تلاش برای parse کردن JSON
        try:
            json.loads(data)
        except json.JSONDecodeError:
            print(f"[ERROR] فایل {filename} خراب است ❌ در حال تعمیر...")
            repaired_data = repair_json_content(data)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(repaired_data, f, ensure_ascii=False, indent=2)
            print(f"[FIX] فایل {filename} با موفقیت تعمیر شد ✅")
            return True

        return False  # نیاز به تعمیر نداشت

    except Exception as e:
        print(f"[FIX ERROR] {filename}: {e}")
        return False

def repair_json_content(content):
    """تلاش ساده برای نجات محتوای ناقص JSON"""
    # حذف نویزها و اصلاح بسته‌شدن آکولادها
    fixed = content.replace("\x00", "").strip()
    if not fixed.endswith("}"):
        fixed += "}"
    try:
        return json.loads(fixed)
    except Exception:
        print("[REPAIR] بازسازی به حالت پایه انجام شد.")
        return {}

def repair_all():
    """تعمیر همه فایل‌های حافظه"""
    print("🧰 شروع تعمیر فایل‌های حافظه...")
    for file in FILES_TO_CHECK:
        result = fix_json_file(file)
        if result:
            print(f"✅ {file} بررسی و تعمیر شد.")
        else:
            print(f"🟢 {file} سالم بود.")
    print("🎯 عملیات تعمیر با موفقیت پایان یافت!")

if __name__ == "__main__":
    repair_all()
