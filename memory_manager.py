import json
import os

MEMORY_FILE = "memory.json"
SHADOW_FILE = "shadow_memory.json"

def init_files():
    """اگر فایل‌های حافظه وجود نداشتن، بسازشون"""
    if not os.path.exists(MEMORY_FILE):
        save_memory({"replies": {}, "learning": True, "mode": "normal"})
    if not os.path.exists(SHADOW_FILE):
        save_shadow({"hidden": {}})

def load_memory():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ✅ این تابع برای سازگاری با bot.py اضافه شد
def load_data():
    return load_memory()

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_shadow():
    with open(SHADOW_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_shadow(data):
    with open(SHADOW_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def merge_shadow_to_memory():
    """وقتی یادگیری دوباره فعال شد، داده‌های پنهان اضافه میشن"""
    memory = load_memory()
    shadow = load_shadow()
    if "hidden" in shadow:
        for k, v in shadow["hidden"].items():
            if k not in memory["replies"]:
                memory["replies"][k] = v
            else:
                memory["replies"][k].extend(v)
        shadow["hidden"] = {}
        save_shadow(shadow)
        save_memory(memory)
