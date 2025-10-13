import re
import random
from memory_manager import learn, load_data, save_data, shadow_learn

# ===============================================================
# 🧠 یادگیری خودکار از متن کاربران — نسخه‌ی پیشرفته هماهنگ با auto_brain
# ===============================================================

def auto_learn_from_text(text: str):
    """یادگیری خودکار از گفت‌وگوهای طبیعی کاربران"""
    if not text or len(text) < 3:
        return

    text = text.strip().replace("؟", "?")

    # الگوهای پرسش‌های متداول
    patterns = {
        r"اسم(ت)? چیه": ["اسمم خنگوله 😅", "من خنگولم 🤖"],
        r"چطوری": ["خوبم تو چطوری؟ 😎", "عالیم 🤖", "رو فرمم!"],
        r"کجایی": ["اینجام پیش خودت 😅", "همین دور و برم 🤖"],
        r"چیکار میکنی": ["دارم یاد می‌گیرم 😁", "در حال رشد هوش مصنوعی‌ام 🤖"],
        r"دوست(م)? داری": ["خیلی زیاد 💙", "آره معلومه 😅"],
        r"کی ساختت": ["یه آدم مهربون 😎", "خودت چی فکر می‌کنی؟ 🤔"]
    }

    # بررسی الگوها
    for pattern, responses in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            learn(pattern, *responses)
            shadow_learn(text, random.choice(responses))
            return

    # یادگیری عمومی برای جملات جدید
    words = text.split()
    if len(words) >= 3:
        key = words[0]
        resp = f"{random.choice(['جالبه', 'آره', 'اوه', 'درسته', 'باشه'])} {words[-1]}"
        shadow_learn(key, resp)


# ===============================================================
# 🧹 پاک‌سازی هوشمند حافظه
# ===============================================================
def clean_duplicates():
    """حذف پاسخ‌های تکراری و بی‌فایده از حافظه"""
    mem = load_data("memory.json")
    if not mem.get("data"):
        return

    changed = False
    for phrase, responses in list(mem["data"].items()):
        if not isinstance(responses, list):
            continue

        # حذف تکراری‌ها
        cleaned = list(set(responses))

        # حذف پاسخ‌های بسیار کوتاه یا بی‌فایده
        cleaned = [r for r in cleaned if len(r.strip()) > 1]

        if cleaned != responses:
            mem["data"][phrase] = cleaned
            changed = True

    if changed:
        save_data("memory.json", mem)
        print("🧽 حافظه تمیز و بهینه شد ✅")
