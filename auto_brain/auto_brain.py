import asyncio
import json
import os
import random
from datetime import datetime

from memory_manager import (
    load_data, save_data, generate_sentence, evaluate_intelligence, reinforce_learning
)
from ai_learning import clean_duplicates  # 🧹 پاکسازی هوشمند حافظه
from ai_learning import auto_learn_from_text  # 🧠 هماهنگی کامل یادگیری لحظه‌ای

ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
BRAIN_STATS_FILE = "auto_brain/brain_stats.json"

# ===============================================================
# 📊 بارگذاری و ذخیره آمار رشد مغز خودکار
# ===============================================================
def load_stats():
    if not os.path.exists(BRAIN_STATS_FILE):
        return {"phrases": 0, "responses": 0, "runs": 0, "last_update": ""}
    with open(BRAIN_STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_stats(stats):
    with open(BRAIN_STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


# ===============================================================
# 🔁 ادغام حافظه سایه با حافظه اصلی
# ===============================================================
def merge_shadow_memory():
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
        shadow["data"] = {}
        save_data("shadow_memory.json", shadow)

    return merged_phrases, added_responses


# ===============================================================
# 🧠 تحلیل و رشد خودکار هوش خنگول
# ===============================================================
async def analyze_and_grow(bot=None):
    prev_stats = load_stats()
    before = {
        "phrases": prev_stats.get("phrases", 0),
        "responses": prev_stats.get("responses", 0)
    }

    # 🔁 ادغام داده‌های سایه
    merged_phrases, added_responses = merge_shadow_memory()

    # 🧹 پاک‌سازی هوشمند حافظه از تکراری‌ها
    try:
        clean_duplicates()
    except Exception as e:
        print(f"[AutoBrain] Clean failed: {e}")

    # 🌱 تقویت حافظه پاسخ‌های مفید
    reinforce_data = {"strengthened": 0, "removed": 0}
    try:
        reinforce_data = reinforce_learning(verbose=False)
    except Exception as e:
        print(f"[AutoBrain] Reinforce failed: {e}")

    # 📈 بروزرسانی آمار فعلی
    from memory_manager import get_stats
    current = get_stats()

    # ✨ ساخت جملات خلاق جدید
    creative = []
    for _ in range(random.randint(2, 5)):
        s = generate_sentence()
        creative.append(s)
        try:
            auto_learn_from_text(s)
        except Exception as e:
            print(f"[AutoBrain] Learn from creative failed: {e}")

    # 📦 افزودن جملات خلاق به حافظه سایه برای رشد بعدی
    shadow = load_data("shadow_memory.json")
    for text in creative:
        shadow["data"][f"✨ {text}"] = ["💡 جمله‌ی ساخته‌شده توسط هوش خودکار"]
    save_data("shadow_memory.json", shadow)

    diff_phrases = current["phrases"] - before["phrases"]
    diff_responses = current["responses"] - before["responses"]

    # 🧩 ارزیابی هوش خودکار (AI IQ)
    try:
        aiq = evaluate_intelligence()
    except Exception as e:
        aiq = {"iq": 0, "level": "❌ خطا در تحلیل هوش", "summary": str(e)}

    # 🧾 ذخیره وضعیت رشد جدید
    stats = {
        "phrases": current["phrases"],
        "responses": current["responses"],
        "runs": prev_stats.get("runs", 0) + 1,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_stats(stats)

    # 💬 گزارش تحلیلی رشد مغز
    report = (
        f"🤖 <b>گزارش رشد هوش خودکار خنگول</b>\n\n"
        f"🧩 جملات جدید ادغام‌شده: <b>{merged_phrases}</b>\n"
        f"💬 پاسخ‌های تازه از حافظه سایه: <b>{added_responses}</b>\n"
        f"✨ جملات خلاق تولید‌شده: <b>{len(creative)}</b>\n"
        f"🧠 پاسخ‌های تقویت‌شده: <b>{reinforce_data['strengthened']}</b>\n"
        f"🗑 پاسخ‌های حذف‌شده: <b>{reinforce_data['removed']}</b>\n\n"
        f"📈 جملات: {before['phrases']} → {current['phrases']} (+{diff_phrases})\n"
        f"💭 پاسخ‌ها: {before['responses']} → {current['responses']} (+{diff_responses})\n\n"
        f"🤯 <b>نمره هوش خودکار:</b> <code>{aiq['iq']}</code>\n"
        f"🌟 <b>سطح:</b> {aiq['level']}\n"
        f"{aiq['summary']}\n\n"
        f"🕓 آخرین بروزرسانی: <code>{stats['last_update']}</code>\n"
        f"🔁 دفعات اجرای خودکار: <b>{stats['runs']}</b>\n"
        f"⚙️ نسخه: <i>AutoBrain+ EmotionSync v3.5</i>"
    )

    print(report)

    # 📤 ارسال گزارش برای ادمین
    if bot:
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=report, parse_mode="HTML")
        except Exception as e:
            print(f"[Brain Report Error] {e}")


# ===============================================================
# 🔄 لوپ اصلی رشد خودکار مغز — هر ۶ ساعت یکبار
# ===============================================================
async def start_auto_brain_loop(bot):
    while True:
        try:
            await analyze_and_grow(bot)
        except Exception as e:
            print(f"[AutoBrain Loop Error] {e}")
        await asyncio.sleep(6 * 60 * 60)
