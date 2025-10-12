import asyncio
import os
import random
import zipfile
from datetime import datetime, timedelta
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# 📦 ماژول‌ها
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    merge_shadow_memory, get_reply, set_mode, get_stats,
    enhance_sentence, generate_sentence
)
from jokes_manager import save_joke, list_jokes
from fortune_manager import save_fortune, list_fortunes

# 🎯 تنظیمات پایه
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754
init_files()

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "last_joke": datetime.now()
}

# ======================= ✳️ دستورات پایه =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.0 فول پلاس آماده‌ست!\n"
        "برای دیدن دستورات بنویس: راهنما 📘"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📘 *راهنمای خنگول 8.0*\n\n"
        "🧠 یادگیری و پاسخ:\n"
        "▪️ `یادبگیر جمله` سپس در خطوط بعدی پاسخ‌ها رو بنویس\n"
        "▪️ `لیست` → نمایش جملات یادگرفته‌شده\n"
        "▪️ `جمله بساز` → ساخت جمله تصادفی\n\n"
        "😂 جوک و فال:\n"
        "▪️ ریپلی روی عکس یا متن بزن و بنویس: `ثبت جوک`\n"
        "▪️ ریپلی روی عکس یا متن بزن و بنویس: `ثبت فال`\n"
        "▪️ لیست جوک‌ها → نمایش جوک‌های ذخیره‌شده\n"
        "▪️ لیست فال‌ها → نمایش فال‌های ذخیره‌شده\n\n"
        "⚙️ مدیریت:\n"
        "▪️ /toggle → روشن/خاموش کردن ربات\n"
        "▪️ /mode شوخ/بی‌ادب/نرمال/غمگین → تغییر مود\n"
        "▪️ /stats → نمایش آمار\n"
        "▪️ /backup → پشتیبان‌گیری کامل\n"
        "▪️ /restore → بازیابی همه فایل‌ها\n"
        "▪️ /broadcast متن → ارسال همگانی\n"
        "▪️ /leave → خروج از گروه\n\n"
        "👋 خوشامد:\n"
        "▪️ /welcome → روشن/خاموش کردن خوشامد\n\n"
        "😄 ربات خودش مود، احساس و شوخی‌ها رو تشخیص می‌ده!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ======================= 🎭 مود و وضعیت =======================

async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("🎭 دستور استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")
    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")

async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    await update.message.reply_text("✅ ربات فعال شد!" if status["active"] else "💤 ربات خاموش شد!")

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!")

# ======================= 📊 آمار =======================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    msg = (
        f"📊 آمار خنگول:\n"
        f"• جملات: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
    )
    await update.message.reply_text(msg)

# ======================= 💬 پاسخ و یادگیری =======================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()

    # ثبت کاربر برای ارسال همگانی
    data = load_data("memory.json")
    uid = update.effective_user.id
    if "users" not in data:
        data["users"] = []
    if uid not in data["users"]:
        data["users"].append(uid)
        save_data("memory.json", data)

    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return

    # یادگیری دستی
    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            memory = load_data("memory.json")
            known_resps = set(memory.get("data", {}).get(phrase, []))
            new_resps = [r for r in responses if r not in known_resps]

            if known_resps:
                for r in new_resps:
                    learn(phrase, r)
                msg = "😏 اینو بلد بودم!"
                if new_resps:
                    msg += f"\n➕ {len(new_resps)} پاسخ جدید اضافه شد."
                else:
                    msg += "\nهیچ پاسخ جدیدی نداشتی."
                await update.message.reply_text(msg)
            else:
                for r in responses:
                    learn(phrase, r)
                await update.message.reply_text(f"🧠 یاد گرفتم {len(responses)} پاسخ برای '{phrase}'!")
        else:
            await update.message.reply_text("❗ بعد از 'یادبگیر' جمله و پاسخ‌هاش رو با خط جدید بنویس.")
        return

    # لیست جملات
    if text == "لیست":
        phrases = list(load_data("memory.json").get("data", {}).keys())
        if phrases:
            await update.message.reply_text("🧾 جملات یادگرفته‌شده:\n" + "\n".join(phrases[:30]))
        else:
            await update.message.reply_text("هنوز چیزی یاد نگرفتم 😅")
        return

    # جوک و فال
    if text.lower() == "ثبت جوک" and update.message.reply_to_message:
        await save_joke(update)
        return
    if text.lower() == "ثبت فال" and update.message.reply_to_message:
        await save_fortune(update)
        return
    if text == "لیست جوک‌ها":
        await list_jokes(update)
        return
    if text == "لیست فال‌ها":
        await list_fortunes(update)
        return

    # جمله تصادفی
    if text == "جمله بساز":
        await update.message.reply_text(generate_sentence())
        return

    reply_text = get_reply(text)
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)

# ======================= 💾 بک‌آپ و بازیابی =======================

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip"
    with zipfile.ZipFile(filename, "w") as zipf:
        for file in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json"]:
            if os.path.exists(file):
                zipf.write(file)
    await update.message.reply_document(document=open(filename, "rb"), filename=filename)
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")
    os.remove(filename)

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را بفرست تا بازیابی شود.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_restore"):
        return
    file = await update.message.document.get_file()
    await file.download_to_drive("restore.zip")

    with zipfile.ZipFile("restore.zip", "r") as zip_ref:
        zip_ref.extractall(".")
    os.remove("restore.zip")

    await update.message.reply_text("✅ بازیابی کامل انجام شد!")
    context.user_data["await_restore"] = False

# ======================= 🚀 اجرای ربات =======================

if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.0 فول پلاس آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling(allowed_updates=Update.ALL_TYPES)
