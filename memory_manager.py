import json
import os
import random

# 📁 مسیر فایل‌های حافظه
MAIN_FILE = "memory.json"
SHADOW_FILE = "shadow_memory.json"
MODE_FILE = "mode.json"


# ========================= 📦 مدیریت فایل =========================

def init_files():
    """ایجاد فایل‌های موردنیاز در صورت نبود"""
    for file in [MAIN_FILE, SHADOW_FILE, MODE_FILE]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

def load_data(file):
    """خواندن داده از فایل"""
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(file, data):
    """ذخیره داده در فایل"""
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ========================= 🧠 یادگیری و حافظه =========================

def learn(phrase, response):
    """افزودن پاسخ به جمله خاص"""
    data = load_data(MAIN_FILE)
    if phrase not in data:
        data[phrase] = []
    if response not in data[phrase]:
        data[phrase].append(response)
    save_data(MAIN_FILE, data)


def shadow_learn(phrase, response):
    """یادگیری پنهان زمانی که ربات خاموش است"""
    data = load_data(SHADOW_FILE)
    if phrase not in data:
        data[phrase] = []
    if response not in data[phrase]:
        data[phrase].append(response)
    save_data(SHADOW_FILE, data)


def merge_shadow_memory():
    """ترکیب حافظه پنهان با حافظه اصلی"""
    main = load_data(MAIN_FILE)
    shadow = load_data(SHADOW_FILE)
    for phrase, responses in shadow.items():
        if phrase not in main:
            main[phrase] = responses
        else:
            for r in responses:
                if r not in main[phrase]:
                    main[phrase].append(r)
    save_data(MAIN_FILE, main)
    save_data(SHADOW_FILE, {})


def get_reply(phrase):
    """پیدا کردن پاسخ برای جمله داده‌شده"""
    data = load_data(MAIN_FILE)
    if phrase in data and data[phrase]:
        return random.choice(data[phrase])
    else:
        # پاسخ پیش‌فرض
        defaults = [
            "من هنوز اینو یاد نگرفتم 😅",
            "می‌خوای یادم بدی؟ 😎",
            "این جمله رو نمی‌دونم، بگو یاد بگیرم؟ 🤔"
        ]
        return random.choice(defaults)


# ========================= 🎭 مودها =========================

def get_mode():
    data = load_data(MODE_FILE)
    return data.get("mode", "نرمال")

def set_mode(mode):
    data = {"mode": mode}
    save_data(MODE_FILE, data)


# ========================= 📈 آمار =========================

def get_stats():
    data = load_data(MAIN_FILE)
    mode = get_mode()
    return {
        "phrases": len(data),
        "responses": sum(len(v) for v in data.values()),
        "mode": mode
    }


# ========================= 💬 بهبود جمله =========================

def enhance_sentence(text):
    """کمی چاشنی مود به پاسخ اضافه می‌کند"""
    mood = get_mode()

    if mood == "شوخ":
        addons = ["😂", "😜", "🤣", "😆"]
    elif mood == "بی‌ادب":
        addons = ["😏", "😈", "🤨", "💢"]
    elif mood == "غمگین":
        addons = ["😔", "😞", "💔", "🥀"]
    else:
        addons = ["🙂", "🤖", "😇"]

    return f"{text} {random.choice(addons)}"
