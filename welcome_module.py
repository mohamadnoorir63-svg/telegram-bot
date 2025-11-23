# welcome_module.py
# ======================= 👋 سیستم خوشامد جامع برای python-telegram-bot v20+ =======================

from telegram import (
    InlineKeyboardMarkup, InlineKeyboardButton, Update
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler
)
import json, os, asyncio
import jdatetime

WELCOME_FILE = "welcome_settings.json"
SUDO_ID = 8588347189   # ← آیدی سودو رباتت را اینجا بگذار

# ---------------- load / save ----------------
def load_welcome_settings():
    if os.path.exists(WELCOME_FILE):
        try:
            with open(WELCOME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_welcome_settings(data):
    with open(WELCOME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

welcome_settings = load_welcome_settings()

# ---------------- defaults ----------------
DEFAULT_WELCOME_TEXT = (
    "سلام {name} عزیز 🌻\n"
    "به گروه {group} خوش آمدی!\n\n"
    "⏰ ساعت ›› {time}"
)

# ---------------- helper time (Persian) ----------------
def get_persian_time():
    now = jdatetime.datetime.now()
    days = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"]
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر",
        "مرداد", "شهریور", "مهر", "آبان",
        "آذر", "دی", "بهمن", "اسفند"
    ]
    weekday = days[now.weekday()]
    date_str = f"{weekday} {now.day} {months[now.month - 1]} {now.year}"
    time_str = now.strftime("%H:%M")
    return f"{time_str} ( {date_str} )"

# ---------------- keyboard ----------------
def build_welcome_keyboard(main_panel: bool = True):
    last_button = InlineKeyboardButton(
        "❌ بستن پنل", callback_data="welcome_close"
    ) if main_panel else InlineKeyboardButton(
        "🔙 بازگشت", callback_data="welcome_back"
    )

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 فعال‌سازی", callback_data="welcome_enable"),
         InlineKeyboardButton("🔴 غیرفعال‌سازی", callback_data="welcome_disable")],
        [InlineKeyboardButton("📜 تنظیم متن", callback_data="welcome_text"),
         InlineKeyboardButton("🖼 تنظیم رسانه", callback_data="welcome_media")],
        [InlineKeyboardButton("📎 لینک قوانین", callback_data="welcome_rules"),
         InlineKeyboardButton("⏳ حذف خودکار", callback_data="welcome_timer")],
        [InlineKeyboardButton("👀 پیش‌نمایش", callback_data="welcome_preview")],
        [last_button]
    ])

