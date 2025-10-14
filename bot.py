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
    "locked": False,
    "reply_mode": False
}

# ======================= ✳️ شروع و پیام فعال‌سازی =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 9.0 Cloud+ Ultra Stable\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )

async def notify_admin_on_startup(app):
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 خنگول فارسی 9.0 Cloud+ Ultra Stable با موفقیت فعال شد ✅"
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
    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "مدیر اصلی می‌تونه با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنه."
        )
    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)

async def save_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه این کارو کنه!")
    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی یه پیام متنی ریپلای کنی تا به عنوان راهنما ذخیره بشه!")
    text = update.message.reply_to_message.text
    async with aiofiles.open(HELP_FILE, "w", encoding="utf-8") as f:
        await f.write(text)
    await update.message.reply_text("✅ راهنما با موفقیت ذخیره شد!")

# ======================= 🎭 تغییر مود =======================
async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat

    # فقط مدیر یا سودو
    if user_id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat.id, user_id)
            if member.status not in ["administrator", "creator"]:
                return await update.message.reply_text("⛔ فقط مدیر می‌تونه مود رو تغییر بده.")
        except:
            return await update.message.reply_text("⚠️ خطا در بررسی سطح دسترسی مدیر.")

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
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط سودو می‌تونه ربات رو خاموش یا روشن کنه.")
    status["active"] = not status["active"]
    await update.message.reply_text("✅ فعال شد!" if status["active"] else "😴 خاموش شد!")

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    if user_id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat.id, user_id)
            if member.status not in ["administrator", "creator"]:
                return await update.message.reply_text("⛔ فقط مدیر گروه می‌تونه خوشامد رو تنظیم کنه.")
        except:
            return await update.message.reply_text("⚠️ خطا در بررسی سطح دسترسی.")
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!")

async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط سودو مجازه این بخشو قفل کنه.")
    status["locked"] = True
    await update.message.reply_text("🔒 یادگیری قفل شد!")

async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط سودو مجازه این بخشو باز کنه.")
    status["locked"] = False
    await update.message.reply_text("🔓 یادگیری باز شد!")import shutil

# ======================= ☁️ بک‌آپ خودکار و دستی (نسخه امن) =======================
async def auto_backup(bot):
    """بک‌آپ خودکار هر ۱۲ ساعت"""
    while True:
        await asyncio.sleep(43200)
        await cloudsync_internal(bot, "Auto Backup")

def _should_include_in_backup(path: str) -> bool:
    """فقط فایل‌های داده‌ای مهم داخل بک‌آپ بروند"""
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp"]
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

async def cloudsync_internal(bot, reason="Manual Backup"):
    """ایجاد و ارسال فایل بک‌آپ به ادمین (Cloud Safe)"""
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

        # ارسال بک‌آپ فقط برای سودو
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

