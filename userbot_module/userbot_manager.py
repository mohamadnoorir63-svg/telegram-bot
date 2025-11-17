import os
import asyncio
from telethon import TelegramClient, sessions
from telethon.tl.functions.messages import ImportChatInviteRequest
from telegram import Update
from telegram.ext import ContextTypes

# ---------------- یوزربات ----------------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")   # ✔ پرانتز اضافی حذف شد
SESSION_STRING = os.environ.get("SESSION_STRING")
USERBOT_ID = int(os.environ.get("USERBOT_ID"))

userbot_client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)

async def start_userbot_client():
    await userbot_client.start()
    print("✅ Userbot started and ready")

# ---------------- اضافه کردن یوزربات به گروه ----------------
async def add_userbot_to_group(bot, chat_id: int):
    # بررسی دسترسی ربات اصلی
    member = await bot.get_chat_member(chat_id, bot.id)
    if member.status not in ("administrator", "creator"):
        return False, "❌ ربات اصلی دسترسی ادمین ندارد!"

    # ساخت لینک دعوت
    invite_link = await bot.export_chat_invite_link(chat_id)

    # یوزربات با لینک وارد گروه می‌شود
    try:
        hash_part = invite_link.split("/")[-1]
        await userbot_client(ImportChatInviteRequest(hash_part))
    except Exception as e:
        return False, f"❌ خطا در ورود یوزربات: {e}"

    # ارتقا یوزربات به ادمین
    try:
        await bot.promote_chat_member(
            chat_id=chat_id,
            user_id=USERBOT_ID,
            can_change_info=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=True,
            can_manage_video_chats=True
        )
    except Exception as e:
        return False, f"❌ خطا در دادن دسترسی ادمین: {e}"

    return True, "✅ یوزربات وارد شد و مدیر گروه شد!"
