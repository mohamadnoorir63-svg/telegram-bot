import os
import json
import asyncio
from typing import Optional
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

# فایل‌های ذخیره‌سازی
ORIGINS_FILE = "origins.json"
TITLES_FILE = "titles.json"

# اگر خواستی آیدی سودوها رو اینجا بذار یا از فایل اصلی بفرستی
SUDO_IDS = [8588347189]


# ---------- کمکی‌های I/O غیرقابل‌بلاک (با to_thread) ----------
async def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    def _sync_read():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return await asyncio.to_thread(_sync_read)


async def _save_json(path: str, data: dict):
    def _sync_write():
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    await asyncio.to_thread(_sync_write)


# ---------- دسترسی: مدیر یا سودو ----------
async def _is_admin_or_sudo(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ---------- وقتی کاربر خودش رو معرفی کرد: پاسخ با دکمه ---------- 
# الگوی ساده: هر پیامی که با این واژه‌ها شروع بشه «معرفی، من هستم، اسمم، اصل:، لقب:»
INTRO_REGEX = r"^(?:معرفی|من هستم|اسمم|اصل:|لقب:)\b"

async def offer_save_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فقط در گروه‌ها کار کن
    chat = update.effective_chat
    msg = update.effective_message
    if not chat or chat.type not in ("group", "supergroup"):
        return

    # متن مناسب ذخیره‌سازی بگیر (می‌تونی فیلترها رو عوض کنی)
    text = (msg.text or msg.caption or "").strip()
    if not text:
        return

    if not filters.Regex(INTRO_REGEX).filter(update):
        return

    # دکمه‌ها یک callback_id حاوی chat_id + message_id + user_id خواهند داشت
    cb_origin = f"save_origin:{chat.id}:{msg.message_id}:{msg.from_user.id}"
    cb_title = f"save_title:{chat.id}:{msg.message_id}:{msg.from_user.id}"

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ ثبت اصل", callback_data=cb_origin),
             InlineKeyboardButton("🏷 ثبت لقب", callback_data=cb_title)]
        ]
    )

    # پاسخ کوتاه که دکمه‌ها رو نمایش می‌ده (اینگونه دسترسی کلیک بعدا چک می‌شه)
    try:
        await msg.reply_text(
            "🔰 اگر این معرفی درست است، مدیران یا سودوها می‌توانند با دکمه زیر آن را ثبت کنند.",
            reply_markup=keyboard
        )
    except:
        pass


# ---------- Callback برای ثبت اصل یا لقب ----------
async def _handle_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # فوری ACK کن

    data = query.data  # مثال: save_origin:<chat_id>:<msg_id>:<user_id>
    parts = data.split(":", 3)
    if len(parts) != 4:
        return

    action, chat_id_s, msg_id_s, target_user_id_s = parts
    chat_id = int(chat_id_s)
    msg_id = int(msg_id_s)
    target_user_id = int(target_user_id_s)

    clicker = query.from_user
    # فقط مدیر یا سودو می‌تونن ثبت کنن
    if not await _is_admin_or_sudo(context, chat_id, clicker.id):
        return await query.edit_message_text("⛔ فقط مدیران یا سودوها می‌توانند ثبت کنند.")

    # تلاش برای گرفتن پیام هدف برای استخراج متن
    try:
        orig_msg = await context.bot.get_chat(chat_id)  # فقط برای اطمینان که چت وجود داره
    except:
        orig_msg = None

    # سعی می‌کنیم متن پیام اصلی را از پیام reply به دکمه (که خودمون ارسال کردیم) پیدا کنیم
    # بهترین راه: خواندن مستقیم پیام اصلی از سرور تلگرام:
    try:
        target_message = await context.bot.get_chat(chat_id)  # placeholder برای عدم خطا
    except:
        target_message = None

    # در واقع ما متن را از طریق get_message نمی‌توانیم مستقیم بگیریم (API محدود)،
    # اما چون callback شامل msg_id بود، می‌تونیم از get_messages استفاده نکنیم.
    # راه ساده: پیامِ اصلی همان پیامی است که کاربر معرفی کرده — از get_chat (خطا) صرف‌نظر می‌کنیم
    # بهتر: از یک approach دیگر استفاده کنیم — متن را در داده‌ی reply_to_message دکمه پیدا کنیم
    # اما چون دکمه روی پیامِ reply ارسال شده است، query.message.reply_to_message ممکن است حاوی آن باشد.
    original_text = None
    # تلاش‌های متعدد برای بازیابی متن پیام اصلی:
    try:
        # اگر پیام دکمه در ریپلای به پیام اصلی ارسال شده باشه:
        if query.message and getattr(query.message, "reply_to_message", None):
            original_text = query.message.reply_to_message.text or query.message.reply_to_message.caption
        else:
            # تلاش جایگزین: بازیابی پیام با get_chat_history وجود نداره؛ بنابراین صرفاً خواندن text از
            # پیامی که ما بهش دکمه اضافه کردیم ممکنه کافی باشه:
            original_text = f"پیامِ معرفی (message_id={msg_id})"
    except:
        original_text = f"پیامِ معرفی (message_id={msg_id})"

    if not original_text:
        original_text = f"معرفی ثبت‌شده (پیام شماره {msg_id})"

    # ذخیره‌سازی در فایل مناسب
    if action == "save_origin":
        data_dict = await _load_json(ORIGINS_FILE)
        data_dict[str(target_user_id)] = original_text
        await _save_json(ORIGINS_FILE, data_dict)
        await query.edit_message_text(f"✅ اصل کاربر ذخیره شد:\n\n{original_text}")
    elif action == "save_title":
        data_dict = await _load_json(TITLES_FILE)
        data_dict[str(target_user_id)] = original_text
        await _save_json(TITLES_FILE, data_dict)
        await query.edit_message_text(f"✅ لقب کاربر ذخیره شد:\n\n{original_text}")
    else:
        await query.edit_message_text("⚠️ عملیات نامشخص است.")


