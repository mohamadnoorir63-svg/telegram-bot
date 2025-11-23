from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.errors import InviteHashExpiredError, InviteHashInvalidError, PeerFloodError
import asyncio
import re
import json
import os
import time

# ────── اطلاعات تلگرام
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ────── تنظیمات
SUDO = 8588347189
(stats)
STATS_FILE = "join_stats.json"
USERS_FILE = "users_list.json"
# ────── شناسایی گروه/کانال‌هایی که از قبل عضو بوده‌ایم
        if event.is_group or event.is_channel:
            stats = load_stats()

            # گروه
            if event.is_group:
                if "__joined_groups__" not in stats:
                    stats["__joined_groups__"] = []

                if event.chat_id not in stats["__joined_groups__"]:
                    stats["__joined_groups__"].append(event.chat_id)
                    stats["groups"] += 1
                    save_stats(stats)

            # کانال
            if event.is_channel:
                if "__joined_channels__" not in stats:
                    stats["__joined_channels__"] = []

                if event.chat_id not in stats["__joined_channels__"]:
                    stats["__joined_channels__"].append(event.chat_id)
                    stats["channels"] += 1
                    save_stats(stats)

# زمان آخرین جوین (برای جلوگیری از محدودیت)
LAST_JOIN_TIME = 0
JOIN_DELAY = 60  # ← هر لینک ۶۰ ثانیه فاصله

# ────── ایجاد فایل‌ها در صورت نبودن
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        json.dump({"groups": 0, "channels": 0, "banned_groups": 0}, f)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# ────── توابع آمار
def load_stats():
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# ────── الگوی لینک
invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

# ────── سیستم جوین با تاخیر
async def join_with_delay(invite_link, event):
    global LAST_JOIN_TIME

    now = time.time()
    wait_time = LAST_JOIN_TIME + JOIN_DELAY - now

    if wait_time > 0:
        await event.reply(f"⏳ باید {int(wait_time)} ثانیه صبر کنم... (جلوگیری از بلاک)")
        await asyncio.sleep(wait_time)

    LAST_JOIN_TIME = time.time()

    stats = load_stats()

    try:
        clean = invite_link.replace("https://", "").replace("http://", "")
        clean = clean.replace("t.me/", "")

        # ── لینک + (لینک خصوصی)
        if clean.startswith("+"):
            invite_hash = clean.replace("+", "")
            await client2(ImportChatInviteRequest(invite_hash))
            stats["groups"] += 1

        # ── لینک joinchat/
        elif clean.startswith("joinchat/"):
            invite_hash = clean.replace("joinchat/", "")
            await client2(ImportChatInviteRequest(invite_hash))
            stats["groups"] += 1

        # ── کانال‌های عادی / t.me/test123
        else:
            await client2(JoinChannelRequest(clean))
            stats["channels"] += 1

        save_stats(stats)
        await event.reply("✅ با موفقیت عضو شدم.")

    except InviteHashExpiredError:
        await event.reply("❌ لینک منقضی شده است.")
    except InviteHashInvalidError:
        await event.reply("❌ لینک معتبر نیست.")
    except Exception as e:
        await event.reply(f"⚠️ خطا: {e}")


# ────── هندلر پیام‌ها
@client2.on(events.NewMessage)
async def main_handler(event):
    sender = event.sender_id
    text = event.raw_text.strip()
    is_sudo = sender == SUDO

    # ────── جمع‌آوری کاربران عادی
    if not is_sudo:
        if event.is_group:
            users = load_users()
            if sender not in users:
                users.append(sender)
                save_users(users)

        # کاربران عادی هم اگر لینک بفرستند → خودکار جوین شو
        match = re.search(invite_pattern, text)
        if match:
            await join_with_delay(match.group(1), event)
        return

    # ────── آمار
    if text in ["آمار", "/stats", "stats"]:
        stats = load_stats()
        users = load_users()
        await event.reply(
            f"📊 **آمار ربات:**\n\n"
            f"👥 کاربران ذخیره شده: `{len(users)}`\n"
            f"📢 کانال‌ها: `{stats['channels']}`\n"
            f"👥 گروه‌ها: `{stats['groups']}`\n"
            f"⛔ گروه‌های بن شده: `{stats['banned_groups']}`"
        )
        return

    # ────── پاکسازی بن
    if text == "پاکسازی بن":
        stats = load_stats()
        stats["banned_groups"] = 0
        save_stats(stats)
        await event.reply("✅ گروه‌های بن شده پاکسازی شدند.")
        return

    # ────── اد عضو
    if text.startswith("اد "):
        parts = text.split()
        if len(parts) < 2:
            await event.reply("❌ فرمت درست: `اد تعداد [گروه_id]`")
            return

        try:
            num = int(parts[1])
        except:
            await event.reply("❌ عدد معتبر نیست.")
            return

        target_chat = event.chat_id if len(parts) == 2 else int(parts[2])
        users = load_users()

        if not users:
            await event.reply("❌ لیست کاربران خالی است.")
            return

        target_users = users[:num]
        added_count = 0
        stats = load_stats()

        for user_id in target_users:
            try:
                await client2(InviteToChannelRequest(target_chat, [user_id]))
                added_count += 1
            except PeerFloodError:
                await event.reply("⚠️ محدودیت تلگرام: عملیات متوقف شد.")
                stats["banned_groups"] += 1
                break
            except:
                stats["banned_groups"] += 1
                pass

        save_users(users[num:])
        save_stats(stats)
        await event.reply(f"✅ تعداد {added_count} نفر اضافه شدند.")
        return

    # ────── ارسال پیام ریپلای
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        target_text = reply_msg.message

        if text == "ارسال گروه":
            async for dialog in client2.iter_dialogs():
                if dialog.is_group:
                    try:
                        await client2.send_message(dialog.id, target_text)
                    except:
                        pass
            await event.reply("✅ پیام به همه گروه‌ها ارسال شد.")
            return

        if text == "ارسال کاربران":
            users = load_users()
            for uid in users:
                try:
                    await client2.send_message(uid, target_text)
                except:
                    pass
            await event.reply("✅ پیام به همه کاربران ارسال شد.")
            return

        if text == "ارسال همه":
            async for dialog in client2.iter_dialogs():
                if dialog.is_group:
                    try:
                        await client2.send_message(dialog.id, target_text)
                    except:
                        pass
            users = load_users()
            for uid in users:
                try:
                    await client2.send_message(uid, target_text)
                except:
                    pass
            await event.reply("✅ پیام به همه ارسال شد.")
            return

    # ────── لینک دعوت (مدیریت خودکار)
    match = re.search(invite_pattern, text)
    if match:
        await join_with_delay(match.group(1), event)


# ────── اجرای کلاینت
async def start_userbot2():
    await client2.start()
    print("⚡ یوزربات فعال شد.")
    await client2.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_userbot2())
