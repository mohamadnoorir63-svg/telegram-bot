import asyncio
import os
import random
import zipfile
import shutil
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import aiofiles
import json

# ======================= ⚙️ تنظیمات پایه =======================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}

# ======================= 📦 فایل‌های داده =======================
ALIAS_FILE = "aliases.json"
REPLY_FILE = "custom_replies.json"

def ensure_file_exists(path, default_data):
    """ایجاد فایل در صورت نبود"""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

def load_json(path):
    ensure_file_exists(path, {})
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🧠 مدیریت Alias =======================
def get_alias(command: str):
    """بررسی وجود دستور مستعار"""
    aliases = load_json(ALIAS_FILE)
    return aliases.get(command.lower())

async def add_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن alias جدید (فقط توسط مدیر)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Only the admin can create aliases!")

    if len(context.args) < 2:
        return await update.message.reply_text("⚙️ Usage: /alias [new_command] [original_command]")

    new_cmd = context.args[0].lower()
    original = context.args[1].lower()
    aliases = load_json(ALIAS_FILE)
    aliases[new_cmd] = original
    save_json(ALIAS_FILE, aliases)

    await update.message.reply_text(f"✅ Alias created: `{new_cmd}` → `{original}`", parse_mode="Markdown")

async def remove_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف alias"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Only the admin can remove aliases!")

    if not context.args:
        return await update.message.reply_text("⚙️ Usage: /unalias [command]")

    cmd = context.args[0].lower()
    aliases = load_json(ALIAS_FILE)
    if cmd in aliases:
        del aliases[cmd]
        save_json(ALIAS_FILE, aliases)
        await update.message.reply_text(f"🗑️ Alias `{cmd}` removed.", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Alias not found!")

# ======================= 💬 مدیریت Reply =======================
async def add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن پاسخ سفارشی با ریپلای"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Only the admin can set replies!")

    if not update.message.reply_to_message or not update.message.text:
        return await update.message.reply_text("❗ Use /reply [trigger] by replying to a message!")

    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await update.message.reply_text("⚙️ Usage: /reply [trigger] (reply on the message you want as answer)")

    trigger = parts[1].strip().lower()
    response = update.message.reply_to_message.text.strip()

    replies = load_json(REPLY_FILE)
    replies[trigger] = response
    save_json(REPLY_FILE, replies)

    await update.message.reply_text(f"✅ Learned reply: `{trigger}` → `{response}`", parse_mode="Markdown")

