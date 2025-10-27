import json
import os
from telegram import Update
from telegram.ext import ContextTypes

# 📁 مسیر فایل سودوها
SUDO_FILE = "sudo_list.json"

# 👑 آیدی مدیر اصلی (اینجا آیدی خودتو بزار)
ADMIN_ID = 7089376754


# ======================= 📂 بارگذاری و ذخیره =======================

def load_sudos():
    """خواندن لیست سودوها از فایل"""
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except:
            pass
    return [ADMIN_ID]


def save_sudos(data):
    """ذخیره لیست سودوها"""
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🧠 لیست سودوهای فعلی
SUDO_IDS = load_sudos()


# ======================= 👑 افزودن سودو =======================

async def add_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه سودو اضافه کنه!")

    if not context.args:
        return await update.message.reply_text("📥 استفاده: /addsudo <ID>")

    try:
        new_id = int(context.args[0])
        if new_id in SUDO_IDS:
            return await update.message.reply_text("⚠️ این کاربر از قبل سودو هست!")

        SUDO_IDS.append(new_id)
        save_sudos(SUDO_IDS)
        await update.message.reply_text(f"✅ کاربر با آیدی <code>{new_id}</code> سودو شد!", parse_mode="HTML")
    except:
        await update.message.reply_text("⚠️ آیدی عددی معتبر بفرست!")


# ======================= 🗑 حذف سودو =======================

async def del_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه حذف کنه!")

    if not context.args:
        return await update.message.reply_text("📥 استفاده: /delsudo <ID>")

    try:
        rem_id = int(context.args[0])
        if rem_id not in SUDO_IDS:
            return await update.message.reply_text("⚠️ این کاربر سودو نیست!")

        SUDO_IDS.remove(rem_id)
        save_sudos(SUDO_IDS)
        await update.message.reply_text(f"🗑️ کاربر با آیدی <code>{rem_id}</code> حذف شد.", parse_mode="HTML")
    except:
        await update.message.reply_text("⚠️ آیدی معتبر بفرست!")


# ======================= 📜 لیست سودوها =======================

async def list_sudos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in [ADMIN_ID, *SUDO_IDS]:
        return await update.message.reply_text("⛔ فقط مدیر اصلی یا سودوها مجازند!")

    text = "👑 <b>لیست سودوهای فعلی:</b>\n\n"
    for i, sid in enumerate(SUDO_IDS, start=1):
        text += f"{i}. <code>{sid}</code>\n"

    await update.message.reply_text(text, parse_mode="HTML")
