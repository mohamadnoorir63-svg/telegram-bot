# === پارت ۱ از ۵ ===
import asyncio
import os
import random
import zipfile
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import aiofiles

# 📦 ماژول‌ها
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn, get_reply,
    set_mode, get_stats, enhance_sentence, generate_sentence, list_phrases
)
from jokes_manager import save_joke, list_jokes
from fortune_manager import save_fortune, list_fortunes
from group_manager import register_group_activity, get_group_stats
from ai_learning import auto_learn_from_text
from smart_reply import detect_emotion, smart_response
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply
from auto_brain.auto_brain import start_auto_brain_loop

# 🎯 تنظیمات پایه
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
init_files()

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}

# ======================= 🧩 alias / unalias / aliases (ساخت دستور مستعار) =======================
ALIASES_FILE = "aliases.json"

def load_aliases():
    if os.path.exists(ALIASES_FILE):
        try:
            return load_data(ALIASES_FILE)
        except Exception:
            pass
    return {}

def save_aliases(d):
    try:
        save_data(ALIASES_FILE, d)
    except Exception as e:
        print("[ALIAS SAVE ERROR]", e)

ALIASES = load_aliases()

def normalize_alias(t: str) -> str:
    return (t or "").strip().lower()

async def handle_alias_execution(text: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """اگر متن کاربر با یکی از aliasها تطبیق داشت، اجراش کن."""
    key = normalize_alias(text)
    if key not in ALIASES:
        return False

    data = ALIASES[key]
    typ = data.get("type")

    if typ == "text":
        await update.message.reply_text(data.get("value", ""))
        return True

    if typ == "command":
        cmd = data.get("target", "").lstrip("/")
        if not cmd:
            return False
        if "COMMAND_MAP" in globals() and cmd in COMMAND_MAP:
            await COMMAND_MAP[cmd](update, context)
        else:
            await update.message.reply_text(f"⚠️ دستور «{cmd}» پیدا نشد.")
        return True

    return False


# ======================= 🔧 مدیریت alias از چت =======================
async def alias_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فقط مدیر اصلی می‌تونه alias بسازه یا حذف کنه"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if update.effective_user.id != ADMIN_ID:
        return  # فقط مدیر اصلی اجازه دارد

    # 📜 لیست alias‌ها
    if text.lower() in ["aliases", "alias list", "لیست alias", "لیست aliasها"]:
        if not ALIASES:
            return await update.message.reply_text("ℹ️ هنوز هیچ aliasی تعریف نشده.")
        msg = "📜 لیست alias‌ها:\n\n"
        for k, v in ALIASES.items():
            if v.get("type") == "text":
                msg += f"• {k} → پاسخ ثابت\n"
            else:
                msg += f"• {k} → اجرای /{v.get('target')}\n"
        return await update.message.reply_text(msg)

    # ❌ حذف alias → unalias NAME
    if text.lower().startswith("unalias "):
        name = normalize_alias(text.split(" ", 1)[1])
        if name in ALIASES:
            ALIASES.pop(name)
            save_aliases(ALIASES)
            return await update.message.reply_text(f"🗑️ دستور مستعار «{name}» حذف شد.")
        return await update.message.reply_text("⚠️ همچین aliasی وجود ندارد.")

    # ✅ ساخت alias → alias NAME='متن: سلام' یا alias NAME='/stats'
    if text.lower().startswith("alias "):
        try:
            body = text[6:].strip()
            if "=" not in body:
                return await update.message.reply_text(
                    "❗ قالب نادرست است.\n\n"
                    "📘 مثال‌ها:\n"
                    "alias آمار='/stats'\n"
                    "alias خوشی='متن: خوشحال شدم دیدمت 😊'"
                )

            left, right = body.split("=", 1)
            name = normalize_alias(left.replace("'", "").replace('"', '').strip())
            value = right.strip().strip("'").strip('"')

            if not name:
                return await update.message.reply_text("❗ نام alias خالی است.")

            if value.lower().startswith("متن:") or value.lower().startswith("text:"):
                ALIASES[name] = {"type": "text", "value": value.split(":", 1)[1].strip()}
                save_aliases(ALIASES)
                return await update.message.reply_text(f"✅ alias «{name}» ساخته شد → پاسخ ثابت")

            target = value.lstrip("/").strip()
            ALIASES[name] = {"type": "command", "target": target}
            save_aliases(ALIASES)
            return await update.message.reply_text(f"✅ alias «{name}» ساخته شد → اجرای /{target}")

        except Exception as e:
            return await update.message.reply_text(f"⚠️ خطا در alias: {e}")# === پارت ۲ از ۵ ===

# ======================= ✳️ شروع و پیام فعال‌سازی =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )

async def notify_admin_on_startup(app):
    """ارسال پیام فعال‌سازی به ادمین هنگام استارت"""
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 ربات خنگول 8.5.1 Cloud+ Supreme Pro Stable+ با موفقیت فعال شد ✅"
        )
        print("[INFO] Startup notification sent ✅")
    except Exception as e:
        print(f"[ERROR] Admin notify failed: {e}")

