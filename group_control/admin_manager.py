import os
import json
import re
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

# ========================= تنظیمات اولیه =========================
BOT_TOKEN = "توکن_ربات_اصلی_اینجا_بگذار"
SUDO_IDS = [8588347189]  # ایدی عددی سودوها

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")
CUSTOM_CMD_FILE = os.path.join(BASE_DIR, "custom_commands.json")

# ساخت فایل‌ها در صورت عدم وجود
for f in (ADMINS_FILE, CUSTOM_CMD_FILE):
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as x:
            json.dump({}, x, ensure_ascii=False, indent=2)

# ========================= توابع کمکی =========================
def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def _has_access(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

async def _bot_can_promote(context, chat_id):
    try:
        me = await context.bot.get_chat_member(chat_id, context.bot.id)
        return me.status == "creator" or getattr(me, "can_promote_members", False)
    except:
        return False

async def _get_target_user(update: Update, context, text: str):
    msg = update.effective_message
    chat_id = update.effective_chat.id

    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None

    parts = text.split()
    if len(parts) >= 2:
        identifier = parts[1]
        try:
            if identifier.startswith("@"):
                user = await context.bot.get_chat_member(chat_id, identifier)
                return user.user, None
            else:
                user_id = int(identifier)
                user = await context.bot.get_chat_member(chat_id, user_id)
                return user.user, None
        except:
            return None, identifier
    return None, None

async def _send_temp_message(msg, text, context, delete_after=10):
    sent = await msg.reply_text(text, parse_mode="HTML")
    asyncio.create_task(_delete_after(sent, delete_after, context))

async def _delete_after(message, delay, context):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

# ========================= هندلر اصلی =========================
async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    text = (msg.text or "").strip()

    if chat.type not in ("group", "supergroup") or not text:
        return

    data = _load_json(ADMINS_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = []

    # ===== افزودن مدیر =====
    if text.startswith("افزودن مدیر"):
        target, mention_failed = await _get_target_user(update, context, text)
        if not target:
            await _send_temp_message(msg, "⚠️ کاربر مشخص نشد. روی پیامش ریپلای کن.", context)
            return

        if not await _has_access(context, chat.id, user.id):
            await _send_temp_message(msg, "🚫 فقط مدیران یا سودوها مجازند.", context)
            return
        if target.id == context.bot.id:
            await _send_temp_message(msg, "😅 نمی‌توانم خودم را مدیر کنم!", context)
            return
        if target.id in SUDO_IDS:
            await _send_temp_message(msg, "👑 این کاربر سودو است و نیاز به ارتقا ندارد.", context)
            return
        if not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 من اجازه‌ی ارتقا ندارم. لطفاً دسترسی «Add New Admins» را بده.", context)
            return

        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                can_delete_messages=True,
                can_restrict_members=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_topics=True,
            )
            data[chat_key].append(target.id)
            _save_json(ADMINS_FILE, data)
            await _send_temp_message(msg, f"✅ {target.first_name} به‌عنوان مدیر منصوب شد.", context)
        except Exception as e:
            await _send_temp_message(msg, f"⚠️ خطا در افزودن مدیر: {e}", context)
        return

    # ===== حذف مدیر =====
    if text.startswith("حذف مدیر"):
        target, mention_failed = await _get_target_user(update, context, text)
        if not target:
            await _send_temp_message(msg, "⚠️ کاربر مشخص نشد.", context)
            return

        if not await _has_access(context, chat.id, user.id):
            await _send_temp_message(msg, "🚫 فقط مدیران یا سودوها مجازند.", context)
            return
        if target.id in SUDO_IDS:
            await _send_temp_message(msg, "👑 این کاربر سودو است و حذف نمی‌شود.", context)
            return
        if not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 من اجازه‌ی حذف مدیران را ندارم.", context)
            return

        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=False,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_manage_topics=False,
            )
            if target.id in data[chat_key]:
                data[chat_key].remove(target.id)
                _save_json(ADMINS_FILE, data)
            await _send_temp_message(msg, f"⚙️ {target.first_name} از مدیران حذف شد.", context)
        except Exception as e:
            await _send_temp_message(msg, f"⚠️ خطا در حذف مدیر: {e}", context)
        return

    # ===== لیست مدیران =====
    if text == "لیست مدیران":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            lines = [f"• {a.user.first_name}" for a in current_admins if not a.user.is_bot]
            await _send_temp_message(
                msg,
                "👑 مدیران فعلی گروه:\n" + "\n".join(lines) if lines else "ℹ️ مدیری وجود ندارد.",
                context,
            )
        except Exception as e:
            await _send_temp_message(msg, f"⚠️ خطا: {e}", context)
        return

# ========================= راه‌اندازی ربات =========================
def register_admin_handlers(application, group_number: int = 15):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_admin_management,
        ),
        group=group_number,
    )

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_admin_handlers(app)
    print("🤖 ربات مدیرساز با موفقیت فعال شد...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
