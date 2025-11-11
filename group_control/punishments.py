import re
from datetime import datetime, timedelta
from telethon import events
from telethon.tl.types import ChatPermissions, Message, MessageEntityMentionName
from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError, PeerIdInvalidError

# 👑 سودوها
SUDO_USERS = [8588347189]


# ================= 🔍 تشخیص کاربر هدف =================
async def get_user_from_input(event, arg=None):
    """دریافت آیدی کاربر از ریپلای، منشن، آیدی عددی یا یوزرنیم"""
    reply = None
    try:
        reply = await event.get_reply_message()
    except Exception:
        reply = None

    # ✅ گاهی Telethon لیست پیام برمی‌گردونه → فقط اولی رو بگیر
    if isinstance(reply, list):
        reply = reply[0] if reply else None

    if reply and isinstance(reply, Message):
        return reply.sender_id

    # ✅ بررسی mention-type entity
    if event.message.entities:
        for ent in event.message.entities:
            if isinstance(ent, MessageEntityMentionName):
                return ent.user_id

    # ✅ بررسی @username
    if arg and arg.startswith("@"):
        username = arg.strip("@")
        try:
            user = await event.client.get_entity(username)
            return user.id
        except (UsernameNotOccupiedError, UsernameInvalidError, PeerIdInvalidError):
            return None

    # ✅ بررسی آیدی عددی
    if arg and re.match(r"^\d+$", arg):
        try:
            return int(arg)
        except ValueError:
            return None

    return None


# ================= 🔐 بررسی ادمین یا سودو =================
async def is_admin_or_sudo(event):
    if event.sender_id in SUDO_USERS:
        return True
    try:
        perms = await event.client.get_permissions(event.chat_id, event.sender_id)
        return perms.is_admin
    except:
        return False


# ================= ⚙️ ماژول اصلی تنبیهات =================
def register_punishment_module(client):
    @client.on(events.NewMessage(pattern=r"^(بن|سکوت|اخطار|حذف\s*بن|حذف\s*سکوت|حذف\s*اخطار)\b"))
    async def punish_command(event):
        if not await is_admin_or_sudo(event):
            return await event.reply("🚫 فقط مدیران یا سودوها مجازند.")

        text = event.raw_text.strip()
        parts = text.split(maxsplit=1)
        command = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        # 🧠 پیدا کردن هدف
        user_id = await get_user_from_input(event, arg)
        if not user_id:
            return await event.reply("⚠️ لطفاً روی پیام ریپلای کنید یا یوزرنیم/آیدی عددی را وارد کنید.")

        # 🛡 محافظت از ادمین و خود ربات
        try:
            member = await event.client.get_permissions(event.chat_id, user_id)
            if member.is_admin:
                return await event.reply("🛡 نمی‌توان روی مدیر یا سازنده اجرا کرد.")
        except:
            pass
        if user_id == (await event.client.get_me()).id:
            return await event.reply("😅 نمی‌توانم خودم را تنبیه کنم.")
        if user_id in SUDO_USERS:
            return await event.reply("🚫 این کاربر در لیست سودو است!")

        # ================= ⚙️ اجرای دستورات =================
        try:
            # 🚫 بن
            if command == "بن":
                await event.client.edit_permissions(event.chat_id, user_id, view_messages=False)
                return await event.reply(f"🚫 کاربر با آیدی `{user_id}` از گروه بن شد.", parse_mode="md")

            # 🔓 حذف بن
            elif command in ["حذفبن", "حذف بن"]:
                await event.client.edit_permissions(event.chat_id, user_id, view_messages=True)
                return await event.reply(f"✅ کاربر با آیدی `{user_id}` از بن خارج شد.", parse_mode="md")

            # 🤐 سکوت
            elif command == "سکوت":
                m = re.search(r"سکوت\s*(\d+)?\s*(ثانیه|دقیقه|ساعت)?", text)
                if m and m.group(1):
                    num = int(m.group(1))
                    unit = m.group(2)
                    if unit == "ساعت":
                        seconds = num * 3600
                    elif unit == "دقیقه":
                        seconds = num * 60
                    elif unit == "ثانیه":
                        seconds = num
                    else:
                        seconds = num * 60
                else:
                    seconds = 3600  # پیش‌فرض ۱ ساعت
                until_date = datetime.utcnow() + timedelta(seconds=seconds)
                await event.client.edit_permissions(
                    event.chat_id,
                    user_id,
                    send_messages=False,
                    until_date=until_date
                )
                return await event.reply(f"🤐 کاربر برای {seconds} ثانیه سکوت شد.")

            # 🔊 حذف سکوت
            elif command in ["حذفسکوت", "حذف سکوت"]:
                await event.client.edit_permissions(
                    event.chat_id,
                    user_id,
                    send_messages=True
                )
                return await event.reply("🔊 کاربر از حالت سکوت خارج شد.")

            # ⚠️ اخطار
            elif command == "اخطار":
                warns = getattr(client, "warns", {})
                key = f"{event.chat_id}:{user_id}"
                warns[key] = warns.get(key, 0) + 1
                client.warns = warns
                if warns[key] >= 3:
                    await event.client.edit_permissions(event.chat_id, user_id, view_messages=False)
                    warns[key] = 0
                    return await event.reply(f"🚫 کاربر به‌دلیل ۳ اخطار بن شد.")
                else:
                    return await event.reply(f"⚠️ اخطار {warns[key]}/3 برای کاربر ثبت شد.")

            # ✅ حذف اخطار
            elif command in ["حذفاخطار", "حذف اخطار"]:
                warns = getattr(client, "warns", {})
                key = f"{event.chat_id}:{user_id}"
                if key in warns:
                    del warns[key]
                    return await event.reply("✅ اخطارهای کاربر حذف شد.")
                return await event.reply("ℹ️ این کاربر اخطاری نداشت.")
        except Exception as e:
            await event.reply(f"⚠️ خطا در اجرای دستور: `{e}`", parse_mode="md")
