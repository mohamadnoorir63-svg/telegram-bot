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

SUDO = 8588347189  # فقط سودو اجازه دستورات دارد

# ────────────────────────────────
# 📌 سیستم آمارگیر
# ────────────────────────────────
STATS_FILE = "join_stats.json"

if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        f.write(json.dumps({"groups": 0, "channels": 0}))

def load_stats():
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f)

invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

# ────────────────────────────────
# 📌 هندلر اصلی
# ────────────────────────────────
@client2.on(events.NewMessage)
async def main_handler(event):
    sender = event.sender_id
    text = event.raw_text.strip()

    # اگر کاربر سودو نبود → هیچی نگو
    if sender != SUDO:
        return  

    # دستور آمار
    if text in ["آمار", "stats", "/stats"]:
        stats = load_stats()
        await event.reply(
            f"📊 **آمار ربات:**\n\n"
            f"👥 گروه‌ها: `{stats['groups']}`\n"
            f"📢 کانال‌ها: `{stats['channels']}`\n"
            f"📦 مجموع: `{stats['groups'] + stats['channels']}`"
        )
        return

    # دستور ارسال پیام ریپلای‌شده
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
            users = []
            # این قسمت را خودت باید پر کنی با لیست کاربران ذخیره شده
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
            # ارسال به کاربران در صورت داشتن لیست
            users = []
            for uid in users:
                try:
                    await client2.send_message(uid, target_text)
                except:
                    pass
            await event.reply("✅ پیام به همه ارسال شد.")
            return

    # لینک دعوت
    match = re.search(invite_pattern, text)
    if not match:
        return

    invite_link = match.group(1)
    await event.reply("🔍 در حال تلاش برای پیوستن...")

    try:
        stats = load_stats()

        if "joinchat" in invite_link or "+" in invite_link:
            invite_hash = invite_link.split("/")[-1]
            await client2(ImportChatInviteRequest(invite_hash))
            stats["groups"] += 1
            save_stats(stats)

        else:
            await client2(JoinChannelRequest(invite_link))

            if "/c/" in invite_link or invite_link.count("/") > 3:
                stats["groups"] += 1
            else:
                stats["channels"] += 1

            save_stats(stats)

        await event.reply("✅ با موفقیت پیوستم!\n📊 آمار به‌روزرسانی شد.")

    except InviteHashExpiredError:
        await event.reply("❌ لینک دعوت منقضی شده است.")
    except InviteHashInvalidError:
        await event.reply("❌ لینک دعوت معتبر نیست.")
    except Exception as e:
        await event.reply(f"⚠️ خطا:\n{e}")

# ────────────────────────────────
# شروع بات
# ────────────────────────────────
async def start_userbot2():
    print("⚡ Userbot2 فعال شد!")
    await client2.start()
    await client2.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_userbot2())
