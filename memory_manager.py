import json
import os
import random

# 🧩 فایل‌های حافظه
FILES = ["memory.json", "group_data.json", "stickers.json"]

# ================== 📦 مدیریت فایل‌ها ==================

def init_files():
    for file in FILES:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                if "memory" in file:
                    json.dump({"data": {}, "users": []}, f, ensure_ascii=False, indent=2)
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

# ================== 🧠 یادگیری ==================

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
    """یادگیری پنهان، بدون پاسخ مستقیم"""
    memory = load_data("memory.json")
    if "shadow" not in memory:
        memory["shadow"] = []
    memory["shadow"].append((phrase, response))
    save_data("memory.json", memory)

def merge_shadow_memory():
    """ادغام داده‌های پنهان با حافظه اصلی"""
    memory = load_data("memory.json")
    if "shadow" in memory:
        for p, r in memory["shadow"]:
            learn(p, r)
        memory["shadow"] = []
        save_data("memory.json", memory)

# ================== 💬 پاسخ‌دهی ==================

def get_reply(text):
    memory = load_data("memory.json")
    if "data" not in memory:
        memory["data"] = {}

    # اگر جمله یاد گرفته شده باشه:
    if text in memory["data"] and memory["data"][text]:
        return random.choice(memory["data"][text])

    # اگر نه، جمله‌ای مشابه پیدا کنه
    for key in memory["data"].keys():
        if key in text or text in key:
            return random.choice(memory["data"][key])

    # اگر هیچ پاسخی پیدا نکرد، خودش جمله می‌سازه
    return generate_sentence()

# ================== 💡 جمله‌سازی هوشمند ==================

def generate_sentence():
    """ساخت جمله جدید از یادگرفته‌ها"""
    memory = load_data("memory.json")
    if "data" not in memory or not memory["data"]:
        return random.choice([
            "من هنوز چیزی یاد نگرفتم 😅",
            "بیا یه چیزی یادم بده!",
            "هیچی یادم نیست فعلاً 🤔"
        ])

    words = []
    for key, responses in memory["data"].items():
        parts = key.split()
        if len(parts) > 0:
            words.append(random.choice(parts))
        if responses:
            words.append(random.choice(responses).split()[0])

    sentence = " ".join(random.sample(words, min(len(words), 8)))
    return enhance_sentence(sentence)


# ================== 🎭 مودها و استایل پاسخ ==================

def get_mode():
    data = load_data("memory.json")
    return data.get("mode", "نرمال")

def set_mode(mode):
    data = load_data("memory.json")
    data["mode"] = mode
    save_data("memory.json", data)

def enhance_sentence(sentence):
    """زیباسازی جمله و افزودن حس مود"""
    mode = get_mode()
    if mode == "شوخ":
        endings = ["😂", "😜", "😎", "🤣"]
    elif mode == "غمگین":
        endings = ["😔", "🥀", "😢"]
    elif mode == "بی‌ادب":
        endings = ["😏", "😈", "🙃"]
    else:
        endings = ["🙂", "😄", "😉"]

    if not sentence.endswith(tuple(endings)):
        sentence += " " + random.choice(endings)
    return sentence


# ================== 📊 آمار ==================

def get_stats():
    memory = load_data("memory.json")
    data = memory.get("data", {})
    return {
        "phrases": len(data),
        "responses": sum(len(v) for v in data.values()),
        "mode": memory.get("mode", "نرمال")
    }
