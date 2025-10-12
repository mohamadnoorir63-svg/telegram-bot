import json
import os
from datetime import datetime
from telegram import Update

# 📁 مسیر فایل داده گروه‌ها
GROUP_FILE = "group_data.json"


# ======================= 📦 مدیریت فایل =======================

def _init_group_file():
    """اگر فایل وجود نداشت بسازش."""
    if not os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def _load_groups():
    """داده‌های گروه‌ها رو بخونه."""
    _init_group_file()
    with open(GROUP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_groups(data):
    """ذخیره تغییرات گروه‌ها در فایل."""
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ======================= 👋 خوش‌آمد =======================

async def welcome_member(update: Update, context):
    """ارسال پیام خوش‌آمد برای عضو جدید."""
    chat_id = update.message.chat_id
    groups = _load_groups()

    # تنظیمات پیش‌فرض اگر نبود
    if str(chat_id) not in groups:
        groups[str(chat_id)] = {"welcome_enabled": True}
        _save_groups(groups)

    if not groups[str(chat_id)]["welcome_enabled"]:
        return

    for member in update.message.new_chat_members:
        t = datetime.now().strftime("%H:%M")
        d = datetime.now().strftime("%Y-%m-%d")
        try:
            await update.message.reply_sticker("CAACAgIAAxkBAAEIBbVkn3IoRh6EPUbE4a7yR1yMG-4aFAACWQADVp29Cmb0vh8k0JtbNgQ")
        except Exception:
            pass

        msg = (
            f"🎉 خوش اومدی {member.first_name}!\n"
            f"🕒 ساعت: {t}\n📅 تاریخ: {d}\n🏠 گروه: {update.message.chat.title}\n"
            f"😄 خوش بگذره!"
        )
        await update.message.reply_text(msg)


# ======================= ⚙️ تغییر وضعیت خوش‌آمد =======================

async def toggle_welcome(update: Update, context):
    """روشن یا خاموش کردن خوش‌آمد در گروه."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    groups = _load_groups()

    # فقط مدیر یا سودو
    try:
        member = await context.bot.get_chat_member(chat_id, user.id)
        is_admin = member.status in ["administrator", "creator"]
    except Exception:
        is_admin = False

    if not (is_admin or user.id == 7089376754):
        return await update.message.reply_text("⛔ فقط مدیر گروه یا سودو می‌تونه خوش‌آمد رو تغییر بده!")

    if str(chat_id) not in groups:
        groups[str(chat_id)] = {"welcome_enabled": True}

    groups[str(chat_id)]["welcome_enabled"] = not groups[str(chat_id)]["welcome_enabled"]
    _save_groups(groups)

    if groups[str(chat_id)]["welcome_enabled"]:
        await update.message.reply_text("👋 پیام خوش‌آمد فعال شد!")
    else:
        await update.message.reply_text("🚫 پیام خوش‌آمد غیرفعال شد!")


# ======================= 🚪 خروج از گروه =======================

async def leave_group(update: Update, context):
    """خروج ربات از گروه (فقط سودو)."""
    if update.effective_user.id != 7089376754:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه منو بیرون بفرسته!")

    await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
    await context.bot.leave_chat(update.effective_chat.id)


# ======================= 📊 آمار گروه =======================

async def group_stats(update: Update, context):
    """نمایش تعداد گروه‌هایی که ربات توش فعاله."""
    if update.effective_user.id != 7089376754:
        return

    groups = _load_groups()
    count = len(groups)
    enabled = sum(1 for g in groups.values() if g.get("welcome_enabled", False))
    await update.message.reply_text(f"📊 من در {count} گروه هستم.\n👋 خوش‌آمد فعال در {enabled} گروه.")


# ======================= 📦 راه‌اندازی اولیه =======================

def init_group_data():
    """فراخوانی اولیه هنگام اجرای ربات."""
    _init_group_file()
