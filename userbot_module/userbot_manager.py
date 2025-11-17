from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import UserAlreadyParticipantError
from userbot import client, BOT_USER_ID  # یوزرباتت

async def add_userbot_to_group(bot, chat_id: int):
    """✅ اضافه کردن یوزربات به گروه با لینک دعوت و ارتقا ادمین"""
    # بررسی اینکه ربات اصلی ادمین است
    member = await bot.get_chat_member(chat_id, bot.id)
    if member.status not in ("administrator", "creator"):
        return False, "❌ ربات اصلی دسترسی ادمین ندارد!"

    # گرفتن لینک دعوت
    invite_link = await bot.export_chat_invite_link(chat_id)

    # یوزربات وارد گروه شود
    try:
        hash_part = invite_link.split("/")[-1]
        await client(ImportChatInviteRequest(hash_part))
    except UserAlreadyParticipantError:
        pass
    except Exception as e:
        return False, f"❌ خطا در ورود یوزربات: {e}"

    # ارتقا یوزربات به ادمین
    try:
        await bot.promote_chat_member(
            chat_id=chat_id,
            user_id=BOT_USER_ID,
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

    return True, "✅ یوزربات وارد شد و ادمین گروه شد!"
