import os
import json
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ===========================
# 📁 مسیر درست سازگار با Heroku
# ===========================
FOLDER = "data/dynamic_buttons"
os.makedirs(FOLDER, exist_ok=True)

FILE = os.path.join(FOLDER, "buttons.json")

# اگر فایل وجود نداشت → ساخت خودکار
if not os.path.exists(FILE):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "فال": {"responses": [], "submenu": []},
                "جوک": {"responses": [], "submenu": []}
            },
            f,
            ensure_ascii=False,
            indent=2
        )


# ===========================
# 🔧 لود دکمه‌ها
# ===========================
def load_all():
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ===========================
# 💾 ذخیره دکمه‌ها
# ===========================
def save_all(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===========================
# 🎛 ساخت کیبورد
# ===========================
def build_keyboard():
    data = load_all()
    buttons = list(data.keys())

    if not buttons:
        return ReplyKeyboardMarkup([["هیچ دکمه‌ای نیست"]], resize_keyboard=True)

    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


# ===========================
# /start → کیبورد
# ===========================
async def start_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👇 یکی از گزینه‌ها رو انتخاب کن:",
                                    reply_markup=build_keyboard())


# ===========================
# /addbtn
# ===========================
async def add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /addbtn نام_دکمه")

    name = " ".join(context.args).strip()
    data = load_all()

    if name in data:
        return await update.message.reply_text("⚠️ این دکمه قبلاً وجود دارد!")

    data[name] = {"responses": [], "submenu": []}
    save_all(data)

    await update.message.reply_text(
        f"✅ دکمه <b>{name}</b> ساخته شد!",
        parse_mode="HTML",
        reply_markup=build_keyboard()
    )


# ===========================
# /savebtn
# ===========================
async def save_button_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /savebtn نام_دکمه (روی پیام ریپلای کنید)")

    name = " ".join(context.args).strip()
    data = load_all()

    if name not in data:
        return await update.message.reply_text("⚠️ همچین دکمه‌ای وجود ندارد!")

    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 باید روی پیام ریپلای کنید.")

    entry = {}

    if reply.text:
        entry = {"type": "text", "data": reply.text}

    elif reply.photo:
        entry = {"type": "photo", "file_id": reply.photo[-1].file_id, "caption": reply.caption or ""}

    elif reply.video:
        entry = {"type": "video", "file_id": reply.video.file_id, "caption": reply.caption or ""}

    elif reply.sticker:
        entry = {"type": "sticker", "file_id": reply.sticker.file_id}

    elif reply.audio:
        entry = {"type": "audio", "file_id": reply.audio.file_id}

    elif reply.document:
        entry = {"type": "document", "file_id": reply.document.file_id}

    else:
        return await update.message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شود.")

    data[name]["responses"].append(entry)
    save_all(data)

    await update.message.reply_text(
        f"🎉 پاسخ برای <b>{name}</b> ثبت شد!",
        parse_mode="HTML"
    )


# ===========================
# /delbtn
# ===========================
async def remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /delbtn نام_دکمه")

    name = " ".join(context.args).strip()
    data = load_all()

    if name not in data:
        return await update.message.reply_text("❌ همچین دکمه‌ای وجود ندارد!")

    del data[name]
    save_all(data)

    await update.message.reply_text("🗑 دکمه حذف شد!", reply_markup=build_keyboard())


# ===========================
# /listbtn
# ===========================
async def list_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_all()
    txt = "📌 دکمه‌های فعلی:\n\n" + "\n".join([f"— {b}" for b in data.keys()])
    await update.message.reply_text(txt)


# ===========================
# هندلر کلیک روی دکمه
# ===========================
async def fixed_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    data = load_all()

    if text not in data:
        return

    btn = data[text]

    if not btn["responses"]:
        return await update.message.reply_text("ℹ️ هنوز پاسخی برای این دکمه ثبت نشده.")

    resp = btn["responses"][0]

    t = resp["type"]

    if t == "text":
        return await update.message.reply_text(resp["data"])

    elif t == "photo":
        return await update.message.reply_photo(resp["file_id"], caption=resp.get("caption", ""))

    elif t == "video":
        return await update.message.reply_video(resp["file_id"], caption=resp.get("caption", ""))

    elif t == "sticker":
        return await update.message.reply_sticker(resp["file_id"])

    elif t == "audio":
        return await update.message.reply_audio(resp["file_id"])

    elif t == "document":
        return await update.message.reply_document(resp["file_id"])
