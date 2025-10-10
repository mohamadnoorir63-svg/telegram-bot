# coding: utf-8
import os
import json
import time
from collections import defaultdict, deque
from typing import Dict, Any

from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

DATA_FILE = "data.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUDO_ID = int(os.getenv("SUDO_ID", "0"))  # آیدی عددی مالک اصلی

# نوع‌های قابل قفل (کلیدها فارسی)
VALID_LOCKS = {
    "لینک": "links",
    "عکس": "photo",
    "فیلم": "video",
    "استیکر": "sticker",
    "گیف": "gif",
    "فایل": "file",
    "صوت": "audio",
    "مخاطب": "contact",
    "مکان": "location",
    "flood": "flood"  # کنترل ارسال مکرر
}

# بارگذاری / ذخیره داده‌ها (ساده، مبتنی بر فایل)
def load_data() -> Dict[str, Any]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(d: Dict[str, Any]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

data = load_data()
# ساختار data:
# data = {
#   "locks": { "<chat_id>": ["links", "photo", ..."], ... },
#   "mods": { "<chat_id>": [<mod_id>, ...] },
#   "warns": { "<chat_id>": { "<user_id>": count } },
#   "flood": { "<chat_id>": {"limit": 5, "period": 8} }
# }

data.setdefault("locks", {})
data.setdefault("mods", {})
data.setdefault("warns", {})
data.setdefault("flood", {})

# برای کنترل flood در حافظه (برای کارآیی)
flood_tracker: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque()))

# کمک: بررسی اینکه آیا کاربر مدیر است (SUDO یا در لیست mods یا مدیر گروه)
async def is_admin(update: Update, user_id: int) -> bool:
    if user_id == SUDO_ID:
        return True
    chat = update.effective_chat
    if not chat:
        return False
    # بررسی لیست ذخیره شده
    mods = [int(x) for x in data.get("mods", {}).get(str(chat.id), [])]
    if user_id in mods:
        return True
    # بررسی رسمی از طریق API
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

# دستورها (فارسی)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n"
        "ربات آنتی‌اسپم روشن است.\n"
        "برای راهنما /help را بفرستید."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "دستورات (فارسی):\n\n"
        "/help - نمایش راهنما\n"
        "/قفل <نوع> - فعال کردن قفل (مثال: /قفل لینک)\n"
        "/بازکردن <نوع|همه> - غیرفعال کردن قفل\n"
        "/وضعیت - نمایش وضعیت قفل‌ها\n"
        "/اضافه_مدیر <آیدی> - اضافه کردن مدیر (SUDO فقط)\n"
        "/حذف_مدیر <آیدی> - حذف مدیر (SUDO فقط)\n"
        "/بن <reply یا آیدی> - بن کردن کاربر (مدیرها)\n"
        "/آنبن <آیدی> - آنبن کردن کاربر (مدیرها)\n"
        "/سایلنت <reply یا آیدی> [ثانیه] - سایلنت موقت (مدیرها)\n"
    )
    await update.message.reply_text(text)

# تبدیل نام فارسی نوع به کلید داخلی
def lock_name_to_key(name: str):
    name = name.strip()
    return VALID_LOCKS.get(name)

# قفل کردن
async def cmd_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(update, user.id):
        return await update.message.reply_text("⛔ شما دسترسی لازم را ندارید.")
    args = context.args
    if not args:
        return await update.message.reply_text("لطفاً نوع قفل را بعد از دستور وارد کنید. مثال: /قفل لینک")
    kind_arg = args[0]
    key = lock_name_to_key(kind_arg)
    if not key:
        return await update.message.reply_text("نوع قفل معتبر نیست. مثال‌ها: لینک، عکس، فیلم، استیکر، گیف، فایل، صوت، مخاطب، مکان، flood")
    chat_id = str(update.effective_chat.id)
    locks = set(data["locks"].get(chat_id, []))
    if key in locks:
        return await update.message.reply_text(f"⚠️ قفل «{kind_arg}» قبلاً فعال شده است.")
    locks.add(key)
    data["locks"][chat_id] = list(locks)
    save_data(data)
    await update.message.reply_text(f"🔒 قفل «{kind_arg}» فعال شد.")

