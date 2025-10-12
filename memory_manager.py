import json
import os
import random

MEMORY_FILE = "memory.json"
SHADOW_FILE = "shadow_memory.json"
GROUP_FILE = "group_data.json"


def init_files():
    """ساخت فایل‌ها در صورت نبودن"""
    for file, default in [
        (MEMORY_FILE, {"data": {}, "users": [], "mode": "نرمال"}),
        (SHADOW_FILE, {"data": {}}),
        (GROUP_FILE, {}),
    ]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False, indent=2)


def load_data(filename):
    """لود داده با ترمیم خودکار"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            # ✅ بررسی و ترمیم ساختار
            if filename == MEMORY_FILE and "data" not in data:
                data = {"data": {}, "users": [], "mode": "نرمال"}
                save_data(filename, data)
            elif filename == SHADOW_FILE and "data" not in data:
                data = {"data": {}}
                save_data(filename, data)
            elif filename == GROUP_FILE and not isinstance(data, dict):
                data = {}
                save_data(filename, data)
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"⚠️ فایل خراب بود ({filename}) → بازسازی شد.")
        if filename == MEMORY_FILE:
            base = {"data": {}, "users": [], "mode": "نرمال"}
        elif filename == SHADOW_FILE:
            base = {"data": {}}
        else:
            base = {}
        save_data(filename, base)
        return base


def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def learn(phrase, response):
    memory = load_data(MEMORY_FILE)
    phrase, response = phrase.strip().lower(), response.strip()
    memory["data"].setdefault(phrase, [])
    if response not in memory["data"][phrase]:
        memory["data"][phrase].append(response)
    save_data(MEMORY_FILE, memory)


def shadow_learn(phrase, response):
    shadow = load_data(SHADOW_FILE)
    phrase, response = phrase.strip().lower(), response.strip()
    shadow["data"].setdefault(phrase, [])
    if response and response not in shadow["data"][phrase]:
        shadow["data"][phrase].append(response)
    save_data(SHADOW_FILE, shadow)


def merge_shadow_memory():
    shadow, memory = load_data(SHADOW_FILE), load_data(MEMORY_FILE)
    for phrase, responses in shadow["data"].items():
        memory["data"].setdefault(phrase, [])
        for r in responses:
            if r not in memory["data"][phrase]:
                memory["data"][phrase].append(r)
    save_data(MEMORY_FILE, memory)
    save_data(SHADOW_FILE, {"data": {}})


def get_reply(text):
    memory = load_data(MEMORY_FILE)
    if "data" not in memory:  # ترمیم در لحظه
        memory = {"data": {}, "users": [], "mode": "نرمال"}
        save_data(MEMORY_FILE, memory)

    text = text.strip().lower()

    if text in memory["data"] and memory["data"][text]:
        return random.choice(memory["data"][text])

    matches = [p for p in memory["data"].keys() if p in text]
    if matches:
        key = random.choice(matches)
        return random.choice(memory["data"][key])

    return random.choice([
        "نمیدونم چی بگم 🤔",
        "بیشتر توضیح بده 😅",
        "جالب شد! ادامه بده 😎",
        "چی گفتی؟ یه بار دیگه بگو 😂",
    ])


def get_mode():
    memory = load_data(MEMORY_FILE)
    return memory.get("mode", "نرمال")


def set_mode(mode):
    memory = load_data(MEMORY_FILE)
    memory["mode"] = mode
    save_data(MEMORY_FILE, memory)


def enhance_sentence(sentence):
    mode = get_mode()
    if mode == "شوخ":
        return f"{sentence} 😄"
    elif mode == "بی‌ادب":
        return f"{sentence} 😏"
    elif mode == "غمگین":
        return f"{sentence} 😔"
    else:
        return sentence


def get_stats():
    memory = load_data(MEMORY_FILE)
    phrases = len(memory.get("data", {}))
    responses = sum(len(v) for v in memory.get("data", {}).values())
    mode = memory.get("mode", "نرمال")
    return {"phrases": phrases, "responses": responses, "mode": mode}
