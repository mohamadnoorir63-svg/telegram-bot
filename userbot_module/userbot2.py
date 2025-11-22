from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.errors import InviteHashExpiredError, InviteHashInvalidError
import asyncio
import re
import json
import os
from datetime import date

# =======================
# 🔹 تنظیمات یوزربات
# =======================
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="
ADMIN_ID = 8588347189  # آیدی برای ارسال گزارش روزانه

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# =======================
# 🔹 فایل‌های ذخیره‌سازی
# =======================
STATS_FILE = "join_stats.json"
DAILY_FILE = "daily_stats.json"
USERS_FILE = "users.json"
LINKS_FILE = "joined_links.json"
GREETED_FILE = "greeted.json"

for file, default in [
    (STATS_FILE, {"groups":0,"channels":0}),
    (DAILY_FILE, {"date": str(date.today()), "groups":0,"channels":0}),
    (USERS_FILE, []),
    (LINKS_FILE, []),
    (GREETED_FILE, [])
]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)

# =======================
# 🔹 توابع کمکی
# =======================
def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def reset_daily_if_needed():
    daily = load_json(DAILY_FILE)
    today = str(date.today())
    if daily["date"] != today:
        daily = {"date": today, "groups":0,"channels":0}
        save_json(DAILY_FILE, daily)
    return daily

MAX_JOIN_PER_DAY = 50
invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

# =======================
# 🔹 مدیریت پیام‌ها و Join
# =======================
@client2.on(events.NewMessage)
async def handler(event):
    text = event.raw_text.strip()
    user_id = event.sender_id
    users = load_json(USERS_FILE)
    greeted = load_json(GREETED_FILE)

    # ذخیره کاربر پیام‌دهنده
    if user_id not in users:
        users.append(user_id)
        save_json(USERS_FILE, users)

    # نمایش آمار
    if text.lower() in ["آمار","/stats","stats"]:
        stats = load_json(STATS_FILE)
        daily = reset_daily_if_needed()
        users_count = len(users)
        joined_links = len(load_json(LINKS_FILE))
        await event.reply(
            f"📊 **آمار ربات:**\n\n"
            f"👤 کاربران پیام‌دهنده: `{users_count}` نفر\n"
            f"👥 گروه‌ها Joined: `{stats['groups']}` (امروز: {daily['groups']})\n"
            f"📢 کانال‌ها Joined: `{stats['channels']}` (امروز: {daily['channels']})\n"
            f"🔗 لینک‌های Join شده: `{joined_links}`\n"
            f"📦 مجموع: `{stats['groups'] + stats['channels']}`"
        )
        return

    # شناسایی لینک گروه یا کانال
    match = re.search(invite_pattern, text)
    if match:
        invite_link = match.group(1)
        joined_links = load_json(LINKS_FILE)
        if invite_link in joined_links:
            await event.reply("⚠️ قبلاً به این لینک پیوسته‌ام.")
            return

        daily = reset_daily_if_needed()
        if daily["groups"] + daily["channels"] >= MAX_JOIN_PER_DAY:
            await event.reply(f"⚠️ محدودیت Join روزانه ({MAX_JOIN_PER_DAY}) رسید.")
            return

        await event.reply("🔍 در حال تلاش برای پیوستن...")
        stats = load_json(STATS_FILE)

        try:
            joined_type = ""
            if "joinchat" in invite_link or "+" in invite_link:
                invite_hash = invite_link.split("/")[-1]
                await client2(ImportChatInviteRequest(invite_hash))
                stats["groups"] += 1
                daily["groups"] += 1
                joined_type = "گروه"
            else:
                await client2(JoinChannelRequest(invite_link))
                if "/c/" in invite_link or invite_link.count("/")>3:
                    stats["groups"] += 1
                    daily["groups"] += 1
                    joined_type = "گروه"
                else:
                    stats["channels"] += 1
                    daily["channels"] += 1
                    joined_type = "کانال"

            save_json(STATS_FILE, stats)
            save_json(DAILY_FILE, daily)
            joined_links.append(invite_link)
            save_json(LINKS_FILE, joined_links)

            # اد خودکار کاربر به گروه اگر لینک گروه باشد
            chat = await event.get_chat()
            if joined_type == "گروه":
                try:
                    await client2(InviteToChannelRequest(channel=chat.id, users=[user_id]))
                    await event.reply(f"✅ ممنون! با موفقیت به {joined_type} پیوستم و کاربر اضافه شد.")
                except:
                    await event.reply(f"✅ با موفقیت به {joined_type} پیوستم، اما کاربر را نتوانستم اضافه کنم.")
            else:
                await event.reply(f"✅ ممنون! با موفقیت به {joined_type} پیوستم.")

        except (InviteHashExpiredError, InviteHashInvalidError):
            await event.reply("❌ لینک دعوت معتبر نیست یا منقضی شده است.")
        except Exception as e:
            await event.reply(f"⚠️ خطا در پیوستن:\n{e}")
        return

    # ========================
    # 🔹 دستور اد و اد همه
    # ========================
    if event.is_reply:
        replied_msg = await event.get_reply_message()
        target_user = replied_msg.sender_id
        chat = await event.get_chat()
        chat_id = chat.id

        if text.lower().startswith("اد "):
            try:
                arg = text.split(" ")[1].lower()
                if arg == "همه":
                    users_to_add = users
                else:
                    users_to_add = [target_user]
                await client2(InviteToChannelRequest(channel=chat_id, users=users_to_add))
                await event.reply(f"✅ کاربران اضافه شدند: {users_to_add}")
            except Exception as e:
                await event.reply(f"❌ خطا در اد کردن کاربر:\n`{e}`")
            return

# =======================
# 🔹 ارسال خودکار گزارش روزانه به ادمین
# =======================
async def send_daily_report():
    await client2.start()
    daily = reset_daily_if_needed()
    users_count = len(load_json(USERS_FILE))
    stats_msg = (
        f"📊 گزارش روزانه ربات\n\n"
        f"👤 کاربران پیام‌دهنده: {users_count} نفر\n"
        f"👥 گروه‌ها Joined امروز: {daily['groups']}\n"
        f"📢 کانال‌ها Joined امروز: {daily['channels']}\n"
        f"📦 مجموع امروز: {daily['groups'] + daily['channels']}"
    )
    try:
        await client2.send_message(ADMIN_ID, stats_msg)
        print("✅ گزارش روزانه به ادمین ارسال شد.")
    except:
        print("❌ خطا در ارسال گزارش روزانه.")

# =======================
# 🔹 اجرای یوزربات
# =======================
async def start_userbot2():
    print("⚡ Userbot2 فعال و آماده است!")
    await client2.start()
    # می‌توان این تابع را زمان‌بندی کرد
    # asyncio.create_task(send_daily_report())
    await client2.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_userbot2())