# ======================= ☁️ بک‌آپ ابری دستی =======================
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستی بک‌آپ ابری"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه از Cloud Backup استفاده کنه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ ZIP در چت =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بک‌آپ محلی و ارسال داخل همین چت"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه بک‌آپ بگیره!")

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
            await update.message.reply_document(document=f, filename=filename)
        await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در گرفتن بک‌آپ:\n{e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= 💾 بازیابی از ZIP با امنیت بالا =======================
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درخواست فایل ZIP برای بازیابی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه داده‌ها رو بازیابی کنه.")
    await update.message.reply_text("📂 فایل ZIP بک‌آپ رو ارسال کن تا بازیابی بشه.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش فایل ZIP و بازیابی ایمن با پوشه موقتی"""
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ لطفاً یک فایل ZIP معتبر بفرست.")

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

        important_files = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]
        moved_any = False
        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            if os.path.exists(src):
                shutil.move(src, fname)
                moved_any = True

        init_files()

        if moved_any:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ هیچ فایلی برای جایگزینی پیدا نشد.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")
    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False# ======================= 💬 پاسخ‌دهی و سیستم ریپلی =======================

# ذخیره وضعیت ریپلی در حافظه (برای هر چت جدا)
REPLY_STATE_FILE = "reply_mode.json"

def load_reply_state():
    if os.path.exists(REPLY_STATE_FILE):
        return load_data(REPLY_STATE_FILE)
    return {}

def save_reply_state(data):
    save_data(REPLY_STATE_FILE, data)

async def toggle_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن/خاموش کردن حالت ریپلی — مخصوص مدیران و سودو"""
    user_id = update.effective_user.id
    chat = update.effective_chat
    reply_data = load_reply_state()

    # فقط سودو یا مدیر گروه مجازه
    if user_id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat.id, user_id)
            if member.status not in ["administrator", "creator"]:
                return await update.message.reply_text("⛔ فقط مدیران می‌تونن ریپلی مود رو تنظیم کنن.")
        except:
            return await update.message.reply_text("⚠️ خطا در بررسی سطح دسترسی مدیر.")

    cid = str(chat.id)
    reply_data[cid] = not reply_data.get(cid, False)
    save_reply_state(reply_data)
    state = "🔁 حالت ریپلی فعال شد!" if reply_data[cid] else "🚫 حالت ریپلی غیرفعال شد!"
    await update.message.reply_text(state)


# ======================= 💬 پاسخ اصلی هوشمند و احساسات =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ‌دهی اصلی هوش مصنوعی و سیستم یادگیری"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    is_private = update.effective_chat.type == "private"

    # 📌 فقط سودو در پیوی
    if is_private and user_id != ADMIN_ID:
        return

    # ثبت کاربر و گروه
    register_user(user_id)
    register_group_activity(chat_id, user_id)

    # ریپلی مود وضعیت فعلی
    reply_state = load_reply_state()
    reply_mode = reply_state.get(str(chat_id), False)

    # اگر ریپلی روشن باشه و پیام ریپلای نباشه → سکوت کن مگر "خنگول کجایی"
    if reply_mode and not update.message.reply_to_message:
        if "خنگول کجایی" in text:
            return await update.message.reply_text("اینجام 😎")
        return

    # یادگیری خودکار
    if not status["locked"]:
        auto_learn_from_text(text)

    # اگر خاموش بود فقط یادگیری در سایه
    if not status["active"]:
        shadow_learn(text, "")
        return

    # ✅ هوش‌های ویژه
    lower_text = text.lower()

    if lower_text == "درصد هوش":
        return await show_logical_iq(update)
    elif lower_text == "درصد هوش اجتماعی":
        return await show_social_iq(update)
    elif lower_text == "هوش کلی":
        return await show_total_iq(update)

    # ✅ دستور یادبگیر
    if text.startswith("یادبگیر "):
        if user_id != ADMIN_ID:
            return await update.message.reply_text("⛔ فقط سودو مجازه جمله‌ها رو آموزش بده.")
        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            msg = learn(phrase, *responses)
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❗ بعد از 'یادبگیر' جمله و پاسخ‌هاش رو با خط جدید بنویس.")
        return

    # ✅ جمله تصادفی
    if text == "جمله بساز":
        return await update.message.reply_text(generate_sentence())

    # ✅ لیست جملات
    if text == "لیست":
        return await update.message.reply_text(list_phrases())

    # ✅ جوک تصادفی
    if text == "جوک":
        return await send_random_joke(update)

    # ✅ فال تصادفی
    if text == "فال":
        return await send_random_fortune(update)

    # ✅ ثبت جوک یا فال
    if text.lower() == "ثبت جوک" and update.message.reply_to_message:
        return await save_joke(update)
    if text.lower() == "ثبت فال" and update.message.reply_to_message:
        return await save_fortune(update)

    # ✅ حالت پاسخ هوشمند و احساسی
    learned_reply = get_reply(text)
    emotion = detect_emotion(text)

    last_emotion = get_last_emotion(user_id)
    context_reply = emotion_context_reply(emotion, last_emotion)
    remember_emotion(user_id, emotion)

    if context_reply:
        reply_text = enhance_sentence(context_reply)
    elif learned_reply:
        reply_text = enhance_sentence(learned_reply)
    else:
        reply_text = smart_response(text, user_id) or enhance_sentence(text)

    await update.message.reply_text(reply_text)


# ======================= 🧠 توابع فرعی برای ارسال فال و جوک =======================
async def send_random_joke(update: Update):
    if not os.path.exists("jokes.json"):
        return await update.message.reply_text("📂 هنوز جوکی ثبت نشده 😅")

    data = load_data("jokes.json")
    if not data:
        return await update.message.reply_text("😅 هنوز جوکی ثبت نشده.")

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

async def send_random_fortune(update: Update):
    if not os.path.exists("fortunes.json"):
        return await update.message.reply_text("📂 هنوز فالی ثبت نشده 😔")

    data = load_data("fortunes.json")
    if not data:
        return await update.message.reply_text("😔 هنوز فالی ثبت نشده.")

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
        await update.message.reply_text(f"⚠️ خطا در ارسال فال: {e}")# ======================= 🧠 هوش منطقی (درصد هوش) =======================
async def show_logical_iq(update: Update):
    score = 0
    details = []

    # حافظه اصلی
    if os.path.exists("memory.json"):
        data = load_data("memory.json")
        phrases = len(data.get("phrases", {}))
        responses = sum(len(v) for v in data.get("phrases", {}).values()) if phrases else 0

        if phrases > 100 and responses > 300:
            score += 40
            details.append("🧠 حافظه گسترده و دقیق — قدرت تحلیل بالاست ✅")
        elif phrases > 30:
            score += 25
            details.append("🧩 حافظه فعال و در حال گسترش 🟢")
        elif phrases > 10:
            score += 15
            details.append("⚪ حافظه محدود ولی یادگیرنده")
        else:
            score += 5
            details.append("🌱 در ابتدای مسیر یادگیری")

    # شوخ‌طبعی
    if os.path.exists("jokes.json"):
        data = load_data("jokes.json")
        count = len(data)
        if count > 20:
            score += 15
            details.append("😂 شوخ‌طبع و خلاق 😄")
        elif count > 5:
            score += 10
            details.append("😅 کمی شوخ‌طبع")
        else:
            details.append("⚪ هنوز زیاد شوخی بلد نیست")

    # فال‌ها
    if os.path.exists("fortunes.json"):
        data = load_data("fortunes.json")
        if len(data) > 20:
            score += 10
            details.append("🔮 فال‌های متنوع و مثبت 💫")
        elif len(data) > 5:
            score += 5
            details.append("🔮 فال‌های محدود ولی موجود")
        else:
            details.append("⚪ فال زیادی ثبت نشده")

    # سیستم پاسخ هوشمند
    try:
        test = smart_response("سلام", "شاد")
        if test:
            score += 15
            details.append("🤖 پاسخ هوشمند فعاله و دقیق ✅")
        else:
            details.append("⚪ پاسخ هوشمند فعاله ولی ضعیف")
    except:
        details.append("⚠️ خطا در smart_response")

    # پایداری فایل‌ها
    essential_files = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]
    stable_count = sum(os.path.exists(f) for f in essential_files)
    if stable_count == len(essential_files):
        score += 15
        details.append("💾 حافظه کامل و پایدار ✅")
    elif stable_count >= 2:
        score += 8
        details.append("⚠️ بخشی از داده‌ها ناقص است")
    else:
        details.append("🚫 فایل‌های کلیدی از دست رفته‌اند")

    score = min(score, 100)
    result = (
        f"🧠 درصد هوش منطقی خنگول: *{score}%*\n\n"
        + "\n".join(details)
        + f"\n\n📈 نسخه Cloud+ Ultra Intelligence\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
    )
    await update.message.reply_text(result, parse_mode="Markdown")


# ======================= 💬 هوش اجتماعی =======================
async def show_social_iq(update: Update):
    score = 0
    details = []

    memory = load_data("memory.json")
    users = len(memory.get("users", []))
    if users > 200:
        score += 30
        details.append(f"👤 کاربران زیاد ({users}) — تعامل گسترده 🌍")
    elif users > 50:
        score += 20
        details.append(f"👥 کاربران فعال ({users}) 🟢")
    elif users > 10:
        score += 10
        details.append(f"🙂 کاربران محدود ({users})")
    else:
        details.append("⚪ هنوز مخاطبین کمی دارم 😅")

    # گروه‌ها
    groups_data = load_data("group_data.json").get("groups", {})
    group_count = len(groups_data) if isinstance(groups_data, dict) else len(groups_data)
    if group_count > 20:
        score += 25
        details.append(f"🏠 گروه‌های زیاد ({group_count}) — اجتماعی بالا 😎")
    elif group_count > 5:
        score += 15
        details.append(f"🏠 چند گروه فعال ({group_count})")
    elif group_count > 0:
        score += 10
        details.append(f"🏠 عضو چند گروه محدود ({group_count})")
    else:
        details.append("🚫 هنوز در هیچ گروهی عضو نیستم")

    # تعاملات
    try:
        activity = get_group_stats()
        active_chats = activity.get("active_chats", 0)
        total_msgs = activity.get("messages", 0)
        if total_msgs > 300:
            score += 25
            details.append("💬 تعامل مداوم و زیاد 😎")
        elif total_msgs > 100:
            score += 15
            details.append("💬 تعامل متوسط 🟢")
        elif total_msgs > 10:
            score += 10
            details.append("💬 تعامل کم ولی فعال 🙂")
        else:
            details.append("⚪ هنوز گفت‌وگوهای کمی دارم")
    except:
        details.append("⚠️ آمار تعاملات در دسترس نیست")

    # تحلیل احساسات
    try:
        test = detect_emotion("دوستت دارم")
        if test in ["شاد", "مهربان"]:
            score += 10
            details.append("❤️ احساس‌پذیر و اجتماعی 💞")
        else:
            details.append("⚪ تحلیل احساسی معمولی")
    except:
        details.append("⚠️ احساسات قابل بررسی نیست")

    score = min(score, 100)
    result = (
        f"💬 درصد هوش اجتماعی خنگول: *{score}%*\n\n"
        + "\n".join(details)
        + f"\n\n📊 شاخص تعامل اجتماعی پیشرفته\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
    )
    await update.message.reply_text(result, parse_mode="Markdown")


# ======================= 🤖 هوش کلی =======================
async def show_total_iq(update: Update):
    logical_score = random.randint(60, 90)  # امتیاز ترکیبی تقریبی
    social_score = random.randint(50, 85)
    overall = int((logical_score + social_score) / 2 + random.randint(0, 10))

    # محاسبه سطح هوش بر اساس امتیاز کلی
    if overall >= 130:
        level = "🌟 نابغه دیجیتال"
    elif overall >= 110:
        level = "🧠 باهوش و تحلیل‌گر"
    elif overall >= 90:
        level = "🙂 نرمال ولی یادگیرنده"
    else:
        level = "🤪 خنگول کلاسیک 😅"

    result = (
        f"🤖 IQ کلی خنگول: *{overall}*\n"
        f"{level}\n\n"
        f"🧩 میانگین هوش منطقی: {logical_score}%\n"
        f"💬 میانگین هوش اجتماعی: {social_score}%\n"
        f"📈 سطح ترکیبی: {level}\n\n"
        f"🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}\n"
        f"نسخه: Cloud+ Ultra AI Analyzer"
    )
    await update.message.reply_text(result, parse_mode="Markdown")# ======================= 🧩 سیستم Alias (دستورات سفارشی) =======================

ALIASES_FILE = "aliases.json"

def load_aliases():
    if os.path.exists(ALIASES_FILE):
        return load_data(ALIASES_FILE)
    return {}

def save_aliases(data):
    save_data(ALIASES_FILE, data)

async def set_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ایجاد دستور سفارشی /alias"""
    user_id = update.effective_user.id
    chat = update.effective_chat

    # فقط سودو یا مدیران گروه مجازند
    if user_id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat.id, user_id)
            if member.status not in ["administrator", "creator"]:
                return await update.message.reply_text("⛔ فقط مدیران و سودو می‌تونن دستور سفارشی بسازن.")
        except:
            return await update.message.reply_text("⚠️ خطا در بررسی سطح دسترسی مدیر.")

    if len(context.args) < 2:
        return await update.message.reply_text("❗ استفاده: `/alias [نام جدید] [دستور اصلی]`", parse_mode="Markdown")

    alias_name = context.args[0].lower()
    original_command = " ".join(context.args[1:])

    data = load_aliases()
    data[alias_name] = original_command
    save_aliases(data)

    await update.message.reply_text(f"✅ دستور `{alias_name}` حالا معادل `{original_command}` است!", parse_mode="Markdown")


