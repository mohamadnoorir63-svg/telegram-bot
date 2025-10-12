import json
import os
import random

# مسیر فایل‌ها
MEMORY_FILE = "memory.json"
SHADOW_FILE = "shadow_memory.json"
GROUP_FILE = "group_data.json"


# ==================== 🔧 راه‌اندازی فایل‌ها ====================

def init_files():
    for file in [MEMORY_FILE, SHADOW_FILE, GROUP_FILE]:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)


def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 🧠 یادگیری و حافظه ====================

def learn(phrase, response):
    data = load_data(MEMORY_FILE)
    phrase = phrase.strip().lower()
    response = response.strip()

    if phrase not in data:
        data[phrase] = []
    if response not in data[phrase]:
        data[phrase].append(response)

    save_data(MEMORY_FILE, data)


def shadow_learn(phrase, response):
    data = load_data(SHADOW_FILE)
    phrase = phrase.strip().lower()
    response = response.strip()

    if phrase not in data:
        data[phrase] = []
    if response and response not in data[phrase]:
        data[phrase].append(response)

    save_data(SHADOW_FILE, data)


def merge_shadow_memory():
    memory = load_data(MEMORY_FILE)
    shadow = load_data(SHADOW_FILE)
    for phrase, responses in shadow.items():
        if phrase not in memory:
            memory[phrase] = responses
        else:
            for r in responses:
                if r not in memory[phrase]:
                    memory[phrase].append(r)
    save_data(MEMORY_FILE, memory)
    save_data(SHADOW_FILE, {})


# ==================== 🤖 پاسخ‌دهی ====================

def get_reply(text):
    text = text.strip().lower()
    data = load_data(MEMORY_FILE)
    if text in data and data[text]:
        return random.choice(data[text])
    else:
        return random.choice([
            "نمیدونم چی بگم 😅",
            "جالب گفتی ولی یادم نیست 😜",
            "بگو یادبگیر تا یادم بمونه 🤔",
        ])


# ==================== 🎭 مودها ====================

MODE_FILE = "mode.json"

def get_mode():
    if not os.path.exists(MODE_FILE):
        return "نرمال"
    with open(MODE_FILE, "r", encoding="utf-8") as f:
        return f.read().strip() or "نرمال"


def set_mode(mode):
    with open(MODE_FILE, "w", encoding="utf-8") as f:
        f.write(mode)


# ==================== 🧮 آمار ====================

def get_stats():
    data = load_data(MEMORY_FILE)
    phrases = len(data)
    responses = sum(len(r) for r in data.values())
    return {"phrases": phrases, "responses": responses, "mode": get_mode()}


# ==================== ✨ زیباتر کردن پاسخ ====================

def enhance_sentence(sentence):
    if not sentence:
        return "😶 حرفی ندارم بزنم!"
    endings = ["😂", "😜", "😎", "😉", "😅", "🙂"]
    if sentence[-1] not in "!?.":
        sentence += random.choice(["!", "؟", "."])
    if random.random() > 0.5:
        sentence += " " + random.choice(endings)
    return sentence