# ---------- نمایش اصل/لقب: ریپلای به پیامِ فرد دیگر یا 'اصل من' / 'لقب من' ----------
async def show_origin_or_title_on_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حالت‌ها:
    - کاربر می‌نویسد 'اصل' و پیامش ریپلای به پیام دیگری است → نمایش اصل آن نفر (اگر داشته باشد)
    - کاربر می‌نویسد 'لقب' و پیامش ریپلای به پیام دیگری است → نمایش لقب آن نفر (اگر داشته باشد)
    - کاربر می‌نویسد 'اصل من' یا 'لقب من' → نمایش داده‌ی خود
    """
    chat = update.effective_chat
    msg = update.effective_message
    text = (msg.text or "").strip()

    if not chat or chat.type not in ("group", "supergroup"):
        return

    lower = text.lower()
    # درخواستِ نمایشِ خودی
    if lower in ("اصل من", "my origin", "اصلمن"):
        data = await _load_json(ORIGINS_FILE)
        val = data.get(str(msg.from_user.id))
        if val:
            await msg.reply_text(f"📜 اصل شما:\n{val}")
        else:
            await msg.reply_text("ℹ️ هیچ «اصل»ی برای شما ثبت نشده.")
        return

    if lower in ("لقب من", "لقبمن"):
        data = await _load_json(TITLES_FILE)
        val = data.get(str(msg.from_user.id))
        if val:
            await msg.reply_text(f"🏷 لقب شما:\n{val}")
        else:
            await msg.reply_text("ℹ️ هیچ «لقب»ی برای شما ثبت نشده.")
        return

    # اگر ریپلای و متن برابر 'اصل' یا 'لقب'
    if msg.reply_to_message and lower in ("اصل", "لقب"):
        target = msg.reply_to_message.from_user
        if not target:
            return
        if lower == "اصل":
            data = await _load_json(ORIGINS_FILE)
            val = data.get(str(target.id))
            if val:
                await msg.reply_text(f"📜 اصل {target.first_name}:\n{val}")
        else:  # لقـب
            data = await _load_json(TITLES_FILE)
            val = data.get(str(target.id))
            if val:
                await msg.reply_text(f"🏷 لقب {target.first_name}:\n{val}")
        return

    # در غیر این صورت چیزی نکن
    return


# ---------- حذف (اختیاری) — فقط برای مدیران/سودو ----------
async def delete_origin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند.")

    if not context.args:
        return await update.message.reply_text("استفاده: /delorigin <user_id>  یا /deltitle <user_id>")

    try:
        uid = str(int(context.args[0]))
    except:
        return await update.message.reply_text("آیدی معتبر وارد کن.")

    data = await _load_json(ORIGINS_FILE)
    if uid in data:
        data.pop(uid)
        await _save_json(ORIGINS_FILE, data)
        await update.message.reply_text("✅ اصل حذف شد.")
    else:
        await update.message.reply_text("⚠️ یافت نشد.")


async def delete_title_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند.")

    if not context.args:
        return await update.message.reply_text("استفاده: /deltitle <user_id>")

    try:
        uid = str(int(context.args[0]))
    except:
        return await update.message.reply_text("آیدی معتبر وارد کن.")

    data = await _load_json(TITLES_FILE)
    if uid in data:
        data.pop(uid)
        await _save_json(TITLES_FILE, data)
        await update.message.reply_text("✅ لقب حذف شد.")
    else:
        await update.message.reply_text("⚠️ یافت نشد.")


# ---------- تابعی که هندلرها رو رجیستر می‌کنه ----------
def register_origin_title_handlers(application, sudo_ids: Optional[list] = None):
    """
    رجیستر هندلرها.
    اگر sudo_ids داده بشه، مقدار پیش‌فرض SUDO_IDS را override می‌کند.
    """
    global SUDO_IDS
    if sudo_ids:
        SUDO_IDS = sudo_ids

    # وقتی کاربر خودش رو معرفی میکنه → پیشنهادی برای ثبت بزن
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(INTRO_REGEX), offer_save_buttons),
        group=5
    )

    # دکمه‌های ثبت اصل/لقب
    application.add_handler(CallbackQueryHandler(_handle_save_callback, pattern=r"^(?:save_origin:|save_title:)"))

    # نمایش اصل/لقب وقتی می‌نویسن 'اصل' / 'لقب' یا 'اصل من' / 'لقب من'
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, show_origin_or_title_on_reply), group=10)

    # فرمان حذف اختیاری برای مدیر
    application.add_handler(CommandHandler("delorigin", delete_origin_cmd))
    application.add_handler(CommandHandler("deltitle", delete_title_cmd))