async def remove_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف دستور سفارشی /unalias"""
    user_id = update.effective_user.id
    chat = update.effective_chat

    if user_id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat.id, user_id)
            if member.status not in ["administrator", "creator"]:
                return await update.message.reply_text("⛔ فقط مدیران یا سودو می‌تونن حذف کنن.")
        except:
            return await update.message.reply_text("⚠️ خطا در بررسی سطح دسترسی مدیر.")

    if len(context.args) < 1:
        return await update.message.reply_text("❗ استفاده: `/unalias [نام دستور]`", parse_mode="Markdown")

    alias_name = context.args[0].lower()
    data = load_aliases()

    if alias_name not in data:
        return await update.message.reply_text("⚠️ چنین دستوری ثبت نشده.")

    del data[alias_name]
    save_aliases(data)
    await update.message.reply_text(f"🗑️ دستور `{alias_name}` حذف شد.", parse_mode="Markdown")


async def list_aliases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست دستورات سفارشی"""
    data = load_aliases()
    if not data:
        return await update.message.reply_text("ℹ️ هنوز هیچ دستور سفارشی ثبت نشده.")
    msg = "🧩 لیست دستورات سفارشی:\n\n"
    for k, v in data.items():
        msg += f"🔹 `{k}` → `{v}`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")


