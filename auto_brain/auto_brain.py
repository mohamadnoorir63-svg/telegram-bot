
import asyncio
import json
import os
import random
from datetime import datetime

from memory_manager import (
    load_data, save_data, clean_memory, generate_sentence
)

# 🧠 تنظیمات اصلی
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
BRAIN_STATS_FILE = "auto_brain/brain_stats.json"

# ========================= ⚙️ تابع کمکی =========================
def load_stats():
    """خواندن آمار قبلی رشد مغز"""
    if not os.path.exists(BRAIN_STATS_FILE):
        return {"phrases": 0, "responses": 0, "runs": 0, "last_update": ""}
    with open(BRAIN_STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_stats(stats):
    """ذخیره آمار رشد"""
    with open(BRAIN_STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


# ========================= 🧩 ادغام حافظه سایه با اصلی =========================
def merge_shadow_memory():
    """ادغام داده‌های shadow_memory.json با memory.json"""
    main = load_data("memory.json")
    shadow = load_data("shadow_memory.json")

    main_data = main.get("data", {})
    shadow_data = shadow.get("data", {})

    merged_phrases = 0
    added_responses = 0

    for phrase, responses in shadow_data.items():
        if phrase not in main_data:
            main_data[phrase] = [{"text": r, "weight": 1} for r in responses]
            merged_phrases += 1
        else:
            existing_texts = [r["text"] if isinstance(r, dict) else r for r in main_data[phrase]]
            for r in responses:
                if r not in existing_texts:
                    main_data[phrase].append({"text": r, "weight": 1})
                    added_responses += 1

    if merged_phrases or added_responses:
        main["data"] = main_data
        save_data("memory.json", main)

        # پاک کردن سایه بعد از ادغام
        shadow["data"] = {}
        save_data("shadow_memory.json", shadow)

    return merged_phrases, added_responses


# ========================= 🧠 رشد هوش و تحلیل حافظه =========================
async def analyze_and_grow(bot=None):
    """تحلیل و رشد هوش خنگول"""
    # آمار قبلی
    prev_stats = load_stats()
    before = {
        "phrases": prev_stats.get("phrases", 0),
        "responses": prev_stats.get("responses", 0)
    }

    # ✳️ ادغام حافظه‌ها
    merged_phrases, added_responses = merge_shadow_memory()

    # ✳️ تمیز کردن حافظه
    cleaned = clean_memory()

    # ✳️ خواندن آمار فعلی
    from memory_manager import get_stats
    current = get_stats()

    # ✳️ ساخت چند جمله خلاق و ذخیره در shadow برای آینده
    creative = []
    for _ in range(random.randint(2, 5)):
        s = generate_sentence()
        creative.append(s)

    shadow = load_data("shadow_memory.json")
    for text in creative:
        shadow["data"][f"✨ {text}"] = ["💡 جمله‌ی ساخته‌شده توسط هوش خودکار"]
    save_data("shadow_memory.json", shadow)

    # ✳️ محاسبه رشد
    diff_phrases = current["phrases"] - before["phrases"]
    diff_responses = current["responses"] - before["responses"]
    growth = diff_phrases + diff_responses

    # ✳️ ذخیره آمار جدید
    stats = {
        "phrases": current["phrases"],
        "responses": current["responses"],
        "runs": prev_stats.get("runs", 0) + 1,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_stats(stats)

    # ✳️ ساخت گزارش
    report = (
        f"🤖 گزارش رشد هوش خودکار خنگول:\n\n"
        f"🧩 جملات جدید ادغام‌شده: {merged_phrases}\n"
        f"💬 پاسخ‌های جدید از سایه: {added_responses}\n"
        f"🧹 حافظه تمیز شد: {cleaned} مورد\n"
        f"✨ جملات خلاق ساخته‌شده: {len(creative)}\n\n"
        f"📊 رشد کلی از آخرین اجرا:\n"
        f"📈 جملات: {before['phrases']} → {current['phrases']} (+{diff_phrases})\n"
        f"💭 پاسخ‌ها: {before['responses']} → {current['responses']} (+{diff_responses})\n\n"
        f"🕓 آخرین بروزرسانی: {stats['last_update']}"
    )

    print(report)

    if bot:
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=report)
        except Exception as e:
            print(f"[Brain Report Error] {e}")


# ========================= 🔁 حلقه خودکار رشد =========================
async def start_auto_brain_loop(bot):
    """اجرای خودکار هوش خنگول هر ۶ ساعت"""
    while True:
        await analyze_and_grow(bot)
        await asyncio.sleep(6 * 60 * 60)  # هر ۶ ساعت
