from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.errors import InviteHashExpiredError, InviteHashInvalidError, PeerFloodError
import asyncio
import re
import json
import os

# ────── اطلاعات تلگرام
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ────── تنظیمات
SUDO = 8588347189
STATS_FILE = "join_stats.json"
USERS_FILE = "users_list.json"

# ────── ایجاد فایل‌ها در صورت نبودن
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        json.dump({"groups":0,"channels":0,"banned_groups":0}, f)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# ────── توابع مدیریت آمار و کاربران
def load_stats():
    with open(STATS_FILE,"r") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE,"w") as f:
        json.dump(data,f)

def load_users():
    with open(USERS_FILE,"r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE,"w") as f:
        json.dump(users,f)

# ────── الگوی لینک دعوت
invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

# ────── هندلر اصلی
@client.on(events.NewMessage)
async def main_handler(event):
    sender = event.sender_id
    text = event.raw_text.strip()

    is_sudo = sender == SUDO

    # ── جمع‌آوری خودکار کاربران (کاربران عادی)
    if not is_sudo:
        if event.is_group:
            users = load_users()
            if sender not in users:
                users.append(sender)
                save_users(users)
        return

    # ── دستور آمار
    if text in ["آمار","stats","/stats"]:
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

    # ── دستور اد با امکان انتخاب گروه مقصد
    if text.startswith("اد "):
        parts = text.split()
        if len(parts) < 2:
            await event.reply("❌ فرمت درست: `اد تعداد [گروه]`")
            return
        try:
            num = int(parts[1])
        except:
            await event.reply("❌ عدد معتبر نیست.")
            return

        # اگر گروه مقصد مشخص نشده، گروه فعلی استفاده می‌شود
        target_chat = event.chat_id if len(parts) == 2 else parts[2]

        users = load_users()
        if not users:
            await event.reply("❌ لیست کاربران خالی است.")
            return

        target_users = users[:num]
        added_count = 0
        stats = load_stats()

        for user_id in target_users:
            try:
                await client(InviteToChannelRequest(target_chat, [user_id]))
                added_count += 1
            except PeerFloodError:
                await event.reply("⚠️ محدودیت تلگرام: عملیات متوقف شد.")
                stats["banned_groups"] += 1
                break
            except Exception:
                stats["banned_groups"] += 1
                pass

        remaining_users = users[num:]
        save_users(remaining_users)
        save_stats(stats)
        await event.reply(f"✅ تعداد {added_count} نفر اضافه شدند.")
        return

    # ── ارسال پیام ریپلای
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        target_text = reply_msg.message

        if text == "ارسال گروه":
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    try:
                        await client.send_message(dialog.id, target_text)
                    except:
                        pass
            await event.reply("✅ پیام به همه گروه‌ها ارسال شد.")
            return

        if text == "ارسال کاربران":
            users = load_users()
            for uid in users:
                try:
                    await client.send_message(uid, target_text)
                except:
                    pass
            await event.reply("✅ پیام به همه کاربران ارسال شد.")
            return

        if text == "ارسال همه":
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    try:
                        await client.send_message(dialog.id, target_text)
                    except:
                        pass
            users = load_users()
            for uid in users:
                try:
                    await client.send_message(uid, target_text)
                except:
                    pass
            await event.reply("✅ پیام به همه گروه‌ها و کاربران ارسال شد.")
            return

    # ── لینک دعوت
    match = re.search(invite_pattern, text)
    if match:
        invite_link = match.group(1)
        await event.reply("🔍 در حال تلاش برای پیوستن...")

        stats = load_stats()
        try:
            if "joinchat" in invite_link or "+" in invite_link:
                invite_hash = invite_link.split("/")[-1]
                await client(ImportChatInviteRequest(invite_hash))
                stats["groups"] += 1
            else:
                await client(JoinChannelRequest(invite_link))
                if "/c/" in invite_link or invite_link.count("/") > 3:
                    stats["groups"] += 1
                else:
                    stats["channels"] += 1
            save_stats(stats)
            await event.reply("✅ با موفقیت پیوستم و آمار بروز شد.")
        except InviteHashExpiredError:
            await event.reply("❌ لینک منقضی شده است.")
        except InviteHashInvalidError:
            await event.reply("❌ لینک معتبر نیست.")
        except Exception as e:
            await event.reply(f"⚠️ خطا: {e}")

# ────── شروع بات
async def main():
    await client.start()
    print("⚡ یوزربات پیشرفته فعال شد!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