# ======================= 💬 اجرای Alias =======================
async def check_alias_and_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی و اجرای دستور سفارشی در متن پیام"""
    if not update.message or not update.message.text:
        return False

    text = update.message.text.strip().lower()
    data = load_aliases()

    if text in data:
        new_command = data[text]
        fake_update = update
        fake_update.message.text = new_command
        await reply(fake_update, context)
        return True

    return False# ======================= 🛡️ سیستم سطح دسترسی =======================

def is_admin(user_id):
    """بررسی اینکه آیا کاربر مدیر اصلی (سودو) است"""
    return user_id == ADMIN_ID

async def is_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی اینکه آیا کاربر مدیر گروه است"""
    user_id = update.effective_user.id
    chat = update.effective_chat
    try:
        member = await context.bot.get_chat_member(chat.id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# ======================= 🔒 کنترل دستورات =======================

async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن / خاموش کردن ربات — فقط سودو"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه این کار رو انجام بده.")
    status["active"] = not status["active"]
    await update.message.reply_text("✅ ربات فعال شد!" if status["active"] else "😴 ربات خاموش شد!")

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال/غیرفعال کردن خوش‌آمد — برای مدیران گروه و سودو"""
    user_id = update.effective_user.id
    if not (is_admin(user_id) or await is_group_admin(update, context)):
        return await update.message.reply_text("⛔ فقط مدیران و سودو می‌تونن خوش‌آمد رو تنظیم کنن.")

    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوش‌آمد فعال شد!" if status["welcome"] else "🚫 خوش‌آمد غیرفعال شد!")

async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر مود — فقط مدیران و سودو"""
    user_id = update.effective_user.id
    if not (is_admin(user_id) or await is_group_admin(update, context)):
        return await update.message.reply_text("⛔ فقط مدیران و سودو مجازند مود را تغییر دهند.")
    if not context.args:
        return await update.message.reply_text("🎭 استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")

    mood = context.args[0].lower()
    valid_modes = ["شوخ", "بی‌ادب", "غمگین", "نرمال"]
    if mood in valid_modes:
        set_mode(mood)
        await update.message.reply_text(f"🎭 مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text(f"❌ مود نامعتبر است! مودهای معتبر: {', '.join(valid_modes)}")


# ======================= 📊 آمار فقط برای سودو =======================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کلی — فقط سودو"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه آمار کلی ببینه.")
    data = get_stats()
    memory = load_data("memory.json")
    groups = len(load_data("group_data.json").get("groups", []))
    users = len(memory.get("users", []))
    msg = (
        f"📊 آمار کلی خنگول:\n"
        f"👤 کاربران: {users}\n"
        f"👥 گروه‌ها: {groups}\n"
        f"🧩 جملات: {data['phrases']}\n"
        f"💬 پاسخ‌ها: {data['responses']}\n"
        f"🎭 مود فعلی: {data['mode']}"
    )
    await update.message.reply_text(msg)

async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کامل گروه‌ها — فقط سودو"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه این آمار رو ببینه.")
    await show_group_statistics(update, context)


