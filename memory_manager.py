import json
import os
import random

MEMORY_FILE = "memory.json"
SHADOW_FILE = "shadow_memory.json"

# ======================= 📦 راه‌اندازی فایل‌های حافظه =======================

def init_files():
    """ایجاد فایل‌های حافظه در صورت نبود"""
    for file in [MEMORY_FILE, SHADOW_FILE]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump({
                    "data": {},
                    "users": [],
                    "stats": {"phrases": 0, "responses": 0, "mode": "نرمال"}
                }, f, ensure_ascii=False, indent=2)

# ======================= 📥 بارگذاری و ذخیره داده =======================

def load_data(filename=MEMORY_FILE):
    if not os.path.exists(filename):
        init_files()
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🧩 یادگیری =======================

def learn(phrase, response):
    """افزودن جمله و پاسخ به حافظه"""
    data = load_data()
    phrase = phrase.strip()
    response = response.strip()
    if phrase not in data["data"]:
        data["data"][phrase] = []
    if response not in data["data"][phrase]:
        data["data"][phrase].append(response)
    data["stats"]["phrases"] = len(data["data"])
    data["stats"]["responses"] = sum(len(v) for v in data["data"].values())
    save_data(MEMORY_FILE, data)

# ======================= 🕶 یادگیری سایه (در حالت غیرفعال) =======================

def shadow_learn(phrase, response):
    """ذخیره یادگیری در حالت غیرفعال برای تمرین بعدی"""
    data = load_data(SHADOW_FILE)
    if phrase not in data["data"]:
        data["data"][phrase] = []
    if response not in data["data"][phrase]:
        data["data"][phrase].append(response)
    save_data(SHADOW_FILE, data)

# ======================= 💬 واکشی پاسخ =======================

def get_reply(phrase):
    data = load_data()
    phrase = phrase.strip()
    if phrase in data["data"]:
        return random.choice(data["data"][phrase])
    else:
        # جستجو در عبارات مشابه
        for key in data["data"]:
            if key in phrase or phrase in key:
                return random.choice(data["data"][key])
    return "نمی‌دونم چی بگم 😅"

# ======================= 🎭 تنظیم و دریافت مود =======================

def set_mode(mode):
    data = load_data()
    data["stats"]["mode"] = mode
    save_data(MEMORY_FILE, data)

def get_stats():
    return load_data().get("stats", {"phrases": 0, "responses": 0, "mode": "نرمال"})

# ======================= 🧠 تقویت جمله =======================

def enhance_sentence(sentence):
    """افزودن تنوع به جمله‌ها"""
    extras = ["😄", "😉", "😂", "🌟", "✨", "😎", "😁"]
    if sentence.endswith("!") or sentence.endswith("؟") or sentence.endswith("."):
        return f"{sentence} {random.choice(extras)}"
    return f"{sentence}! {random.choice(extras)}"

# ======================= 🧩 جمله‌سازی تصادفی =======================

def generate_sentence():
    data = load_data()
    if not data["data"]:
        return "من هنوز چیزی یاد نگرفتم 😅"
    phrase = random.choice(list(data["data"].keys()))
    response = random.choice(data["data"][phrase])
    return f"{phrase} → {response}"

# ======================= 👥 ثبت کاربر =======================

def register_user(user_id):
    data = load_data()
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(MEMORY_FILE, data)
