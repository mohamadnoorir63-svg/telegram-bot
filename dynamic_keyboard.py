import os
import json
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

# مسیر ذخیره دکمه‌ها
FOLDER = "backup/dynamic_buttons"
os.makedirs(FOLDER, exist_ok=True)


# -----------------------------
# مسیر فایل هر دکمه
# -----------------------------
def file_path(name):
    safe = name.replace("/", "_")
    return os.path.join(FOLDER, f"{safe}.json")


# -----------------------------
# بارگذاری دکمه
# -----------------------------
def load_button(name):
    path = file_path(name)
    if not os.path.exists(path):
        data = {"name": name, "responses": [], "submenu": []}
        save_button(name, data)
        return data

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"name": name, "responses": [], "submenu": []}


# -----------------------------
# ذخیره دکمه
# -----------------------------
def save_button(name, data):
    path = file_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------------
# گرفتن لیست دکمه‌ها
# -----------------------------
def list_all_buttons():
    return [
        f.replace(".json", "")
        for f in os.listdir(FOLDER)
        if f.endswith(".json")
    ]


# -----------------------------
# ساخت کیبورد اصلی
# -----------------------------
def build_keyboard():
    buttons = list_all_buttons()
    if not buttons:
        return ReplyKeyboardMarkup([["هیچ دکمه‌ای نیست"]], resize_keyboard=True)

    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


# ============================================================
#  /start → نمایش کیبورد
# ============================================================
async def start_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👇 یکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=build_keyboard()
    )


# ============================================================
#  /mkbtn → ساخت دکمه جدید
# ============================================================
async def add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /addbtn نام_دکمه")

    name = " ".join(context.args)
    load_button(name)

    await update.message.reply_text(
        f"✅ دکمه <b>{name}</b> ساخته شد!",
        parse_mode="HTML",
        reply_markup=build_keyboard()
    )


# ============================================================
# /savebtn → ذخیره پاسخ برای دکمه (با ریپلای)
# ============================================================
async def save_button_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /savebtn نام_دکمه (روی پیام ریپلای بده)")

    name = " ".join(context.args)
    data = load_button(name)

    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 باید روی یک پیام ریپلای کنید.")

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

    data["responses"].append(entry)
    save_button(name, data)

    await update.message.reply_text(
        f"🎉 پاسخ ذخیره شد برای دکمه <b>{name}</b>!", parse_mode="HTML"
    )


# ============================================================
# /delbtn → حذف دکمه
# ============================================================
async def remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /delbtn نام_دکمه")

    name = " ".join(context.args)
    path = file_path(name)

    if os.path.exists(path):
        os.remove(path)
        await update.message.reply_text("🗑 دکمه حذف شد!", reply_markup=build_keyboard())
    else:
        await update.message.reply_text("❌ همچین دکمه‌ای وجود ندارد!")


# ============================================================
# /listbtn → لیست دکمه‌ها
# ============================================================
async def list_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = list_all_buttons()
    txt = "📌 دکمه‌های فعلی:\n\n" + "\n".join([f"— {b}" for b in buttons])

    await update.message.reply_text(txt)


# ============================================================
# وقتی کاربر روی دکمه کلیک می‌کند → پاسخ بده
# ============================================================
async def fixed_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    buttons = list_all_buttons()

    if text not in buttons:
        return  # هیچ کاری نکن

    data = load_button(text)
    if not data["responses"]:
        return await update.message.reply_text("ℹ️ هنوز پاسخی برای این دکمه ثبت نشده.")

    resp = data["responses"][0]  # فعلاً اولین پاسخ

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