# ======================= 🧠 هوش‌ها فقط برای سودو =======================

async def show_logical_iq(update: Update):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه درصد هوش رو ببینه.")
    await calculate_logical_iq(update)

async def show_social_iq(update: Update):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه درصد هوش اجتماعی رو ببینه.")
    await calculate_social_iq(update)

async def show_total_iq(update: Update):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه هوش کلی رو بررسی کنه.")
    await calculate_total_iq(update)# ======================= 💬 سیستم ریپلی هوشمند =======================

replies_status = {
    "enabled": True  # پیش‌فرض فعال است
}

async def toggle_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن یا خاموش کردن حالت ریپلی"""
    user_id = update.effective_user.id
    chat = update.effective_chat

    # فقط سودو یا مدیران گروه می‌تونن اینو تغییر بدن
    if not (user_id == ADMIN_ID or await is_group_admin(update, context)):
        return await update.message.reply_text("⛔ فقط مدیران گروه یا سودو مجاز به تغییر ریپلی هستند!")

    replies_status["enabled"] = not replies_status["enabled"]
    state = "✅ حالت ریپلی فعال شد!" if replies_status["enabled"] else "🚫 حالت ریپلی غیرفعال شد!"
    await update.message.reply_text(state)


# ======================= 💭 پاسخ به پیام‌های ریپلای‌شده =======================

async def reply_to_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی کسی به پیام ربات ریپلای کنه، خنگول جواب بده (اگر فعال بود)"""
    if not replies_status["enabled"]:
        return

    message = update.message
    text = message.text.strip().lower() if message.text else ""

    # واکنش‌های خاص
    special_replies = {
        "خنگول کجایی": [
            "اینجام دیگه خنگول 😜",
            "😴 داشتم چرت می‌زدم، چخبر؟",
            "😂 همیشه اینجام، فقط نمی‌خواستم لو برم!",
            "🧠 همین کنارم، باهوش‌تر از همیشه 😎",
            "😅 همین نزدیکی‌ها… مثل همیشه خنگولی!"
        ],
        "کجایی خنگول": [
            "اینجام 😁 چرا دنبالم می‌گردی؟",
            "😂 همین اطرافم، فقط حوصله نداشتم جواب بدم!",
            "😴 یه لحظه رفتم مغزم رو شارژ کنم!",
            "😎 من همیشه آنلاینم، فقط پنهون!"
        ],
        "سلام خنگول": [
            "سلام! 😁 چه خبر از مغزای انسانیا؟",
            "سلام دوست من 🌸",
            "ایول! سلام دوباره 😎",
            "سلاممم، بازم اومدی منو اذیت کنی؟ 😅"
        ]
    }

    # اگه یکی از جملات خاص بود
    for phrase, options in special_replies.items():
        if phrase in text:
            await message.reply_text(random.choice(options))
            return

    # اگر فقط ریپلای معمولی بود
    if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
        responses = [
            "آره؟ 😅",
            "چی گفتی؟ 😜",
            "منظورت با من بود؟ 🤔",
            "عه! داری با من حرف می‌زنی؟ 😆",
            "باشه بابا، من خنگولم دیگه 😁"
        ]
        await message.reply_text(random.choice(responses))


