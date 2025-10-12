import re
from memory_manager import learn, load_data, save_data

# 🧠 یادگیری خودکار بر اساس الگوی ساده جمله‌ها
def auto_learn_from_text(text: str):
    """یادگیری خودکار از ساختار جمله‌های کاربران"""
    if not text or len(text) < 4:
        return

    memory = load_data("memory.json")
    data = memory.get("data", {})

    # الگوهای ساده برای پرسش/پاسخ
    questions = ["?", "چطوری", "کجایی", "چیکار می‌کنی", "اسمت چیه"]
    answers = ["خوبم", "اینجام", "در حال خدمت 🤖", "اسمم خنگوله 😅"]

    for q, a in zip(questions, answers):
        if q in text:
            if q not in data:
                learn(q, a)
            else:
                if a not in data[q]:
                    data[q].append(a)
                    save_data("memory.json", memory)
            break

# ✨ نسخه‌ی جدید دارای auto-clean برای جلوگیری از تکرار زیاد
def clean_duplicates():
    mem = load_data("memory.json")
    if not mem.get("data"):
        return
    changed = False
    for k, v in mem["data"].items():
        unique = list(set(v))
        if len(unique) != len(v):
            mem["data"][k] = unique
            changed = True
    if changed:
        save_data("memory.json", mem)