# ---------------- panel open ----------------
async def open_welcome_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_cb = bool(getattr(update, "callback_query", None))
    chat = update.effective_chat
    user = update.effective_user

    # check admin OR sudo
    try:
        if user.id != SUDO_ID:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status not in ["administrator", "creator"]:
                txt = "⛔ فقط مدیران می‌توانند خوشامد را تنظیم کنند!"
                if is_cb:
                    return await update.callback_query.answer(txt, show_alert=True)
                else:
                    return await update.message.reply_text(txt)
    except:
        pass

    cid = str(chat.id)
    welcome_settings.setdefault(cid, {
        "enabled": True,
        "text": DEFAULT_WELCOME_TEXT,
        "media": None,
        "rules": None,
        "delete_after": 0
    })
    save_welcome_settings(welcome_settings)

    panel_text = (
        "👋 <b>پنل تنظیم خوشامد</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "از گزینه‌ها برای تنظیم پیام خوشامد استفاده کن.\n"
        "می‌تونی متن، رسانه، لینک قوانین و زمان حذف رو تنظیم کنی."
    )
    keyboard = build_welcome_keyboard(main_panel=True)

    if is_cb:
        try:
            await update.callback_query.edit_message_text(
                panel_text, parse_mode=ParseMode.HTML, reply_markup=keyboard
            )
        except:
            await context.bot.send_message(
                chat.id, panel_text, parse_mode=ParseMode.HTML, reply_markup=keyboard
            )
    else:
        await update.message.reply_text(panel_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

# ---------------- callback buttons ----------------
async def welcome_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat = query.message.chat
    cid = str(chat.id)
    cfg = welcome_settings.setdefault(cid, {
        "enabled": True, "text": DEFAULT_WELCOME_TEXT, "media": None, "rules": None, "delete_after": 0
    })

    data = query.data

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="welcome_back")]])

    if data == "welcome_back":
        return await open_welcome_panel(update, context)
    if data == "welcome_close":
        try:
            await query.message.edit_text("")
        except:
            try:
                await query.message.delete()
            except:
                pass
        return

    msg = ""
    keyboard = None

    # فعال/غیرفعال
    if data == "welcome_enable":
        cfg["enabled"] = True
        msg = "✅ خوشامد فعال شد."
        keyboard = build_welcome_keyboard(True)

    elif data == "welcome_disable":
        cfg["enabled"] = False
        msg = "🚫 خوشامد غیرفعال شد."
        keyboard = build_welcome_keyboard(True)

    # پیش‌نمایش
    elif data == "welcome_preview":
        now = get_persian_time()
        sample = cfg["text"].format(name="محمد", group=chat.title, time=now)
        msg = f"👀 <b>پیش‌نمایش:</b>\n\n{sample}"
        keyboard = build_welcome_keyboard(True)

    # زیرمنوها
    elif data == "welcome_text":
        context.chat_data["set_mode"] = "text"
        msg = "📜 لطفاً متن جدید خوشامد را ارسال کنید."
        keyboard = back_btn

    elif data == "welcome_media":
        context.chat_data["set_mode"] = "media"
        msg = "🖼 لطفاً رسانه را ارسال کنید."
        keyboard = back_btn

    elif data == "welcome_rules":
        context.chat_data["set_mode"] = "rules"
        msg = "📎 لینک قوانین را ارسال کنید."
        keyboard = back_btn

    elif data == "welcome_timer":
        context.chat_data["set_mode"] = "timer"
        msg = "⏳ عدد ثانیه برای حذف خودکار پیام ارسال کنید."
        keyboard = back_btn

    save_welcome_settings(welcome_settings)

    try:
        await query.message.edit_text(msg, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except:
        pass

# ---------------- handle inputs from panel ----------------
async def welcome_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    cid = str(update.effective_chat.id)
    mode = context.chat_data.get("set_mode")
    if not mode:
        return

    text = update.message.text.strip() if update.message.text else None

    if mode == "text" and text:
        welcome_settings[cid]["text"] = text
        await update.message.reply_text("✅ متن ذخیره شد.")

    elif mode == "rules" and text:
        welcome_settings[cid]["rules"] = text
        await update.message.reply_text("✅ لینک قوانین ذخیره شد.")

    elif mode == "timer" and text:
        try:
            sec = int(text)
            welcome_settings[cid]["delete_after"] = max(0, sec)
            await update.message.reply_text(f"⏳ حذف خودکار: {sec} ثانیه")
        except:
            await update.message.reply_text("⚠️ یک عدد صحیح وارد کنید.")

    # media
    elif mode == "media":
        media_info = None
        msg_type = None

        if update.message.photo:
            media_info = update.message.photo[-1].file_id
            msg_type = "photo"

        elif update.message.video:
            media_info = update.message.video.file_id
            msg_type = "video"

        elif update.message.animation:
            anim = update.message.animation
            media_info = anim.file_id
            msg_type = "animation" if (anim.duration or 0) <= 6 else "video"

        elif update.message.document:
            doc = update.message.document
            media_info = doc.file_id
            msg_type = _type_from_document(doc)

        elif update.message.audio:
            media_info = update.message.audio.file_id
            msg_type = "audio"

        elif update.message.voice:
            media_info = update.message.voice.file_id
            msg_type = "voice"

        elif update.message.sticker:
            media_info = update.message.sticker.file_id
            msg_type = "sticker"

        if not media_info:
            await update.message.reply_text("⚠️ رسانه معتبر نیست.")
            context.chat_data.pop("set_mode", None)
            return

        welcome_settings[cid]["media"] = {"type": msg_type, "file_id": media_info}
        await update.message.reply_text("✅ رسانه خوشامد ذخیره شد.")

    context.chat_data.pop("set_mode", None)
    save_welcome_settings(welcome_settings)

# ---------------- utility: determine type from document mime/filename ----------------
def _type_from_document(document):
    mime = (document.mime_type or "").lower()
    fname = (document.file_name or "").lower()
    if mime.startswith("image/") or fname.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return "photo"
    if mime.startswith("video/") or fname.endswith((".mp4", ".mov", ".mkv", ".webm")):
        return "video"
    if mime.startswith("audio/") or fname.endswith((".mp3", ".m4a", ".ogg", ".wav")):
        return "audio"
    return "document"

# ---------------- safe send ----------------
async def _safe_send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE, m_type, file_id, caption):
    try:
        if m_type == "photo":
            return await update.message.reply_photo(file_id, caption=caption, parse_mode=ParseMode.HTML)
        if m_type == "animation":
            return await update.message.reply_animation(file_id, caption=caption, parse_mode=ParseMode.HTML)
        if m_type == "video":
            return await update.message.reply_video(file_id, caption=caption, parse_mode=ParseMode.HTML)
        if m_type == "audio":
            return await update.message.reply_audio(file_id, caption=caption, parse_mode=ParseMode.HTML)
        if m_type == "voice":
            return await update.message.reply_voice(file_id, caption=caption, parse_mode=ParseMode.HTML)
        if m_type == "sticker":
            return await update.message.reply_sticker(file_id)
        return await update.message.reply_document(file_id, caption=caption, parse_mode=ParseMode.HTML)
    except:
        try:
            return await update.message.reply_document(file_id, caption=caption, parse_mode=ParseMode.HTML)
        except Exception as e:
            print("[WELCOME SEND ERROR]", e)
            return None