# باز کردن قفل
async def cmd_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(update, user.id):
        return await update.message.reply_text("⛔ شما دسترسی لازم را ندارید.")
    args = context.args
    if not args:
        return await update.message.reply_text("لطفاً نوع قفل یا 'همه' را وارد کنید. مثال: /بازکردن لینک")
    kind_arg = args[0]
    chat_id = str(update.effective_chat.id)
    if kind_arg == "همه":
        data["locks"][chat_id] = []
        save_data(data)
        return await update.message.reply_text("🔓 تمام قفل‌ها برداشته شد.")
    key = lock_name_to_key(kind_arg)
    if not key:
        return await update.message.reply_text("نوع قفل معتبر نیست.")
    locks = set(data["locks"].get(chat_id, []))
    if key not in locks:
        return await update.message.reply_text(f"⚠️ قفل «{kind_arg}» فعال نیست.")
    locks.remove(key)
    data["locks"][chat_id] = list(locks)
    save_data(data)
    await update.message.reply_text(f"🔓 قفل «{kind_arg}» غیرفعال شد.")

# وضعیت قفل‌ها
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    locks = data["locks"].get(chat_id, [])
    if not locks:
        await update.message.reply_text("🔓 هیچ قفلی فعال نیست.")
        return
    # برگرداندن اسم‌های فارسی
    inv = {v: k for k, v in VALID_LOCKS.items()}
    active = [inv.get(k, k) for k in locks]
    await update.message.reply_text("🔒 قفل‌های فعال:\n" + "، ".join(active))

# اضافه/حذف مدیر (فقط SUDO)
async def cmd_add_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != SUDO_ID:
        return await update.message.reply_text("⛔ فقط SUDO می‌تواند این کار را انجام دهد.")
    args = context.args
    if not args:
        return await update.message.reply_text("آیدی را بعد از دستور وارد کن: /اضافه_مدیر 123456")
    try:
        uid = int(args[0])
    except:
        return await update.message.reply_text("آیدی باید عددی باشد.")
    chat_id = str(update.effective_chat.id)
    mods = set(data["mods"].get(chat_id, []))
    mods.add(uid)
    data["mods"][chat_id] = list(mods)
    save_data(data)
    await update.message.reply_text(f"✅ کاربر {uid} به عنوان مدیر محلی اضافه شد.")

async def cmd_remove_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != SUDO_ID:
        return await update.message.reply_text("⛔ فقط SUDO می‌تواند این کار را انجام دهد.")
    args = context.args
    if not args:
        return await update.message.reply_text("آیدی را بعد از دستور وارد کن: /حذف_مدیر 123456")
    try:
        uid = int(args[0])
    except:
        return await update.message.reply_text("آیدی باید عددی باشد.")
    chat_id = str(update.effective_chat.id)
    mods = set(data["mods"].get(chat_id, []))
    if uid in mods:
        mods.remove(uid)
        data["mods"][chat_id] = list(mods)
        save_data(data)
        await update.message.reply_text(f"✅ کاربر {uid} از مدیران حذف شد.")
    else:
        await update.message.reply_text("آن کاربر مدیر محلی نیست.")

# بن کردن
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ شما دسترسی ندارید.")
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target = int(context.args[0])
        except:
            pass
    if not target:
        return await update.message.reply_text("لطفاً به پیام کاربر ریپلای کن یا آیدی کاربر را وارد کن.")
    try:
        await update.effective_chat.ban_member(target)
        await update.message.reply_text(f"✅ کاربر {target} بن شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا در بن کردن: {e}")

# آنبن
async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ شما دسترسی ندارید.")
    if not context.args:
        return await update.message.reply_text("آیدی کاربر را وارد کن: /آنبن 123456")
    try:
        target = int(context.args[0])
    except:
        return await update.message.reply_text("آیدی معتبر نیست.")
    try:
        await update.effective_chat.unban_member(target)
        await update.message.reply_text(f"✅ کاربر {target} آنبن شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا در آنبن: {e}")

