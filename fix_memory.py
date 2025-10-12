import json
import os

def fix_json(file_path: str):
    """تعمیر خودکار فایل JSON خراب"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        print(f"✅ {file_path} سالم است.")
        return True
    except json.JSONDecodeError:
        print(f"⚠️ {file_path} خراب شده، تلاش برای تعمیر...")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        # حذف نویزهای غیر JSON
        raw = raw.strip().replace("\x00", "")
        if not raw.startswith("{"):
            idx = raw.find("{")
            if idx != -1:
                raw = raw[idx:]

        try:
            data = json.loads(raw)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ فایل {file_path} با موفقیت تعمیر شد.")
            return True
        except Exception as e:
            print(f"❌ نتوانستم فایل {file_path} را تعمیر کنم: {e}")
            return False
