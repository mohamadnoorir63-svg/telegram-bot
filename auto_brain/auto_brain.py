# auto_brain.py
import asyncio
import json
import os
import random
from datetime import datetime

from memory_manager import (
    load_data, save_data, generate_sentence, evaluate_intelligence,
    reinforce_learning, get_stats
)
from ai_learning import clean_duplicates, auto_learn_from_text
from fix_memory import fix_json

ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
BRAIN_STATS_FILE = "auto_brain/brain_stats.json"


# ------------------------------
# 📊 آمار
# ------------------------------
def load_stats():
    if not os.path.exists(BRAIN_STATS_FILE):
        return {"phrases": 0, "responses": 0, "runs": 0, "last_update": ""}
    try:
        with open(BRAIN_STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"phrases": 0, "responses": 0, "runs": 0, "last_update": ""}


def save_stats(stats):
    try:
        with open(BRAIN_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[AutoBrain] خطا در ذخیره آمار: {e}")


# ------------------------------
# 🛠 تعمیر فایل‌های حافظه
# ------------------------------
def ensure_memory_files():
    for file in ["memory.json", "shadow_memory.json"]:
        fix_json(file)


# ------------------------------
# 🔁 ادغام حافظه سایه
# ------------------------------
def merge_shadow_memory():
    main = load_data("memory.json")
    shadow = load_data("shadow_memory.json")

    main_data = main.get("data", {})
    shadow_data = shadow.get("data", {})

    merged_phrases = 0
    added_responses = 0

    for phrase, responses in shadow_data.items():

        new_responses = []
        for r in responses:
            if isinstance(r, str):
                new_responses.append({"text": r, "weight": 1})
            elif isinstance(r, dict) and "text" in r:
                new_responses.append({"text": r["text"], "weight": r.get("weight", 1)})

        if phrase not in main_data:
            main_data[phrase] = new_responses
            merged_phrases += 1
        else:
            existing = [x["text"] for x in main_data[phrase]]
            for r in new_responses:
                if r["text"] not in existing:
                    main_data[phrase].append(r)
                    added_responses += 1

    if merged_phrases or added_responses:
        main["data"] = main_data
        save_data("memory.json", main)

        shadow["data"] = {}
        save_data("shadow_memory.json", shadow)

    return merged_phrases, added_responses


# ------------------------------
# 🧠 عملیات اصلی رشد هوش
# ------------------------------
async def analyze_and_grow(bot=None):

    ensure_memory_files()

    prev_stats = load_stats()
    before = {
        "phrases": prev_stats.get("phrases", 0),
        "responses": prev_stats.get("responses", 0)
    }

    # → ادغام حافظه سایه
    merged_phrases, added_responses = merge_shadow_memory()

    # → پاکسازی
    try:
        clean_duplicates()
    except Exception as e:
        print(f"[AutoBrain] Clean failed: {e}")

    # → تقویت یادگیری
    try:
        reinforce_data = reinforce_learning(verbose=False)
    except Exception as e:
        print(f"[AutoBrain] Reinforce failed: {e}")
        reinforce_data = {"strengthened": 0, "removed": 0}

    # → آمار جدید
    current = get_stats()

    # → جمله‌سازی خلاق
    creative = []
    for _ in range(random.randint(2, 5)):
        s = generate_sentence()
        creative.append(s)
        try:
            auto_learn_from_text(s)
        except Exception:
            pass

    # ذخیره در حافظه سایه
    shadow = load_data("shadow_memory.json")
    for text in creative:
        shadow["data"][f"✨ {text}"] = ["💡 جمله‌ی ساخته‌شده توسط هوش خودکار"]
    save_data("shadow_memory.json", shadow)

    # → ارزیابی هوش
    try:
        aiq = evaluate_intelligence()
    except Exception as e:
        aiq = {"iq": 0, "level": "❌ خطا", "summary": str(e)}

    # → ذخیره آمار
    stats = {
        "phrases": current["phrases"],
        "responses": current["responses"],
        "runs": prev_stats.get("runs", 0) + 1,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_stats(stats)

    # → گزارش نهایی
    report = (
        f"🤖 <b>گزارش رشد هوش خودکار</b>\n"
        f"🧩 ادغام‌شده: <b>{merged_phrases}</b>\n"
        f"💬 پاسخ‌های جدید: <b>{added_responses}</b>\n"
        f"✨ خلاقیت‌ها: <b>{len(creative)}</b>\n\n"
        f"📈 جملات: {before['phrases']} → {stats['phrases']}\n"
        f"💭 پاسخ‌ها: {before['responses']} → {stats['responses']}\n\n"
        f"🧠 IQ: <b>{aiq['iq']}</b>\n"
        f"🌟 سطح: {aiq['level']}\n"
        f"{aiq['summary']}\n\n"
        f"🕓 زمان: {stats['last_update']}\n"
        f"🔁 اجراها: <b>{stats['runs']}</b>"
    )

    print(report)

    # =====================
    # 🛡 ارسال پیام فقط اگر:
    # 1) bot وجود دارد
    # 2) ادمین آنرا استارت کرده
    # =====================
    if bot:
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=report,
                parse_mode="HTML",
                disable_notification=True
            )
        except Exception as e:
            print(f"[Brain Report Error] {e}")


# ------------------------------
# 🔁 حلقه ۶ ساعته
# ------------------------------
async def start_auto_brain_loop(bot):
    while True:
        try:
            await analyze_and_grow(bot)
        except Exception as e:
            print(f"[AutoBrain Loop Error] {e}")
        await asyncio.sleep(6 * 60 * 60)
