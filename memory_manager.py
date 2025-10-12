import json
import os
import random

MAIN_MEMORY = "memory.json"
SHADOW_MEMORY = "shadow_memory.json"

# اگر فایل‌ها نبودن، بسازشون
def init_files():
    for file_name, default_data in [
        (MAIN_MEMORY, {"replies": {}, "learning": True, "mode": "نرمال", "users": []}),
        (SHADOW_MEMORY, {"hidden": {}})
    ]:
        if not os.path.exists(file_name):
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

# بارگذاری داده
def load_data(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)

# ذخیره داده
def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# آمار حافظه
def get_stats():
    data = load_data(MAIN_MEMORY)
    total_phrases = len(data.get("replies", {}))
    total_responses = sum(len(v) for v in data.get("replies", {}).values())
    mode = data.get("mode", "نرمال")
    total_users = len(data.get("users", []))
    return {
        "phrases": total_phrases,
        "responses": total_responses,
        "mode": mode,
        "users": total_users
    }

# گرفتن پاسخ از حافظه
def get_reply(text):
    data = load_data(MAIN_MEMORY)
    replies = data.get("replies", {})
    text = text.lower().strip()
    if text in replies:
        return random.choice(replies[text])
    random_words = ["عه 😅", "جدی؟", "باشه", "جالبه 😎", "نمی‌دونم والا"]
    return random.choice(random_words)