# ======================= 🔗 اتصال هندلرهای جدید =======================

def setup_reply_handlers(app):
    """افزودن هندلرهای ریپلی و کنترلش"""
    app.add_handler(CommandHandler("replymode", toggle_replies))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT & ~filters.COMMAND, reply_to_replies))# ======================= 🚀 خنگول فارسی 9.0 Ultra+ Stable =======================

from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from telegram import Update
import os, random, json, asyncio
from datetime import datetime

# 📦 بارگذاری توابع و تنظیمات پایه
from memory_manager import *
from jokes_manager import *
from fortune_manager import *
from group_manager import *
from ai_learning import *
from smart_reply import *
from emotion_memory import *
from auto_brain.auto_brain import start_auto_brain_loop


TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

status = {
    "active": True,
    "welcome": True
}

replies_status = {"enabled": True}


# ======================= 🧩 ذخیره و بارگذاری فایل =======================
def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ======================= 🧠 سطوح دسترسی =======================
def is_admin(uid):
    return uid == ADMIN_ID

async def is_group_admin(update, context):
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ======================= 💬 دستورات پایه =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 9.0 Ultra+ Stable فعال شد!\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧩 راهنما:\n/start\n/help\n/mode\n/stats\n/fullstats\n"
        "/backup\n/reload\n/reset\n/leave\n/alias\n/replymode\n"
        "و دستورات: جوک، فال، درصد هوش، درصد هوش اجتماعی، هوش کلی"
    )

# ======================= 💭 سیستم ریپلی هوشمند =======================
async def toggle_replies(update, context):
    user_id = update.effective_user.id
    if not (is_admin(user_id) or await is_group_admin(update, context)):
        return await update.message.reply_text("⛔ فقط مدیران گروه یا سودو مجازند.")
    replies_status["enabled"] = not replies_status["enabled"]
    await update.message.reply_text(
        "✅ ریپلی فعال شد!" if replies_status["enabled"] else "🚫 ریپلی غیرفعال شد!"
    )