# ---------------- welcome handler on new members ----------------
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.effective_chat.id)
    cfg = welcome_settings.get(cid, {"enabled": True})
    if not cfg.get("enabled", True):
        return

    text_tpl = cfg.get("text", DEFAULT_WELCOME_TEXT)
    media = cfg.get("media")
    rules = cfg.get("rules")
    delete_after = cfg.get("delete_after", 0)

    for member in update.message.new_chat_members:
        name = member.first_name or member.username or "کاربر"
        now = get_persian_time()
        message_text = text_tpl.format(name=name, group=update.effective_chat.title or "", time=now)

        if rules:
            message_text += f"\n\n📜 <a href='{rules}'>مشاهده قوانین گروه</a>"

        msg_obj = None
        try:
            if media:
                msg_obj = await _safe_send_welcome(update, context, media["type"], media["file_id"], message_text)
            else:
                msg_obj = await update.message.reply_text(message_text, parse_mode=ParseMode.HTML)

            if delete_after and msg_obj:
                await asyncio.sleep(int(delete_after))
                await context.bot.delete_message(update.effective_chat.id, msg_obj.message_id)
        except Exception as e:
            print("[WELCOME ERROR]", e)

# ---------------- register handlers helper ----------------
def register_welcome_handlers(app, group: int = 20):
    app.add_handler(CallbackQueryHandler(welcome_panel_buttons, pattern="^welcome_"), group=group)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, welcome_input_handler), group=group)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome), group=group)
    app.add_handler(CommandHandler("welcome_panel", open_welcome_panel), group=group)

    async def _save_on_exit(_app):
        save_welcome_settings(welcome_settings)

    try:
        app.post_stop = _save_on_exit
    except:
        pass
