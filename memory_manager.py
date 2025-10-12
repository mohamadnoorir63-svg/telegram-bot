import json
import os
import random

# 📂 مسیر فایل‌های حافظه
MEMORY_FILE = "memory.json"
SHADOW_FILE = "shadow_memory.json"

# 🧠 حافظه‌ی درون‌برنامه‌ای
memory = {
    "data": {},
    "users": [],
    "mode": "نرمال"
}

# ======================= 📦 راه‌اندازی فایل‌ها =======================

def init_files():
    """بررسی و ایجاد فایل‌های اولیه در صورت نبود"""
    for file in [MEMORY_FILE, SHADOW_FILE]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump({"data": {}, "users": [], "mode": "نرمال"}, f, ensure_ascii=False, indent=2)

# ======================= 📥 بارگذاری و ذخیره =======================

def load_data(filename=MEMORY_FILE):
    """خواندن داده‌ها از فایل"""
    if not os.path.exists(filename):
        init_files()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"data": {}, "users": [], "mode": "نرمال"}

def save_data(data, filename=MEMORY_FILE):
    """ذخیره داده‌ها در فایل"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🧠 یادگیری =======================

def learn(phrase, response):
    """افزودن پاسخ جدید برای جمله‌ای خاص"""
    data = load_data()
    phrase = phrase.strip()
    response = response.strip()
    if phrase not in data["data"]:
        data["data"][phrase] = []
    if response not in data["data"][phrase]:
        data["data"][phrase].append(response)
        save_data(data)

def shadow_learn(phrase, response):
    """ذخیره در حافظه سایه وقتی ربات غیرفعاله"""
    data = load_data(SHADOW_FILE)
    phrase = phrase.strip()
    response = response.strip()
    if phrase not in data["data"]:
        data["data"][phrase] = []
    if response not in data["data"][phrase]:
        data["data"][phrase].append(response)
        save_data(data, SHADOW_FILE)

# ======================= 💬 پاسخ =======================

def get_reply(text):
    """پیدا کردن پاسخ تصادفی برای ورودی"""
    data = load_data()
    for key, responses in data["data"].items():
        if key in text:
            return random.choice(responses)
    # اگر پیدا نشد از حافظه سایه امتحان کن
    shadow = load_data(SHADOW_FILE)
    for key, responses in shadow["data"].items():
        if key in text:
            return random.choice(responses)
    return "نمی‌دونم چی بگم 😅"

# ======================= 🎭 مود پاسخ =======================

def set_mode(mode):
    """تنظیم مود فعلی ربات"""
    data = load_data()
    data["mode"] = mode
    save_data(data)

def get_mode():
    """گرفتن مود فعلی"""
    data = load_data()
    return data.get("mode", "نرمال")

# ======================= 📊 آمار =======================

def get_stats():
    """گرفتن آمار کلی حافظه"""
    data = load_data()
    phrases = len(data.get("data", {}))
    responses = sum(len(v) for v in data.get("data", {}).values())
    mode = data.get("mode", "نرمال")
    return {"phrases": phrases, "responses": responses, "mode": mode}

# ======================= ✨ بهبود جمله =======================

def enhance_sentence(sentence):
    """افزودن حس طبیعی به پاسخ"""
    endings = ["😂", "😄", "😉", "😅", "😎", "😜", "🤔", "🙂"]
    if not sentence:
        return "عه؟ 😅"
    if sentence.endswith("!"):
        return sentence + " " + random.choice(endings)
    if not sentence.endswith(("!", ".", "؟")):
        return sentence + " " + random.choice(endings)
    return sentence

# ======================= 🧩 جمله‌سازی تصادفی =======================

def generate_sentence():
    """تولید جمله‌ی تصادفی از حافظه"""
    data = load_data()
    if not data["data"]:
        return "فعلاً چیزی بلد نیستم 😅"
    phrase = random.choice(list(data["data"].keys()))
    responses = data["data"][phrase]
    return f"{phrase} → {random.choice(responses)}"