async def remove_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف پاسخ سفارشی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Only the admin can remove replies!")

    if not context.args:
        return await update.message.reply_text("⚙️ Usage: /unreply [trigger]")

    trigger = context.args[0].lower()
    replies = load_json(REPLY_FILE)
    if trigger in replies:
        del replies[trigger]
        save_json(REPLY_FILE, replies)
        await update.message.reply_text(f"🗑️ Reply `{trigger}` removed.", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Reply not found!")

def get_custom_reply(text: str):
    """بررسی پاسخ سفارشی"""
    replies = load_json(REPLY_FILE)
    return replies.get(text.lower())# ======================= 🧱 مدیریت داده و فایل‌ها =======================

def init_files():
    """ساخت فایل‌های موردنیاز در اولین اجرا"""
    ensure_file_exists("memory.json", {"users": [], "phrases": {}})
    ensure_file_exists("group_data.json", {"groups": {}})
    ensure_file_exists("jokes.json", {})
    ensure_file_exists("fortunes.json", {})
    ensure_file_exists(ALIAS_FILE, {})
    ensure_file_exists(REPLY_FILE, {})

def load_data(path):
    ensure_file_exists(path, {})
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 👤 ثبت کاربران =======================

def register_user(user_id):
    """ثبت خودکار کاربر"""
    data = load_data("memory.json")
    users = data.get("users", [])
    if user_id not in users:
        users.append(user_id)
        data["users"] = users
        save_data("memory.json", data)

# ======================= 👥 فعالیت گروه‌ها =======================

def register_group_activity(group_id, user_id):
    """ثبت فعالیت کاربر در گروه"""
    data = load_data("group_data.json")
    groups = data.get("groups", {})

    if str(group_id) not in groups:
        groups[str(group_id)] = {
            "title": f"Group_{group_id}",
            "members": [],
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    group = groups[str(group_id)]
    if user_id not in group["members"]:
        group["members"].append(user_id)
    group["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    data["groups"] = groups
    save_data("group_data.json", data)

def get_group_stats():
    """دریافت آمار تعاملات کلی گروه‌ها"""
    data = load_data("group_data.json")
    groups = data.get("groups", {})
    active_chats = len(groups)
    total_msgs = sum(len(info.get("members", [])) for info in groups.values())
    return {"active_chats": active_chats, "messages": total_msgs}

# ======================= ☁️ بک‌آپ ابری و محلی =======================

def _should_include_in_backup(path: str) -> bool:
    """تشخیص فایل‌های مهم برای بک‌آپ"""
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp"]
    if any(sd in path for sd in skip_dirs):
        return False
    if path.endswith(".zip"):
        return False
    return path.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

async def cloudsync_internal(bot, reason="Manual Backup"):
    """ساخت و ارسال بک‌آپ ابری برای مدیر"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=arcname)

        with open(filename, "rb") as f:
            await bot.send_document(chat_id=ADMIN_ID, document=f, filename=filename)

        await bot.send_message(chat_id=ADMIN_ID, text=f"☁️ {reason} done successfully ✅")

    except Exception as e:
        await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Cloud Backup error:\n{e}")

    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور بک‌آپ ابری دستی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Only admin can run cloud backup!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بک‌آپ محلی در چت"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    try:
        with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=arcname)
        with open(filename, "rb") as f:
            await update.message.reply_document(document=f, filename=filename)
        await update.message.reply_text("✅ Local backup completed successfully!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error during backup:\n{e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= 🔄 بازیابی بک‌آپ =======================

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درخواست ارسال فایل ZIP برای ریستور"""
    await update.message.reply_text("📂 Send the backup ZIP file to restore.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش فایل ZIP برای بازیابی داده‌ها"""
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ Please send a valid .ZIP file!")

    restore_zip = "restore.zip"
    restore_dir = "restore_temp"

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)

        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir, exist_ok=True)

        with zipfile.ZipFile(restore_zip, "r") as zip_ref:
            zip_ref.extractall(restore_dir)

        important_files = [
            "memory.json", "group_data.json", "jokes.json", "fortunes.json",
            ALIAS_FILE, REPLY_FILE
        ]

        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            if os.path.exists(src):
                shutil.move(src, fname)

        init_files()
        await update.message.reply_text("✅ Restore completed successfully!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Restore error:\n{e}")

    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False# ======================= 💬 پاسخ‌دهی هوشمند و مدیریت پیام‌ها =======================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """موتور پاسخ اصلی ربات - هوش، alias و پاسخ‌های یادگرفته‌شده"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    # ثبت کاربر و گروه
    register_user(uid)
    register_group_activity(chat_id, uid)

    # 🔒 قفل یادگیری
    if status["locked"]:
        pass
    else:
        # auto learn از پیام‌ها
        from ai_learning import auto_learn_from_text
        auto_learn_from_text(text)

    # 💤 اگر ربات غیرفعاله فقط ذخیره کن
    if not status["active"]:
        from memory_manager import shadow_learn
        shadow_learn(text, "")
        return

    # ======================= ⚡️ سیستم alias =======================
    alias_target = get_alias(text.lower())
    if alias_target:
        text = alias_target  # مثلاً alias("جوک") -> "/joke"
        print(f"[ALIAS] {text}")

    # ======================= 💬 پاسخ سفارشی =======================
    custom = get_custom_reply(text)
    if custom:
        await update.message.reply_text(custom)
        return

    # ======================= درصد هوش منطقی =======================
    if text.lower() == "ai level" or text.lower() == "درصد هوش":
        memory_data = load_data("memory.json")
        phrases = len(memory_data.get("phrases", {}))
        responses = sum(len(v) for v in memory_data.get("phrases", {}).values()) if phrases else 0
        jokes = len(load_data("jokes.json"))
        fortunes = len(load_data("fortunes.json"))

        score = 20
        if phrases > 15 and responses > 25:
            score += 25
        if jokes > 5:
            score += 20
        if fortunes > 5:
            score += 15
        if score > 100:
            score = 100

        await update.message.reply_text(
            f"🤖 AI Level: {score}%\n🧠 Learned: {phrases} phrases, {responses} responses\n😂 Jokes: {jokes}\n🔮 Fortunes: {fortunes}"
        )
        return

    # ======================= 😂 جوک =======================
    if text.lower() in ["joke", "جوک"]:
        if os.path.exists("jokes.json"):
            data = load_data("jokes.json")
            if data:
                key, val = random.choice(list(data.items()))
                vtype = val.get("type", "text")
                v = val.get("value", "")
                try:
                    if vtype == "text":
                        await update.message.reply_text("😂 " + v)
                    elif vtype == "photo":
                        await update.message.reply_photo(photo=v, caption="😂 Funny!")
                    elif vtype == "video":
                        await update.message.reply_video(video=v, caption="😂 Video joke!")
                    elif vtype == "sticker":
                        await update.message.reply_sticker(sticker=v)
                except Exception as e:
                    await update.message.reply_text(f"⚠️ Error sending joke: {e}")
            else:
                await update.message.reply_text("😅 No jokes yet!")
        return

    # ======================= 🔮 فال =======================
    if text.lower() in ["fortune", "فال"]:
        if os.path.exists("fortunes.json"):
            data = load_data("fortunes.json")
            if data:
                key, val = random.choice(list(data.items()))
                vtype = val.get("type", "text")
                v = val.get("value", "")
                try:
                    if vtype == "text":
                        await update.message.reply_text("🔮 " + v)
                    elif vtype == "photo":
                        await update.message.reply_photo(photo=v, caption="🔮 Fortune!")
                    elif vtype == "video":
                        await update.message.reply_video(video=v, caption="🔮 Fortune video!")
                    elif vtype == "sticker":
                        await update.message.reply_sticker(sticker=v)
                except Exception as e:
                    await update.message.reply_text(f"⚠️ Error sending fortune: {e}")
            else:
                await update.message.reply_text("😔 No fortunes saved yet.")
        return

    # ======================= 🧠 یادگیری دستی =======================
    if text.lower().startswith("learn ") or text.lower().startswith("یادبگیر "):
        parts = text.replace("learn ", "").replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            from memory_manager import learn
            msg = learn(phrase, *responses)
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❗ Format: learn [trigger]\\n[response1]\\n[response2] ...")
        return

    # ======================= ✨ جمله تصادفی =======================
    if text.lower() in ["generate", "جمله بساز"]:
        from memory_manager import generate_sentence
        await update.message.reply_text(generate_sentence())
        return

    # ======================= 🧩 لیست جملات یادگرفته‌شده =======================
    if text.lower() in ["list", "لیست"]:
        from memory_manager import list_phrases
        await update.message.reply_text(list_phrases())
        return

    # ======================= 💬 پاسخ هوشمند یادگرفته‌شده =======================
    from memory_manager import get_reply, enhance_sentence
    learned_reply = get_reply(text)
    if learned_reply:
        await update.message.reply_text(enhance_sentence(learned_reply))
        return

    # ======================= 🧠 پاسخ احساسی / هوشمند =======================
    try:
        from smart_reply import detect_emotion, smart_response
        from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply

        emotion = detect_emotion(text)
        last = get_last_emotion(uid)
        context_reply = emotion_context_reply(emotion, last)
        remember_emotion(uid, emotion)

        if context_reply:
            reply_text = enhance_sentence(context_reply)
        else:
            reply_text = smart_response(text, emotion) or enhance_sentence(text)

        await update.message.reply_text(reply_text)
    except Exception as e:
        await update.message.reply_text(f"💬 (simple) {text}")# ======================= ⚙️ کنترل وضعیت =======================

async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    await update.message.reply_text("✅ Bot activated!" if status["active"] else "😴 Bot deactivated!")

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 Welcome messages enabled!" if status["welcome"] else "🚫 Welcome messages disabled!")

async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["locked"] = True
    await update.message.reply_text("🔒 Learning locked!")

async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["locked"] = False
    await update.message.reply_text("🔓 Learning unlocked!")

# ======================= 📊 آمار =======================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data("memory.json")
    users = len(data.get("users", []))
    phrases = len(data.get("phrases", {}))
    groups_data = load_data("group_data.json").get("groups", {})
    group_count = len(groups_data) if isinstance(groups_data, dict) else len(groups_data)

    msg = (
        f"📊 **Bot Stats:**\n"
        f"👤 Users: {users}\n"
        f"👥 Groups: {group_count}\n"
        f"💬 Phrases: {phrases}\n"
        f"🎭 Mode: {'Active' if status['active'] else 'Inactive'}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کامل گروه‌ها"""
    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})
        if not groups:
            return await update.message.reply_text("ℹ️ No groups registered yet.")

        text = "📈 **Group Stats:**\n\n"
        for gid, info in groups.items():
            name = info.get("title", f"Group_{gid}")
            members = len(info.get("members", []))
            last = info.get("last_active", "Unknown")
            text += f"🏠 {name}\n👥 Members: {members}\n🕓 Last Active: {last}\n\n"

        await update.message.reply_text(text[:4000], parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ======================= 🧹 پاکسازی و ریست =======================

async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Only admin can reset data!")

    for f in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json", ALIAS_FILE, REPLY_FILE]:
        if os.path.exists(f):
            os.remove(f)
    init_files()
    await update.message.reply_text("🧹 All data cleared successfully!")

async def reload_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_files()
    await update.message.reply_text("🔄 Memory reloaded successfully!")

# ======================= 📨 ارسال همگانی =======================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Only admin can broadcast!")

    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❗ Usage: /broadcast [message]")

    users = load_data("memory.json").get("users", [])
    groups_data = load_data("group_data.json").get("groups", {})

    group_ids = list(groups_data.keys()) if isinstance(groups_data, dict) else []
    sent, failed = 0, 0

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
        except:
            failed += 1

    for gid in group_ids:
        try:
            await context.bot.send_message(chat_id=int(gid), text=msg)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(
        f"📨 Broadcast complete ✅\n"
        f"👤 Users: {len(users)} | 👥 Groups: {len(group_ids)}\n"
        f"✅ Sent: {sent} | ⚠️ Failed: {failed}"
    )

# ======================= 🚪 خروج از گروه =======================

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🫡 Leaving group... See you soon 😂")
    await context.bot.leave_chat(update.message.chat.id)

# ======================= 🚀 اجرای نهایی =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Khangool v8.5.1 Cloud+ Supreme Pro Ready!\n"
        "Type /help to see all commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📘 Use /alias, /reply, /stats, /backup, /restore etc. for control.")

# ======================= 🌙 Startup =======================

async def notify_admin_on_startup(app):
    """ارسال پیام فعال‌سازی به ادمین هنگام استارت"""
    try:
        await app.bot.send_message(chat_id=ADMIN_ID, text="🚀 Khangool started successfully ✅")
    except Exception as e:
        print(f"[ERROR] Failed to notify admin: {e}")

async def on_startup(app):
    """تسک‌های اولیه هنگام شروع"""
    await notify_admin_on_startup(app)
    app.create_task(cloudsync_internal(app.bot, "Auto Backup"))
    print("🌙 [SYSTEM] Startup tasks scheduled ✅")

# ======================= 🧩 اجرای برنامه =======================

if __name__ == "__main__":
    print("🤖 Khangool 8.5.1 Cloud+ Supreme Pro — Booting...")

    app = ApplicationBuilder().token(TOKEN).build()

    # خطایاب
    async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
        print(f"⚠️ Error: {context.error}")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Error:\n{context.error}")
        except:
            pass

    app.add_error_handler(handle_error)

    # 📋 ثبت دستورها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("alias", add_alias))
    app.add_handler(CommandHandler("unalias", remove_alias))
    app.add_handler(CommandHandler("reply", add_reply))
    app.add_handler(CommandHandler("unreply", remove_reply))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("lock", lock_learning))
    app.add_handler(CommandHandler("unlock", unlock_learning))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("fullstats", fullstats))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("reload", reload_memory))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("cloudsync", cloudsync))
    app.add_handler(CommandHandler("leave", leave))

    # 📨 پیام‌ها
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)# ======================= 👋 خوشامدگویی با عکس پروفایل =======================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خوشامد با عکس پروفایل کاربر جدید"""
    if not status["welcome"]:
        return

    for member in update.message.new_chat_members:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        text = (
            f"🎉 Welcome {member.first_name}!\n"
            f"📅 Joined on: {now}\n"
            f"🏠 Group: {update.message.chat.title}\n"
            f"😄 Enjoy your stay!"
        )

        try:
            photos = await context.bot.get_user_profile_photos(member.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                await update.message.reply_photo(file_id, caption=text)
            else:
                await update.message.reply_text(text)
        except Exception:
            await update.message.reply_text(text)

# ======================= 🧠 Auto Brain Loop =======================

async def start_auto_brain_loop(bot):
    """حلقه یادگیری خودکار و هوشمند"""
    while True:
        try:
            data = load_data("memory.json")
            phrases = len(data.get("phrases", {}))
            if phrases < 5:
                print("[AUTO-BRAIN] Expanding base memory...")
                learn("سلام", "سلام! حالت چطوره؟")
                learn("خداحافظ", "فعلاً! به زودی می‌بینمت 😄")
            else:
                print("[AUTO-BRAIN] Memory stable ✅")

            # هر ۶ ساعت بررسی کن
            await asyncio.sleep(21600)
        except Exception as e:
            print(f"[AUTO-BRAIN ERROR] {e}")
            await asyncio.sleep(600)

# ======================= 🔁 ترکیب نهایی Startup =======================

async def on_startup(app):
    """اجرای تسک‌ها هنگام استارت"""
    await notify_admin_on_startup(app)
    app.create_task(start_auto_brain_loop(app.bot))
    app.create_task(cloudsync_internal(app.bot, "Auto Backup"))
    print("🌙 [SYSTEM] Auto Brain + Cloud Backup enabled ✅")

# ======================= 🧠 هوش خودکار و پایداری =======================

async def health_check(bot):
    """بررسی سلامت فایل‌ها و پایداری سیستم"""
    essential = ["memory.json", "group_data.json", "jokes.json", "fortunes.json", ALIAS_FILE, REPLY_FILE]
    missing = [f for f in essential if not os.path.exists(f)]
    if missing:
        for f in missing:
            ensure_file_exists(f, {})
        await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Missing files recreated: {', '.join(missing)}")
    else:
        print("[HEALTH] All core files OK ✅")

# ======================= 🧾 گزارش وضعیت لحظه‌ای =======================

async def system_report(bot):
    """ارسال گزارش دوره‌ای از وضعیت حافظه به ادمین"""
    try:
        memory = load_data("memory.json")
        users = len(memory.get("users", []))
        phrases = len(memory.get("phrases", {}))
        groups = len(load_data("group_data.json").get("groups", {}))

        report = (
            f"🧾 **System Report:**\n"
            f"👤 Users: {users}\n"
            f"👥 Groups: {groups}\n"
            f"💬 Learned phrases: {phrases}\n"
            f"🕓 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=report, parse_mode="Markdown")
    except Exception as e:
        print(f"[REPORT ERROR] {e}")

# ======================= 🌍 اجرای نهایی =======================

if __name__ == "__main__":
    print("🚀 Finalizing Khangool v8.5.1 Cloud+ Supreme Pro...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(handle_error)

    # ثبت دستورات اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("alias", add_alias))
    app.add_handler(CommandHandler("unalias", remove_alias))
    app.add_handler(CommandHandler("reply", add_reply))
    app.add_handler(CommandHandler("unreply", remove_reply))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("fullstats", fullstats))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("reload", reload_memory))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("cloudsync", cloudsync))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("lock", lock_learning))
    app.add_handler(CommandHandler("unlock", unlock_learning))

    # ثبت پیام‌ها
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # اجرای تسک‌های خودکار
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
