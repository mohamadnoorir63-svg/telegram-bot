import json
import os
import random

# ================== 📂 مدیریت فایل‌ها ==================

def init_files():
    for file in ["memory.json", "group_data.json", "stickers.json"]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                if "memory" in file:
                    json.dump({"data": {}, "users": [], "mode": "نرمال"}, f, ensure_ascii=False, indent=2)
                else:
                    json.dump({}, f, ensure_ascii=False, indent=2)


def load_data(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================== 🧠 یادگیری و پاسخ ==================

def learn(phrase, response):
    memory = load_data("memory.json")
    if "data" not in memory:
        memory["data"] = {}
    if phrase not in memory["data"]:
        memory["data"][phrase] = []
    if response not in memory["data"][phrase]:
        memory["data"][phrase].append(response)
        save_data("memory.json", memory)


def shadow_learn(phrase, response):
    """یادگیری پنهان در حالت غیرفعال"""
    if not phrase.strip():
        return
    memory = load_data("memory_shadow.json") if os.path.exists("memory_shadow.json") else {"data": {}}
    if phrase not in memory["data"]:
        memory["data"][phrase] = []
    if response and response not in memory["data"][phrase]:
        memory["data"][phrase].append(response)
    save_data("memory_shadow.json", memory)


def merge_shadow_memory():
    """ادغام یادگیری پنهان در حافظه اصلی"""
    if not os.path.exists("memory_shadow.json"):
        return
    main = load_data("memory.json")
    shadow = load_data("memory_shadow.json")
    for phrase, responses in shadow.get("data", {}).items():
        if phrase not in main["data"]:
            main["data"][phrase] = responses
        else:
            for r in responses:
                if r not in main["data"][phrase]:
                    main["data"][phrase].append(r)
    save_data("memory.json", main)
    os.remove("memory_shadow.json")


# ================== 💬 پاسخ‌دهی ==================

def get_reply(text):
    memory = load_data("memory.json")
    data = memory.get("data", {})
    if text in data and data[text]:
        return random.choice(data[text])

    # اگر جمله مشابهی پیدا بشه
    for phrase in data.keys():
        if phrase in text or text in phrase:
            return random.choice(data[phrase])

    # پاسخ پیش‌فرض
    return random.choice([
        "نمیدونم 😅",
        "یاد بده تا یاد بگیرم 🤔",
        "جالب بود! ولی هنوز اینو بلد نیستم 😄",
        "بگو یادبگیر تا بفهمم چی میگی 😅"
    ])


def enhance_sentence(sentence):
    """تقویت طبیعی بودن پاسخ‌ها"""
    if not sentence or len(sentence) < 2:
        return sentence
    endings = ["😂", "😅", "😎", "🙂", "🤔", "😏"]
    if not sentence.endswith(tuple(endings)):
        sentence += " " + random.choice(endings)
    return sentence


# ================== 🎭 مودها ==================

def get_mode():
    memory = load_data("memory.json")
    return memory.get("mode", "نرمال")


def set_mode(mode):
    memory = load_data("memory.json")
    memory["mode"] = mode
    save_data("memory.json", memory)


# ================== 📊 آمار ==================

def get_stats():
    memory = load_data("memory.json")
    return {
        "phrases": len(memory.get("data", {})),
        "responses": sum(len(v) for v in memory.get("data", {}).values()),
        "mode": memory.get("mode", "نرمال")
    }


# ================== ✍️ جمله‌سازی تصادفی ==================

def generate_sentence():
    """ترکیب تصادفی کلمات یادگرفته‌شده برای ساخت جمله جدید"""
    memory = load_data("memory.json")
    data = list(memory.get("data", {}).keys())
    if not data:
        return "هنوز چیزی یاد نگرفتم 😅"
    parts = []
    for _ in range(random.randint(3, 7)):
        part = random.choice(data)
        parts.append(part.split()[0] if part else "")
    return " ".join(parts).strip() + random.choice(["!", " 😄", " 🤪", " 🙂"])
