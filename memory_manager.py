import json
import os
import random

MAIN_MEMORY = "memory.json"
SHADOW_MEMORY = "shadow_memory.json"

# ======================== 🧠 فایل‌ها =========================
def init_files():
    """ایجاد فایل‌های اولیه در صورت نبودن"""
    for file_name, default_data in [
        (MAIN_MEMORY, {"replies": {}, "learning": True, "mode": "نرمال", "users": []}),
        (SHADOW_MEMORY, {"hidden": {}})
    ]:
        if not os.path.exists(file_name):
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)


def load_data(file_name):
    """خواندن داده از فایل"""
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(file_name, data):
    """ذخیره داده در فایل"""
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ======================== 💡 یادگیری =========================
def learn(phrase, response):
    """یادگیری جمله جدید"""
    data = load_data(MAIN_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()
    if phrase not in data["replies"]:
        data["replies"][phrase] = []
    if response not in data["replies"][phrase]:
        data["replies"][phrase].append(response)
        save_data(MAIN_MEMORY, data)


def shadow_learn(phrase, response):
    """یادگیری پنهان (وقتی ربات خاموش است)"""
    data = load_data(SHADOW_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()
    if phrase not in data["hidden"]:
        data["hidden"][phrase] = []
    if response and response not in data["hidden"][phrase]:
        data["hidden"][phrase].append(response)
        save_data(SHADOW_MEMORY, data)


def merge_shadow_memory():
    """ادغام یادگیری پنهان در حافظه اصلی"""
    main_data = load_data(MAIN_MEMORY)
    shadow_data = load_data(SHADOW_MEMORY)
    for phrase, responses in shadow_data.get("hidden", {}).items():
        if phrase not in main_data["replies"]:
            main_data["replies"][phrase] = []
        for r in responses:
            if r not in main_data["replies"][phrase]:
                main_data["replies"][phrase].append(r)
    shadow_data["hidden"] = {}
    save_data(MAIN_MEMORY, main_data)
    save_data(SHADOW_MEMORY, shadow_data)


# ======================== 🗣 پاسخ =========================
def get_reply(text):
    """گرفتن پاسخ از حافظه"""
    data = load_data(MAIN_MEMORY)
    text = text.lower().strip()
    replies = data.get("replies", {})
    if text in replies and replies[text]:
        return random.choice(replies[text])
    else:
        fallback = ["عه 😅", "باشه", "درسته", "جالبه 😎", "نمی‌دونم والا"]
        return random.choice(fallback)


# ======================== ⚙️ مود و آمار =========================
def get_mode():
    data = load_data(MAIN_MEMORY)
    return data.get("mode", "نرمال")


def set_mode(mode):
    data = load_data(MAIN_MEMORY)
    data["mode"] = mode
    save_data(MAIN_MEMORY, data)


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


# ======================== ✨ بهبود پاسخ =========================
def enhance_sentence(sentence):
    """افزودن کمی حالت طبیعی‌تر به پاسخ‌ها"""
    endings = [" 😊", " 😎", " 😂", " 😅", " ❤️"]
    if sentence and not sentence.endswith(tuple(endings)):
        sentence += random.choice(endings)
    return sentence
