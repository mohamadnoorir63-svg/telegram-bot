import json
import os
from telegram import Update
from telegram.ext import ContextTypes

# 📁 مسیر فایل سودوها
SUDO_FILE = "sudo_list.json"

# 👑 آیدی مدیر اصلی (عدد خودتو بذار اینجا)
ADMIN_ID = 7089376754


# ======================= 📂 بارگذاری و ذخیره =======================

def load_sudos():
    """خواندن لیست سودوها از فایل"""
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except:
            pass

    # اگر فایل وجود نداشت، فقط مدیر اصلی رو اضافه کن
    return {str(ADMIN_ID): "مدیر اصلی"}


def save_sudos(data):
    """ذخیره لیست سودوها"""
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🧠 لیست فعلی سودوها
SUDO_DATA = load_sudos()


# ======================= 👑 افزودن سودو =======================

async def add_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه سودو اضافه کنه!")

    if len(context.args) < 2:
        return await update.message.reply_text("📥 استفاده: /addsudo <ID> <لقب>")

    try:
        new_id = int(context.args[0])
        title = " ".join(context.args[1:])

        if str(new_id) in SUDO_DATA:
            return await update.message.reply_text("⚠️ این کاربر از قبل سودو هست!")

        SUDO_DATA[str(new_id)] = title
        save_sudos(SUDO_DATA)

        await update.message.reply_text(
            f"✅ کاربر با آیدی <code>{new_id}</code> با لقب «{title}» سودو شد!",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در افزودن سودو: {e}")


# ======================= 🗑 حذف سودو =======================

async def del_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه سودو حذف کنه!")

    if not context.args:
        return await update.message.reply_text("📥 استفاده: /delsudo <ID>")

    try:
        rem_id = str(int(context.args[0]))
        if rem_id not in SUDO_DATA:
            return await update.message.reply_text("⚠️ این آیدی در لیست سودوها نیست!")

        title = SUDO_DATA.pop(rem_id)
        save_sudos(SUDO_DATA)

        await update.message.reply_text(
            f"🗑️ کاربر با آیدی <code>{rem_id}</code> و لقب «{title}» حذف شد.",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف سودو: {e}")


# ======================= 📜 لیست سودوها =======================

async def list_sudos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # فقط مدیر اصلی یا سودوها
    if str(user.id) not in SUDO_DATA and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی یا سودوها مجازند!")

    text = "👑 <b>لیست سودوهای فعلی:</b>\n\n"
    for i, (uid, title) in enumerate(SUDO_DATA.items(), start=1):
        text += f"{i}. <b>{title}</b> — <code>{uid}</code>\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ======================= ⚙️ ابزارهای دسترسی =======================

def get_sudo_ids():
    """برگرداندن آیدی همه سودوها به‌صورت عددی"""
    return [int(uid) for uid in SUDO_DATA.keys()]


def is_sudo(user_id):
    """بررسی سودو بودن"""
    return str(user_id) in SUDO_DATA or user_id == ADMIN_ID
