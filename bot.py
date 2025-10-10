# coding: utf-8
import os
import json
import time
from collections import defaultdict, deque
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# 📦 تنظیمات اصلی
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUDO_ID = int(os.getenv("SUDO_ID", "0"))
DATA_FILE = "data.json"

# نوع قفل‌ها
LOCK_TYPES = {
    "link": "لینک",
    "photo": "عکس",
    "video": "فیلم",
    "sticker": "استیکر",
    "gif": "گیف",
    "file": "فایل",
    "audio": "صوت",
    "contact": "مخاطب",
    "location": "مکان",
    "flood": "اسپم"
}

# فایل داده‌ها
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()
data.setdefault("locks", {})
data.setdefault("warns", {})
data.setdefault("flood", {})

# کنترل flood
flood_tracker = defaultdict(lambda: defaultdict(lambda: deque()))

# بررسی ادمین بودن
async def is_admin(update: Update, user_id: int) -> bool:
    if user_id == SUDO_ID:
        return True
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

# 🚀 دستورات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n"
        "من ربات آنتی‌اسپم فارسی هستم ✅\n"
        "از دستور /help برای دیدن راهنما استفاده کن."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 راهنمای دستورات:\n\n"
        "/start - بررسی فعال بودن ربات\n"
        "/help - راهنما\n"
        "/ghofl <نوع> - قفل نوع خاصی از پیام‌ها (مثلاً: /ghofl link)\n"
        "/bazkardan <نوع|all> - باز کردن قفل\n"
        "/vaziyat - وضعیت قفل‌ها\n"
        "/ban <id یا ریپلای> - بن کردن کاربر\n"
        "/unban <id> - آن‌بن کاربر\n"
        "/silent <id یا ریپلای> [ثانیه] - سایلنت موقت\n"
        "/floodset <تعداد> <ثانیه> - تنظیم محدودیت اسپم (مثلاً /floodset 5 8)"
    )
    await update.message.reply_text(text)

# 🔐 قفل و باز کردن
async def cmd_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ شما ادمین نیستید.")
    args = context.args
    if not args:
        return await update.message.reply_text("مثال: /ghofl link")
    lock_type = args[0].lower()
    if lock_type not in LOCK_TYPES:
        return await update.message.reply_text("نوع قفل نامعتبر است.")
    chat_id = str(update.effective_chat.id)
    locks = set(data["locks"].get(chat_id, []))
    locks.add(lock_type)
    data["locks"][chat_id] = list(locks)
    save_data(data)
    await update.message.reply_text(f"🔒 قفل {LOCK_TYPES[lock_type]} فعال شد.")

async def cmd_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ شما ادمین نیستید.")
    args = context.args
    chat_id = str(update.effective_chat.id)
    if not args:
        return await update.message.reply_text("مثال: /bazkardan link یا /bazkardan all")
    kind = args[0].lower()
    if kind == "all":
        data["locks"][chat_id] = []
        save_data(data)
        return await update.message.reply_text("🔓 همه‌ی قفل‌ها باز شدند.")
    if kind not in LOCK_TYPES:
        return await update.message.reply_text("نوع قفل نامعتبر است.")
    locks = set(data["locks"].get(chat_id, []))
    locks.discard(kind)
    data["locks"][chat_id] = list(locks)
    save_data(data)
    await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[kind]} باز شد.")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    locks = data["locks"].get(chat_id, [])
    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست.")
    text = "🔒 قفل‌های فعال:\n" + "\n".join([f"- {LOCK_TYPES[k]}" for k in locks])
    await update.message.reply_text(text)

# 🧱 عملیات بن، آن‌بن و سایلنت
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین می‌تواند بن کند.")
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
    elif context.args:
        target = int(context.args[0])
    if not target:
        return await update.message.reply_text("به پیام کاربر ریپلای کن یا آیدی بده.")
    await update.effective_chat.ban_member(target)
    await update.message.reply_text(f"🚫 کاربر {target} بن شد.")

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ فقط ادمین می‌تواند آن‌بن کند.")
    if not context.args:
        return await update.message.reply_text("مثال: /unban 123456")
    target = int(context.args[0])
    await update.effective_chat.unban_member(target)
    await update.message.reply_text(f"✅ کاربر {target} آن‌بن شد.")

async def cmd_silent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ شما ادمین نیستید.")
    timeout = 60
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
    elif context.args:
        target = int(context.args[0])
        if len(context.args) > 1:
            timeout = int(context.args[1])
    if not target:
        return await update.message.reply_text("مثال: /silent <id> [زمان]")
    until = int(time.time() + timeout)
    await update.effective_chat.restrict_member(
        user_id=target,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until
    )
    await update.message.reply_text(f"🔇 کاربر {target} برای {timeout} ثانیه سایلنت شد.")

# ⚙️ تنظیم flood
async def set_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ شما ادمین نیستید.")
    if len(context.args) < 2:
        return await update.message.reply_text("مثال: /floodset 5 8")
    limit, period = int(context.args[0]), int(context.args[1])
    chat_id = str(update.effective_chat.id)
    data["flood"][chat_id] = {"limit": limit, "period": period}
    save_data(data)
    await update.message.reply_text(f"تنظیم flood: {limit} پیام در {period} ثانیه.")

# 🧠 بررسی پیام‌ها برای اجرای قفل‌ها
async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    chat_id = str(update.effective_chat.id)
    locks = set(data["locks"].get(chat_id, []))

    # لینک
    if "link" in locks:
        text = (msg.text or msg.caption or "").lower()
        if "http://" in text or "https://" in text or "t.me/" in text:
            await msg.delete()
            return

    # عکس، ویدیو، فایل و ...
    if ("photo" in locks and msg.photo) or \
       ("video" in locks and msg.video) or \
       ("sticker" in locks and msg.sticker) or \
       ("gif" in locks and msg.animation) or \
       ("file" in locks and msg.document) or \
       ("audio" in locks and (msg.audio or msg.voice)) or \
       ("contact" in locks and msg.contact) or \
       ("location" in locks and msg.location):
        await msg.delete()
        return

    # flood
    if "flood" in locks:
        user_id = str(msg.from_user.id)
        limit = int(data["flood"].get(chat_id, {}).get("limit", 5))
        period = int(data["flood"].get(chat_id, {}).get("period", 8))
        dq = flood_tracker[chat_id][user_id]
        now = time.time()
        dq.append(now)
        while dq and dq[0] < now - period:
            dq.popleft()
        if len(dq) > limit:
            await msg.delete()
            await update.effective_chat.restrict_member(
                user_id=msg.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=int(time.time() + 60)
            )

# 🎯 شروع ربات
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN تنظیم نشده است!")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # دستورها (لاتین ولی پاسخ‌ها فارسی)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ghofl", cmd_lock))
    app.add_handler(CommandHandler("bazkardan", cmd_unlock))
    app.add_handler(CommandHandler("vaziyat", cmd_status))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("silent", cmd_silent))
    app.add_handler(CommandHandler("floodset", set_flood))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), on_message))

    print("🤖 ربات آنتی‌اسپم فارسی در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
