import json
import os
import random

# ==================== 🧩 تنظیم مسیر فایل‌ها ====================

MEMORY_FILE = "memory.json"
SHADOW_FILE = "shadow_memory.json"
GROUP_FILE = "group_data.json"


# ==================== 🧠 توابع پایه ====================

def init_files():
    """اگر فایل‌ها وجود نداشتن، می‌سازد"""
    for file, default in [
        (MEMORY_FILE, {"data": {}, "users": []}),
        (SHADOW_FILE, {"data": {}}),
        (GROUP_FILE, {}),
    ]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False, indent=2)


def load_data(filename):
    """لود داده از فایل (اگر خراب بود، بازسازی می‌کند)"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"⚠️ فایل خراب بود ({filename}) → بازسازی شد.")
        base = {"data": {}, "users": []} if "memory" in filename else {}
        save_data(filename, base)
        return base


def save_data(filename, data):
    """ذخیره داده در فایل JSON"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 💬 یادگیری و پاسخ ====================

def learn(phrase, response):
    """یادگیری جمله و پاسخ"""
    memory = load_data(MEMORY_FILE)
    phrase = phrase.strip().lower()
    response = response.strip()

    if phrase not in memory["data"]:
        memory["data"][phrase] = []

    if response not in memory["data"][phrase]:
        memory["data"][phrase].append(response)

    save_data(MEMORY_FILE, memory)


def shadow_learn(phrase, response):
    """یادگیری در حالت خاموش (shadow)"""
    shadow = load_data(SHADOW_FILE)
    phrase = phrase.strip().lower()
    response = response.strip()

    if phrase not in shadow["data"]:
        shadow["data"][phrase] = []

    if response and response not in shadow["data"][phrase]:
        shadow["data"][phrase].append(response)

    save_data(SHADOW_FILE, shadow)


def merge_shadow_memory():
    """ادغام حافظه سایه با حافظه اصلی"""
    shadow = load_data(SHADOW_FILE)
    memory = load_data(MEMORY_FILE)

    for phrase, responses in shadow["data"].items():
        if phrase not in memory["data"]:
            memory["data"][phrase] = responses
        else:
            for r in responses:
                if r not in memory["data"][phrase]:
                    memory["data"][phrase].append(r)

    save_data(MEMORY_FILE, memory)
    save_data(SHADOW_FILE, {"data": {}})


def get_reply(text):
    """دریافت پاسخ از حافظه"""
    memory = load_data(MEMORY_FILE)
    text = text.strip().lower()

    if text in memory["data"] and memory["data"][text]:
        return random.choice(memory["data"][text])

    # جستجوی تطبیقی
    matches = [p for p in memory["data"].keys() if p in text]
    if matches:
        key = random.choice(matches)
        return random.choice(memory["data"][key])

    # اگر چیزی پیدا نشد
    return random.choice([
        "نمیدونم چی بگم 🤔",
        "بیشتر توضیح بده 😅",
        "جالب شد! ادامه بده 😎",
        "چی گفتی؟ یه بار دیگه بگو 😂",
    ])


# ==================== 🎭 مود و لحن پاسخ ====================

def get_mode():
    memory = load_data(MEMORY_FILE)
    return memory.get("mode", "نرمال")


def set_mode(mode):
    memory = load_data(MEMORY_FILE)
    memory["mode"] = mode
    save_data(MEMORY_FILE, memory)


def enhance_sentence(sentence):
    """بهبود جمله بر اساس مود"""
    mode = get_mode()

    if mode == "شوخ":
        return f"{sentence} 😄"
    elif mode == "بی‌ادب":
        return f"{sentence} 😏"
    elif mode == "غمگین":
        return f"{sentence} 😔"
    else:
        return sentence


# ==================== 📊 آمار ====================

def get_stats():
    memory = load_data(MEMORY_FILE)
    phrases = len(memory.get("data", {}))
    responses = sum(len(v) for v in memory.get("data", {}).values())
    mode = memory.get("mode", "نرمال")
    return {"phrases": phrases, "responses": responses, "mode": mode}