# ======================= ⚙️ خطایاب خودکار =======================
async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    error_text = f"⚠️ خطا در ربات:\n\n{context.error}"
    print(error_text)
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=error_text)
    except:
        pass

# ======================= 📘 راهنمای قابل ویرایش =======================
HELP_FILE = "custom_help.txt"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /help و واژه 'راهنما' از فایل custom_help.txt بخونن"""
    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "مدیر اصلی می‌تونه با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنه."
        )
    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)

async def save_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره متن راهنما با ریپلای (فقط توسط ADMIN_ID)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه راهنما رو تنظیم کنه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ برای ثبت راهنما باید روی یک پیام متنی ریپلای کنی!")

    text = update.message.reply_to_message.text
    async with aiofiles.open(HELP_FILE, "w", encoding="utf-8") as f:
        await f.write(text)

    await update.message.reply_text("✅ متن راهنما با موفقیت ذخیره شد!")

# ======================= 🎭 تغییر مود =======================
async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("🎭 استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")

    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"🎭 مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")

# ======================= ⚙️ کنترل وضعیت =======================
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    await update.message.reply_text("✅ فعال شد!" if status["active"] else "😴 خاموش شد!")

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!")

async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["locked"] = True
    await update.message.reply_text("🔒 یادگیری قفل شد!")

async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["locked"] = False
    await update.message.reply_text("🔓 یادگیری باز شد!")# === پارت ۳ از ۵ ===

# ======================= 📊 آمار خلاصه =======================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    memory = load_data("memory.json")
    groups = len(load_data("group_data.json").get("groups", []))
    users = len(memory.get("users", []))

    msg = (
        f"📊 آمار خنگول:\n"
        f"👤 کاربران: {users}\n"
        f"👥 گروه‌ها: {groups}\n"
        f"🧩 جملات: {data['phrases']}\n"
        f"💬 پاسخ‌ها: {data['responses']}\n"
        f"🎭 مود فعلی: {data['mode']}"
    )
    await update.message.reply_text(msg)

# ======================= 📊 آمار کامل گروه‌ها =======================
async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کامل گروه‌ها"""
    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})

        if isinstance(groups, list):
            if not groups:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")
            text = "📈 آمار کامل گروه‌ها:\n\n"
            for g in groups:
                group_id = g.get("id", "نامشخص")
                title = g.get("title", f"Group_{group_id}")
                members = len(g.get("members", []))
                last_active = g.get("last_active", "نامشخص")
                try:
                    chat = await context.bot.get_chat(group_id)
                    if chat.title:
                        title = chat.title
                except:
                    pass
                text += f"🏠 {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last_active}\n\n"

        elif isinstance(groups, dict):
            if not groups:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")
            text = "📈 آمار کامل گروه‌ها:\n\n"
            for group_id, info in groups.items():
                title = info.get("title", f"Group_{group_id}")
                members = len(info.get("members", []))
                last_active = info.get("last_active", "نامشخص")
                try:
                    chat = await context.bot.get_chat(group_id)
                    if chat.title:
                        title = chat.title
                except:
                    pass
                text += f"🏠 {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last_active}\n\n"

        else:
            return await update.message.reply_text("⚠️ ساختار فایل group_data.json نامعتبر است!")

        if len(text) > 4000:
            text = text[:3990] + "..."
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آمار گروه‌ها:\n{e}")