async def reply_to_replies(update, context):
    if not replies_status["enabled"]:
        return
    text = update.message.text.lower()
    if "خنگول کجایی" in text or "کجایی خنگول" in text:
        reply_text = random.choice([
            "اینجام 😜", "داشتم چرت می‌زدم 😴", "😂 همیشه اینجام!",
            "🧠 همین دور و برم!", "😅 گفتم ببینم دنبالم می‌گردی یا نه!"
        ])
        await update.message.reply_text(reply_text)
        return
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        await update.message.reply_text(random.choice([
            "آره؟ 😅", "منظورت با من بود؟ 😜", "عه! منو صدا کردی؟ 😆", "باشه بابا، من خنگولم 😁"
        ]))

# ======================= 🧩 Alias =======================
ALIASES_FILE = "aliases.json"
def load_aliases():
    return load_data(ALIASES_FILE)
def save_aliases(d): save_data(ALIASES_FILE, d)

async def set_alias(update, context):
    user = update.effective_user.id
    if not (is_admin(user) or await is_group_admin(update, context)):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن alias بسازن.")
    if len(context.args) < 2:
        return await update.message.reply_text("🧩 مثال: `/alias خنده جوک`", parse_mode="Markdown")
    alias, cmd = context.args[0].lower(), " ".join(context.args[1:])
    data = load_aliases(); data[alias] = cmd; save_aliases(data)
    await update.message.reply_text(f"✅ `{alias}` حالا معادل `{cmd}` است!", parse_mode="Markdown")

async def remove_alias(update, context):
    user = update.effective_user.id
    if not (is_admin(user) or await is_group_admin(update, context)):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if not context.args:
        return await update.message.reply_text("❗ استفاده: `/unalias نام`", parse_mode="Markdown")
    data = load_aliases(); name = context.args[0].lower()
    if name in data: del data[name]; save_aliases(data); await update.message.reply_text("🗑️ حذف شد!")
    else: await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

async def check_alias(update, context):
    text = update.message.text.lower().strip()
    data = load_aliases()
    if text in data:
        update.message.text = data[text]
        await reply(update, context)
        return True
    return False

# ======================= 🤖 پاسخ اصلی هوش مصنوعی =======================
async def reply(update, context):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    # در پیوی فقط سودو
    if chat_type == "private" and not is_admin(user_id):
        return

    # بررسی alias
    if await check_alias(update, context):
        return

    # درصد هوش‌ها فقط برای سودو
    if text.lower() in ["درصد هوش", "درصد هوش اجتماعی", "هوش کلی"]:
        if not is_admin(user_id):
            return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه این دستور رو اجرا کنه.")
        if text.lower() == "درصد هوش":
            await update.message.reply_text("🤖 هوش منطقی خنگول: 93% 🧠")
        elif text.lower() == "درصد هوش اجتماعی":
            await update.message.reply_text("👥 هوش اجتماعی خنگول: 88% 💬")
        else:
            await update.message.reply_text("🧩 هوش کلی خنگول: 95% 🚀")
        return

    # دستورات عمومی
    if text == "جوک":
        jokes = ["😂 یه روز خنگول رفت مدرسه...", "🤣 خنگول گفت مغزم هنگ کرده!"]
        return await update.message.reply_text(random.choice(jokes))
    if text == "فال":
        f = ["💫 امروز شاد می‌شی!", "🌙 امشب خوابت پر از ایده‌ست!", "✨ یه سورپرایز در راهه!"]
        return await update.message.reply_text(random.choice(f))

    await update.message.reply_text(random.choice([
        "🙂 جالبه!", "😅 چی گفتی الان؟", "🤖 دارم فکر می‌کنم...", "🧠 باحال بود!", "😂 خنگول هم فهمید!"
    ]))

# ======================= ⚙️ اجرای نهایی =======================
if __name__ == "__main__":
    print("🤖 خنگول 9.0 Ultra+ Stable آماده است!")
    app = ApplicationBuilder().token(TOKEN).build()

    # دستورات اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("alias", set_alias))
    app.add_handler(CommandHandler("unalias", remove_alias))
    app.add_handler(CommandHandler("replymode", toggle_replies))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, reply_to_replies))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # آغاز
    async def on_startup(app):
        await app.bot.send_message(chat_id=ADMIN_ID, text="✅ خنگول 9.0 با موفقیت فعال شد!")
        app.create_task(start_auto_brain_loop(app.bot))
    app.post_init = on_startup

    app.run_polling()
