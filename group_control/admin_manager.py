import os
import json
from telegram import Update, ChatAdministratorRights
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")

SUDO_IDS = [8588347189]  # آیدی سودوها (صاحبان ربات)

if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)


# ================= 📁 توابع کمکی =================
def _load_admins():
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_admins(data):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def _has_access(context, chat_id, user_id):
    """بررسی اینکه کاربر دسترسی لازم برای افزودن/حذف مدیر دارد"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ================= ⚙️ مدیریت مدیران گروه =================
async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    text = (msg.text or "").strip()

    if chat.type not in ("group", "supergroup"):
        return

    data = _load_admins()
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = []

    # فقط مدیر یا سودو اجازه دارد
    if text.startswith("افزودن مدیر") or text.startswith("حذف مدیر") or text == "لیست مدیران":
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    # ========== ➕ افزودن مدیر ==========
    if text.startswith("افزودن مدیر"):
        if not msg.reply_to_message:
            return await msg.reply_text("⚠️ باید روی پیام فردی که می‌خواهی مدیر شود ریپلای کنی.")
        target = msg.reply_to_message.from_user

        # اگه از قبل مدیر است
        if target.id in SUDO_IDS:
            return await msg.reply_text("👑 این کاربر سودو است و نیازی به افزودن ندارد.")

        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                privileges=ChatAdministratorRights(
                    can_manage_chat=True,
                    can_change_info=True,
                    can_delete_messages=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_video_chats=True,
                    is_anonymous=False
                )
            )
            if target.id not in data[chat_key]:
                data[chat_key].append(target.id)
                _save_admins(data)
            await msg.reply_text(f"✅ {target.first_name} به‌عنوان مدیر گروه اضافه شد.")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در افزودن مدیر: {e}")

    # ========== ❌ حذف مدیر ==========
    elif text.startswith("حذف مدیر"):
        if not msg.reply_to_message:
            return await msg.reply_text("⚠️ باید روی پیام فردی که می‌خواهی از مدیریت حذف شود ریپلای کنی.")
        target = msg.reply_to_message.from_user

        if target.id in SUDO_IDS:
            return await msg.reply_text("🚫 نمی‌توان سودو را حذف کرد!")

        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                privileges=ChatAdministratorRights(
                    can_manage_chat=False,
                    can_change_info=False,
                    can_delete_messages=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_manage_video_chats=False,
                    is_anonymous=False
                )
            )
            if target.id in data[chat_key]:
                data[chat_key].remove(target.id)
                _save_admins(data)
            await msg.reply_text(f"❌ {target.first_name} از مدیران حذف شد.")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در حذف مدیر: {e}")

    # ========== 📋 لیست مدیران ==========
    elif text == "لیست مدیران":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            lines = []
            for admin in current_admins:
                if not admin.user.is_bot:
                    lines.append(f"• {admin.user.first_name}")
            if lines:
                await msg.reply_text("👑 مدیران فعلی گروه:\n" + "\n".join(lines))
            else:
                await msg.reply_text("ℹ️ هیچ مدیری در گروه یافت نشد.")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در دریافت لیست مدیران: {e}")


# ================= 🔧 ثبت هندلر =================
def register_admin_handlers(application, group_number: int = 15):
    """ثبت هندلر مدیریت مدیران"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_admin_management,
        ),
        group=group_number,
    )