# ======================= 👋 خوشامد با عکس پروفایل =======================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خوشامد با عکس پروفایل"""
    if not status["welcome"]:
        return
    for member in update.message.new_chat_members:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        text = (
            f"🎉 خوش اومدی {member.first_name}!\n"
            f"📅 {now}\n"
            f"🏠 گروه: {update.message.chat.title}\n"
            f"😄 امیدوارم لحظات خوبی داشته باشی!"
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

# ======================= 👤 ثبت خودکار کاربران =======================
def register_user(user_id):
    """ثبت کاربر در memory.json"""
    data = load_data("memory.json")
    users = data.get("users", [])
    if user_id not in users:
        users.append(user_id)
    data["users"] = users
    save_data("memory.json", data)

# ======================= ☁️ بک‌آپ خودکار و دستی =======================
import shutil

async def auto_backup(bot):
    """بک‌آپ خودکار هر ۱۲ ساعت"""
    while True:
        await asyncio.sleep(43200)
        await cloudsync_internal(bot, "Auto Backup")

def _should_include_in_backup(path: str) -> bool:
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp"]
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

async def cloudsync_internal(bot, reason="Manual Backup"):
    """بک‌آپ ابری برای مدیر"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=arcname)
        with open(filename, "rb") as f:
            await bot.send_document(chat_id=ADMIN_ID, document=f, filename=filename)
        await bot.send_message(chat_id=ADMIN_ID, text=f"☁️ {reason} انجام شد ✅")
    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ خطا در Cloud Backup:\n{e}")
        except:
            pass
    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")# === پارت ۴ از ۵ ===

# ======================= 💬 پاسخ، هوش مصنوعی، alias و سیستم فال و جوک =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ‌دهی هوش مصنوعی و سیستم alias"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    register_user(uid)
    register_group_activity(chat_id, uid)

    if not status["locked"]:
        auto_learn_from_text(text)

    if not status["active"]:
        shadow_learn(text, "")
        return

    # 🎯 بررسی aliasها
    if await handle_alias_execution(text, update, context):
        return

    # ✅ درصد هوش
    if text.lower() == "درصد هوش":
        data = load_data("memory.json")
        phrases = len(data.get("phrases", {}))
        responses = sum(len(v) for v in data.get("phrases", {}).values()) if phrases else 0
        score = min(100, phrases + responses // 2)
        await update.message.reply_text(
            f"🤖 درصد هوش فعلی خنگول: {score}%\n"
            f"📈 جملات: {phrases} | پاسخ‌ها: {responses}\n"
            f"🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        )
        return

    # ✅ درصد هوش اجتماعی
    if text.lower() == "درصد هوش اجتماعی":
        users = len(load_data("memory.json").get("users", []))
        groups = len(load_data("group_data.json").get("groups", {}))
        score = min(100, (users + groups * 2))
        await update.message.reply_text(
            f"💬 درصد هوش اجتماعی خنگول: {score}%\n"
            f"👤 کاربران: {users}\n"
            f"👥 گروه‌ها: {groups}"
        )
        return

    # ✅ هوش کلی
    if text.lower() == "هوش کلی":
        data = load_data("memory.json")
        phrases = len(data.get("phrases", {}))
        responses = sum(len(v) for v in data.get("phrases", {}).values()) if phrases else 0
        users = len(data.get("users", []))
        jokes = len(load_data("jokes.json")) if os.path.exists("jokes.json") else 0
        fortunes = len(load_data("fortunes.json")) if os.path.exists("fortunes.json") else 0
        score = min(160, int((phrases + responses + users + jokes + fortunes) / 2))
        level = "🌟 نابغه دیجیتال" if score >= 130 else "🧠 باهوش" if score >= 100 else "🙂 در حال رشد"
        await update.message.reply_text(
            f"🧠 IQ کلی خنگول: {score}\n{level}\n"
            f"📊 جملات: {phrases}, پاسخ‌ها: {responses}\n😂 جوک‌ها: {jokes}, 🔮 فال‌ها: {fortunes}"
        )
        return

    # ✅ جوک تصادفی
    if text == "جوک":
        if os.path.exists("jokes.json"):
            data = load_data("jokes.json")
            if data:
                key, val = random.choice(list(data.items()))
                t = val.get("type", "text")
                v = val.get("value", "")
                try:
                    if t == "text":
                        await update.message.reply_text("😂 " + v)
                    elif t == "photo":
                        await update.message.reply_photo(photo=v, caption="😂 جوک تصویری!")
                    elif t == "video":
                        await update.message.reply_video(video=v, caption="😂 جوک ویدیویی!")
                    elif t == "sticker":
                        await update.message.reply_sticker(sticker=v)
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال جوک: {e}")
            else:
                await update.message.reply_text("هنوز جوکی ثبت نشده 😅")
        else:
            await update.message.reply_text("📂 فایل جوک‌ها پیدا نشد 😕")
        return

    # ✅ فال تصادفی
    if text == "فال":
        if os.path.exists("fortunes.json"):
            data = load_data("fortunes.json")
            if data:
                key, val = random.choice(list(data.items()))
                t = val.get("type", "text")
                v = val.get("value", "")
                try:
                    if t == "text":
                        await update.message.reply_text("🔮 " + v)
                    elif t == "photo":
                        await update.message.reply_photo(photo=v, caption="🔮 فال تصویری!")
                    elif t == "video":
                        await update.message.reply_video(video=v, caption="🔮 فال ویدیویی!")
                    elif t == "sticker":
                        await update.message.reply_sticker(sticker=v)
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال فال: {e}")
            else:
                await update.message.reply_text("هنوز فالی ثبت نشده 😔")
        else:
            await update.message.reply_text("📂 فایل فال‌ها پیدا نشد 😕")
        return

    # ✅ ثبت جوک و فال
    if text.lower() == "ثبت جوک" and update.message.reply_to_message:
        await save_joke(update)
        return
    if text.lower() == "ثبت فال" and update.message.reply_to_message:
        await save_fortune(update)
        return

    # ✅ لیست‌ها
    if text == "لیست جوک‌ها":
        await list_jokes(update)
        return
    if text == "لیست فال‌ها":
        await list_fortunes(update)
        return
    if text == "لیس
