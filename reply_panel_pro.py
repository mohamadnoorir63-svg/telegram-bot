# ========================= ✳️ Reply Panel Pro++ 8.7.1 (Classic Patrick Full Edition) =========================
# ✅ بدون / در دستور (به جای /reply از "Reply" استفاده کنید)
# ✅ دارای ویرایش پاسخ‌ها (تغییر متن / حذف پاسخ)
# ✅ رفع خطاهای Message is not modified و ذخیره تکراری
# ---------------------------------------------------------------------------------

import os
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

REPLY_FILE = "memory.json"
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ---------------------- 📂 فایل حافظه ----------------------
def load_replies():
    if not os.path.exists(REPLY_FILE):
        return {"replies": {}, "learning": True, "mode": "نرمال", "users": []}
    with open(REPLY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if "replies" not in data:
                data["replies"] = {}
            return data
        except:
            return {"replies": {}, "learning": True, "mode": "نرمال", "users": []}

def save_replies(data):
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------- 🧭 دستور Reply ----------------------
async def add_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه پاسخ جدید بسازه.")

    msg = update.message
    key = msg.text.replace("Reply", "").strip()
    if not key:
        return await msg.reply_text("❗ بنویس: Reply <کلمه>")

    context.user_data.clear()
    context.user_data["reply_key"] = key
    context.user_data["reply_data"] = {"text": [], "media": [], "saved_once": False}
    context.user_data["meta"] = {
        "access": "همه",
        "scope": "گروه",
        "mode": "تصادفی",
        "send_all": True
    }

    await msg.reply_text(
        f"شما اکنون در حال ساخت پاسخ شخصی برای «{key}» هستید\n\n"
        "- انتخاب کنید چه کسانی می‌توانند دستور را فراخوانی کنند\n"
        "- انتخاب کنید که ریلِی ربات به کجا ارسال شود\n"
        "- مشخص کنید که همه ریلِی‌ها باهم ارسال شوند یا فقط یکی تصادفی\n\n"
        "گزینه‌های انتخاب‌شده با حروف بزرگ نشان داده شده‌اند",
        reply_markup=InlineKeyboardMarkup(build_panel(context.user_data["meta"]))
    )

# ---------------------- 🎛 ساخت پنل ----------------------
def build_panel(meta):
    def mark(key, value):
        return "✅" if meta.get(key) == value else ""

    return [
        [
            InlineKeyboardButton(f"همه {mark('access','همه')}", callback_data="access_همه"),
            InlineKeyboardButton(f"ادمین {mark('access','ادمین')}", callback_data="access_ادمین")
        ],
        [
            InlineKeyboardButton(f"گروه {mark('scope','گروه')}", callback_data="scope_گروه"),
            InlineKeyboardButton(f"شخصی {mark('scope','شخصی')}", callback_data="scope_شخصی")
        ],
        [
            InlineKeyboardButton(f"تصادفی {mark('mode','تصادفی')}", callback_data="mode_تصادفی"),
            InlineKeyboardButton(f"ارسال برای همه {mark('mode','ارسال برای همه')}", callback_data="mode_ارسال برای همه")
        ],
        [
            InlineKeyboardButton("✏️ ویرایش پاسخ‌ها", callback_data="edit_menu"),
            InlineKeyboardButton("💾 ذخیره", callback_data="save_reply")
        ],
        [InlineKeyboardButton("🗑 حذف", callback_data="cancel")]
    ]

# ---------------------- ⚙️ دکمه‌ها ----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "meta" not in context.user_data:
        return await query.edit_message_text("⛔ ابتدا باید Reply اجرا شود.")

    meta = context.user_data["meta"]
    data = load_replies()

    # تغییر تنظیمات
    if "_" in query.data:
        group, value = query.data.split("_", 1)
        if group in ["access", "scope", "mode"]:
            meta[group] = value

        new_markup = InlineKeyboardMarkup(build_panel(meta))
        old_markup = query.message.reply_markup
        if not old_markup or old_markup.to_dict() != new_markup.to_dict():
            await query.edit_message_reply_markup(new_markup)
        return

    # ذخیره پاسخ
    if query.data == "save_reply":
        key = context.user_data["reply_key"]
        reply_data = context.user_data["reply_data"]
        reply_data.update(meta)

        if key not in data["replies"]:
            data["replies"][key] = []
        data["replies"][key].append(reply_data)
        save_replies(data)
        context.user_data.clear()
        await query.edit_message_text(f"✅ پاسخ '{key}' با موفقیت ذخیره شد!")
        return

    # منوی ویرایش
    if query.data == "edit_menu":
        replies = data.get("replies", {})
        if not replies:
            return await query.edit_message_text("ℹ️ هنوز هیچ پاسخی ثبت نشده.")
        keyboard = []
        for key in replies.keys():
            keyboard.append([InlineKeyboardButton(f"🧩 {key}", callback_data=f"edit_{key}")])
        await query.edit_message_text(
            "📋 یکی از کلیدها را برای ویرایش انتخاب کن 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # لغو
    if query.data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ عملیات لغو شد.")
        return

# ---------------------- 📨 دریافت پیام‌ها ----------------------
async def message_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "reply_key" not in context.user_data:
        return

    msg = update.message
    reply_data = context.user_data["reply_data"]

    if reply_data.get("saved_once"):
        return

    if msg.text:
        reply_data["text"].append(msg.text.strip())
    elif msg.photo:
        reply_data["media"].append(("photo", msg.photo[-1].file_id))
    elif msg.video:
        reply_data["media"].append(("video", msg.video.file_id))
    elif msg.audio:
        reply_data["media"].append(("audio", msg.audio.file_id))
    elif msg.voice:
        reply_data["media"].append(("voice", msg.voice.file_id))
    elif msg.sticker:
        reply_data["media"].append(("sticker", msg.sticker.file_id))
    elif msg.video_note:
        reply_data["media"].append(("video_note", msg.video_note.file_id))

    reply_data["saved_once"] = True
    await msg.reply_text("✅ پیام برای پاسخ ذخیره شد. حالا از پنل پایین تنظیم کن 👇")
    # ---------------------- 💬 پاسخ خودکار ----------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    data = load_replies()
    user = update.effective_user
    chat = update.effective_chat

    if text not in data["replies"]:
        return

    replies = []
    for entry in data["replies"][text]:
        if entry.get("access") == "ادمین" and user.id != ADMIN_ID:
            continue
        if entry.get("scope") == "شخصی" and chat.type != "private":
            continue
        if entry.get("scope") == "گروه" and chat.type == "private":
            continue
        replies.append(entry)

    if not replies:
        return

    entry = random.choice(replies)
    reply_text = "\n".join(entry.get("text", [])) if entry.get("text") else ""
    media = entry.get("media", [])

    if entry.get("mode") == "ارسال برای همه":
        for t in entry.get("text", []):
            await msg.reply_text(t)
        for mtype, fid in media:
            await send_media(msg, mtype, fid)
    else:
        if media:
            mtype, fid = random.choice(media)
            await send_media(msg, mtype, fid, reply_text)
        elif reply_text:
            await msg.reply_text(reply_text)

# ---------------------- 🖼 ارسال مدیا ----------------------
async def send_media(msg, mtype, fid, caption=None):
    if mtype == "photo":
        await msg.reply_photo(fid, caption=caption or None)
    elif mtype == "video":
        await msg.reply_video(fid, caption=caption or None)
    elif mtype == "audio":
        await msg.reply_audio(fid, caption=caption or None)
    elif mtype == "voice":
        await msg.reply_voice(fid, caption=caption or None)
    elif mtype == "sticker":
        await msg.reply_sticker(fid)
    elif mtype == "video_note":
        await msg.reply_video_note(fid)

# ---------------------- ✏️ ویرایش پاسخ ----------------------
async def start_edit_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل ویرایش پاسخ‌های ذخیره‌شده"""
    query = update.callback_query
    await query.answer()

    data = load_replies()
    replies = data.get("replies", {})
    user = query.from_user

    if user.id != ADMIN_ID:
        return await query.edit_message_text("⛔ فقط مدیر مجازه.")

    key = query.data.replace("edit_", "").strip()
    if key not in replies or not replies[key]:
        return await query.edit_message_text("⚠️ هیچ پاسخی برای این کلید پیدا نشد!")

    context.user_data["edit_key"] = key
    context.user_data["edit_index"] = 0

    current = replies[key][0]
    text_block = "\n".join(current.get("text", [])) if current.get("text") else "— بدون متن —"

    txt = (
        f"🧩 <b>ویرایش پاسخ:</b> {key}\n\n"
        f"📝 <b>متن فعلی:</b>\n{text_block}\n\n"
        f"🎛 <b>تنظیمات:</b>\n"
        f"👥 دسترسی: {current.get('access','همه')}\n"
        f"📍 محدوده: {current.get('scope','هر دو')}\n"
        f"🎲 حالت: {current.get('mode','تصادفی')}"
    )

    keyboard = [
        [InlineKeyboardButton("✏️ تغییر متن", callback_data=f"change_text_{key}")],
        [InlineKeyboardButton("🗑 حذف پاسخ", callback_data=f"delete_reply_{key}")],
        [InlineKeyboardButton("⬅️ بازگشت", callback_data="edit_menu")]
    ]

    await query.edit_message_text(txt, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------------- 🗑 حذف پاسخ ----------------------
async def handle_delete_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_replies()
    key = query.data.replace("delete_reply_", "").strip()

    if key in data.get("replies", {}):
        del data["replies"][key]
        save_replies(data)
        await query.edit_message_text(f"🗑 پاسخ '{key}' با موفقیت حذف شد.")
    else:
        await query.edit_message_text("⚠️ پاسخی برای حذف پیدا نشد!")

# ---------------------- 📝 تغییر متن پاسخ ----------------------
async def handle_change_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("change_text_", "").strip()
    context.user_data["await_new_text"] = key
    await query.edit_message_text(
        f"✏️ لطفاً متن جدید پاسخ برای «{key}» را ارسال کن.\n\n📨 فقط متن ساده بفرست."
    )

# ---------------------- 💾 دریافت متن جدید و ذخیره ----------------------
async def handle_new_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "await_new_text" not in context.user_data:
        return

    key = context.user_data.pop("await_new_text")
    data = load_replies()

    if key not in data["replies"]:
        return await update.message.reply_text("⚠️ کلید پاسخ پیدا نشد!")

    new_text = update.message.text.strip()
    if not new_text:
        return await update.message.reply_text("❗ لطفاً فقط متن بفرست.")

    # جایگزینی اولین پاسخ متنی
    data["replies"][key][0]["text"] = [new_text]
    save_replies(data)

    await update.message.reply_text(f"✅ متن پاسخ «{key}» با موفقیت به‌روزرسانی شد!")

# ---------------------- ⚙️ ثبت هندلرهای ویرایش ----------------------
def register_edit_handlers(app):
    app.add_handler(CallbackQueryHandler(start_edit_reply, pattern="^edit_"))
    app.add_handler(CallbackQueryHandler(handle_delete_reply, pattern="^delete_reply_"))
    app.add_handler(CallbackQueryHandler(handle_change_text, pattern="^change_text_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_text))