# سایلنت (موقت)
async def cmd_silent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ شما دسترسی ندارید.")
    timeout = 3600  # پیش فرض 1 ساعت
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target = int(context.args[0])
            if len(context.args) > 1:
                timeout = int(context.args[1])
        except:
            pass
    if not target:
        return await update.message.reply_text("لطفاً به پیام کاربر ریپلای کن یا آیدی کاربر + مدت (ثانیه) وارد کن.")
    try:
        until = int(time.time() + timeout)
        await update.effective_chat.restrict_member(
            user_id=target,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        await update.message.reply_text(f"🔇 کاربر {target} به مدت {timeout} ثانیه سایلنت شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا در سایلنت: {e}")

# بررسی پیام‌ها و اعمال قفل‌ها (محور اصلی)
async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not update.effective_chat:
        return
    chat_id = str(update.effective_chat.id)
    locks = set(data["locks"].get(chat_id, []))

    # 1) flood کنترل
    if "flood" in locks:
        cfg = data.get("flood", {}).get(chat_id, {"limit": 5, "period": 8})
        limit = int(cfg.get("limit", 5))
        period = int(cfg.get("period", 8))
        user_id = str(msg.from_user.id)
        dq = flood_tracker[chat_id][user_id]
        now = time.time()
        dq.append(now)
        # تمیز کردن زمان‌های قدیمی
        while dq and dq[0] < now - period:
            dq.popleft()
        if len(dq) > limit:
            # عمل: حذف پیام و در صورت نیاز اخطار یا بن
            try:
                await msg.delete()
            except:
                pass
            # افزایش شمار تخلفات
            warns_chat = data["warns"].setdefault(chat_id, {})
            warns_chat[user_id] = warns_chat.get(user_id, 0) + 1
            save_data(data)
            if warns_chat[user_id] >= 3:
                # بن موقت به عنوان مثال
                try:
                    await update.effective_chat.ban_member(int(user_id))
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"کاربر {user_id} به دلیل ارسال مکرر بن شد.")
                except:
                    pass
            return

    # 2) لینک
    if "links" in locks:
        has_link = False
        if msg.entities:
            for e in msg.entities:
                if e.type in ("url", "text_link"):
                    has_link = True
                    break
        text = (msg.text or msg.caption or "") or ""
        if "t.me/" in text or "telegram.me/" in text:
            has_link = True
        if has_link:
            try:
                await msg.delete()
            except:
                pass
            return

    # 3) عکس
    if "photo" in locks and msg.photo:
        try:
            await msg.delete()
        except:
            pass
        return

    # 4) ویدیو
    if "video" in locks and msg.video:
        try:
            await msg.delete()
        except:
            pass
        return

    # 5) استیکر
    if "sticker" in locks and msg.sticker:
        try:
            await msg.delete()
        except:
            pass
        return

    # 6) گیف (animation)
    if "gif" in locks and msg.animation:
        try:
            await msg.delete()
        except:
            pass
        return

    # 7) فایل (document)
    if "file" in locks and msg.document:
        try:
            await msg.delete()
        except:
            pass
        return

    # 8) صوت / ویس
    if "audio" in locks and (msg.audio or msg.voice):
        try:
            await msg.delete()
        except:
            pass
        return

    # 9) مخاطب
    if "contact" in locks and msg.contact:
        try:
            await msg.delete()
        except:
            pass
        return

    # 10) مکان
    if "location" in locks and msg.location:
        try:
            await msg.delete()
        except:
            pass
        return

# فرمان تنظیم flood (SUDO یا مدیر)
async def set_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, update.effective_user.id):
        return await update.message.reply_text("⛔ شما دسترسی ندارید.")
    args = context.args
    if len(args) < 2:
        return await update.message.reply_text("استفاده: /تنظیم_flood <limit> <period_ثانیه>  مثال: /تنظیم_flood 5 8")
    try:
        limit = int(args[0])
        period = int(args[1])
    except:
        return await update.message.reply_text("مقادیر باید عددی باشند.")
    chat_id = str(update.effective_chat.id)
    data.setdefault("flood", {})
    data["flood"][chat_id] = {"limit": limit, "period": period}
    save_data(data)
    await update.message.reply_text(f"تنظیم flood ثبت شد: {limit} پیام در {period} ثانیه.")

# راه‌اندازی اپ
def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN تنظیم نشده است!")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("قفل", cmd_lock))
    app.add_handler(CommandHandler("بازکردن", cmd_unlock))
    app.add_handler(CommandHandler("وضعیت", cmd_status))
    app.add_handler(CommandHandler("اضافه_مدیر", cmd_add_mod))
    app.add_handler(CommandHandler("حذف_مدیر", cmd_remove_mod))
    app.add_handler(CommandHandler("بن", cmd_ban))
    app.add_handler(CommandHandler("آنبن", cmd_unban))
    app.add_handler(CommandHandler("سایلنت", cmd_silent))
    app.add_handler(CommandHandler("تنظیم_flood", set_flood))

    # دریافت همه پیام‌ها برای بررسی قفل‌ها
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), on_message))

    print("ربات آنتی‌اسپم فارسی در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
