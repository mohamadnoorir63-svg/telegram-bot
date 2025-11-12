import os
import json
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")

# لیست سودوها
SUDO_IDS = [8588347189]

# ساخت فایل در صورت نبود
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ------------------------ توابع ------------------------
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

async def _get_target_user(update: Update):
    msg = update.effective_message
    if msg.reply_to_message:
        return msg.reply_to_message.from_user
    return None

async def _send_temp_message(msg, text, delete_after=10):
    sent = await msg.reply_text(text, parse_mode="HTML")
    asyncio.create_task(_delete_after(sent, delete_after))

async def _delete_after(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# ------------------------ هندلر ------------------------
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    target = await _get_target_user(update)
    if not target:
        await _send_temp_message(msg, "⚠️ روی پیام کاربر ریپلای کنید.")
        return

    if not await _has_access(context, chat.id, user.id):
        await _send_temp_message(msg, "🚫 فقط مدیران یا سودو می‌توانند.",)
        return

    # افزودن مدیر
    if text.startswith("افزودن مدیر"):
        if target.id in data[chat_key]:
            await _send_temp_message(msg, f"ℹ️ {target.first_name} قبلاً مدیر است.")
            return
        if not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 دسترسی ارتقا ندارم. ادمین Creator باشم.")
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
                can_promote_members=True
            )
            data[chat_key].append(target.id)
            _save_json(ADMINS_FILE, data)
            await _send_temp_message(msg, f"✅ {target.first_name} مدیر شد.")
        except Exception as e:
            await _send_temp_message(msg, f"⚠️ خطا: {e}")

    # حذف مدیر
    elif text.startswith("حذف مدیر"):
        if target.id not in data[chat_key]:
            await _send_temp_message(msg, f"ℹ️ {target.first_name} مدیر نیست.")
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
                can_manage_topics=False
            )
            data[chat_key].remove(target.id)
            _save_json(ADMINS_FILE, data)
            await _send_temp_message(msg, f"⚙️ {target.first_name} حذف شد.")
        except Exception as e:
            await _send_temp_message(msg, f"⚠️ خطا: {e}")

    elif text == "لیست مدیران":
        admins = await context.bot.get_chat_administrators(chat.id)
        lines = [f"• {a.user.first_name}" for a in admins if not a.user.is_bot]
        await _send_temp_message(msg, "👑 مدیران:\n" + "\n".join(lines) if lines else "ℹ️ مدیر ندارد.")

# ------------------------ ثبت هندلر ------------------------
def register_admin_handlers(application, group_number=15):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_admin,
        ),
        group=group_number
    )
