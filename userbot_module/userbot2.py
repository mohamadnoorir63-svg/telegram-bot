from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import InviteHashExpiredError, InviteHashInvalidError
import asyncio
import re
import json
import os

API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ────────────────────────────────
# 📌 فایل آمار + فایل کاربران
# ────────────────────────────────

STATS_FILE = "join_stats.json"
USERS_FILE = "users.json"

# اگر فایل‌ها نبودند، بسازیم
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        f.write(json.dumps({"groups": 0, "channels": 0}))

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        f.write(json.dumps([]))

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

# ────────────────────────────────

invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

@client2.on(events.NewMessage)
async def handler(event):

    # 📌 ثبت کاربر جدید در آمار کاربران
    user_id = event.sender_id
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

    text = event.raw_text

    # 📊 اگر گفت "آمار"
    if text.strip() in ["آمار", "/stats", "stats"]:
        stats = load_stats()
        users_count = len(load_users())

        await event.reply(
            f"📊 **آمار ربات:**\n\n"
            f"👤 کاربران پیام‌داده: `{users_count}` نفر\n"
            f"👥 گروه‌ها Joined: `{stats['groups']}`\n"
            f"📢 کانال‌ها Joined: `{stats['channels']}`\n"
            f"📦 مجموع: `{stats['groups'] + stats['channels']}`"
        )
        return

    # 🔍 جستجوی لینک و join
    match = re.search(invite_pattern, text)
    if match:
        invite_link = match.group(1)
        await event.reply("🔍 در حال تلاش برای پیوستن...")

        try:
            stats = load_stats()

            if "joinchat" in invite_link or "+" in invite_link:
                invite_hash = invite_link.split("/")[-1]
                await client2(ImportChatInviteRequest(invite_hash))
                stats["groups"] += 1
            else:
                await client2(JoinChannelRequest(invite_link))
                stats["channels"] += 1

            save_stats(stats)
            await event.reply("✅ با موفقیت پیوستم!")

        except Exception as e:
            await event.reply(f"⚠️ خطا:\n{e}")

# ────────────────────────────────
# ⚡ جوین خودکار به لینک‌های کانال
# ────────────────────────────────
@client2.on(events.ChatAction)
async def auto_join(event):
    if event.user_joined or event.user_added:
        if event.user_id == (await client2.get_me()).id:
            chat = await event.get_chat()
            if not chat.broadcast:  # یعنی کانال یا گروه عمومی
                async for message in client2.iter_messages(chat.id, limit=200):
                    if message.raw_text:
                        match = re.search(invite_pattern, message.raw_text)
                        if match:
                            link = match.group(1)
                            try:
                                if "joinchat" in link or "+" in link:
                                    invite_hash = link.split("/")[-1]
                                    await client2(ImportChatInviteRequest(invite_hash))
                                else:
                                    await client2(JoinChannelRequest(link))

                            except:
                                pass

async def start_userbot2():
    print("⚡ Userbot2 فعال شد!")
    await client2.start()
    await client2.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_userbot2())
