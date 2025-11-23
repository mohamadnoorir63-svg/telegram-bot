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
import traceback

# ────── اطلاعات تلگرام
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ────── تنظیمات
SUDO = 8588347189
STATS_FILE = "join_stats.json"
USERS_FILE = "users_list.json"

LAST_JOIN_TIME = 0
JOIN_DELAY = 60  # فاصله بین جوین لینک‌ها
BATCH_SIZE = 50
BATCH_DELAY = 120  # ثانیه بین بسته‌ها

# ────── ایجاد فایل‌ها در صورت نبودن
def ensure_files():
    if not os.path.exists(STATS_FILE):
        initial = {
            "groups": 0,
            "channels": 0,
            "banned_groups": 0,
            "__joined_groups__": [],
            "__joined_channels__": []
        }
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(initial, f, ensure_ascii=False, indent=2)

    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

ensure_files()

# ────── توابع آمار و کاربران
def load_stats():
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ────── الگوی لینک
invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

# ────── ثبت گروه/کانال
async def register_chat(chat_id, is_group):
    stats = load_stats()
    if is_group:
        joined_groups = stats.get("__joined_groups__", [])
        if chat_id not in joined_groups:
            joined_groups.append(chat_id)
            stats["__joined_groups__"] = joined_groups
            stats["groups"] += 1
            save_stats(stats)
    else:
        joined_channels = stats.get("__joined_channels__", [])
        if chat_id not in joined_channels:
            joined_channels.append(chat_id)
            stats["__joined_channels__"] = joined_channels
            stats["channels"] += 1
            save_stats(stats)

# ────── اسکن اولیه دیالوگ‌ها
async def init_joined_chats():
    stats = load_stats()
    stats.setdefault("__joined_groups__", [])
    stats.setdefault("__joined_channels__", [])
    stats.setdefault("groups", 0)
    stats.setdefault("channels", 0)
    changed = False

    async for dialog in client2.iter_dialogs():
        try:
            chat_id = dialog.id
            if dialog.is_group and chat_id not in stats["__joined_groups__"]:
                stats["__joined_groups__"].append(chat_id)
                stats["groups"] += 1
                changed = True
            elif dialog.is_channel and chat_id not in stats["__joined_channels__"]:
                stats["__joined_channels__"].append(chat_id)
                stats["channels"] += 1
                changed = True
        except Exception:
            print("خطا هنگام اسکن دیالوگ:", traceback.format_exc())

    if changed:
        save_stats(stats)
        print("✅ آمار اولیه به‌روزرسانی شد.")
    else:
        print("ℹ️ هیچ چت جدیدی برای اضافه کردن وجود نداشت.")

# ────── سیستم جوین با تاخیر
async def join_with_delay(invite_link, event):
    global LAST_JOIN_TIME

    now = time.time()
    wait_time = LAST_JOIN_TIME + JOIN_DELAY - now
    if wait_time > 0:
        try: await event.reply(f"⏳ باید {int(wait_time)} ثانیه صبر کنم...")
        except: pass
        await asyncio.sleep(wait_time)

    LAST_JOIN_TIME = time.time()
    stats = load_stats()

    try:
        clean = invite_link.replace("https://", "").replace("http://", "").replace("t.me/", "")
        if clean.startswith("+") or clean.startswith("joinchat/"):
            invite_hash = clean.replace("+", "").replace("joinchat/", "")
            await client2(ImportChatInviteRequest(invite_hash))
            stats["groups"] = stats.get("groups", 0) + 1
        else:
            await client2(JoinChannelRequest(clean))
            stats["channels"] = stats.get("channels", 0) + 1

        save_stats(stats)
        try: await event.reply("✅ با موفقیت عضو شدم.")
        except: pass

    except InviteHashExpiredError:
        try: await event.reply("❌ لینک منقضی شده است.")
        except: pass
    except InviteHashInvalidError:
        try: await event.reply("❌ لینک معتبر نیست.")
        except: pass
    except Exception as e:
        print("خطا در join_with_delay:", traceback.format_exc())
        try: await event.reply(f"⚠️ خطا: {e}")
        except: pass

# ────── ارسال پیام با batching
async def send_in_batches(targets, message_text, event, target_type="user"):
    sent_count = 0
    total = len(targets)
    for i in range(0, total, BATCH_SIZE):
        batch = targets[i:i + BATCH_SIZE]
        for t in batch:
            try:
                await client2.send_message(t, message_text)
            except: pass
            sent_count += 1
        if i + BATCH_SIZE < total:
            await event.reply(f"⏳ ارسال {sent_count}/{total} انجام شد، صبر {BATCH_DELAY} ثانیه برای ادامه...")
            await asyncio.sleep(BATCH_DELAY)
    await event.reply(f"✅ ارسال پیام به همه {total} {target_type}s انجام شد.")
  # ────── هندلر پیام‌ها
@client2.on(events.NewMessage)
async def main_handler(event):
    try:
        sender = getattr(event, "sender_id", None)
        text = (event.raw_text or "").strip()
        is_sudo = (sender == SUDO)

        # ────── ثبت گروه/کانال جدید در آمار
        chat_id = getattr(event, "chat_id", None)
        if getattr(event, "is_group", False) and chat_id is not None:
            await register_chat(chat_id, is_group=True)
        elif getattr(event, "is_channel", False) and chat_id is not None:
            await register_chat(chat_id, is_group=False)

        # ────── جمع‌آوری کاربران عادی
        if not is_sudo:
            if sender is not None and getattr(event, "is_group", False):
                users = load_users()
                if sender not in users:
                    users.append(sender)
                    save_users(users)
            match = re.search(invite_pattern, text)
            if match:
                await join_with_delay(match.group(1), event)
            return

        # ────── دستورات مدیریتی SUDO
        if text in ["آمار", "/stats", "stats"]:
            stats = load_stats()
            users = load_users()
            await event.reply(
                f"📊 **آمار ربات:**\n\n"
                f"👥 کاربران ذخیره شده: `{len(users)}`\n"
                f"📢 کانال‌ها: `{stats.get('channels', 0)}`\n"
                f"👥 گروه‌ها: `{stats.get('groups', 0)}`\n"
                f"⛔ گروه‌های بن شده: `{stats.get('banned_groups', 0)}`"
            )
            return

        if text == "پاکسازی بن":
            stats = load_stats()
            stats["banned_groups"] = 0
            save_stats(stats)
            await event.reply("✅ گروه‌های بن شده پاکسازی شدند.")
            return

        # ────── اد کاربران به گروه/کانال
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

            for i in range(0, len(target_users), BATCH_SIZE):
                batch = target_users[i:i + BATCH_SIZE]
                for uid in batch:
                    try:
                        await client2(InviteToChannelRequest(target_chat, [uid]))
                        added_count += 1
                    except PeerFloodError:
                        await event.reply("⚠️ محدودیت تلگرام: عملیات متوقف شد.")
                        stats["banned_groups"] = stats.get("banned_groups", 0) + 1
                        break
                    except:
                        stats["banned_groups"] = stats.get("banned_groups", 0) + 1
                        pass
                if i + BATCH_SIZE < len(target_users):
                    await event.reply(f"⏳ اضافه شدن {added_count}/{len(target_users)} کاربر، صبر {BATCH_DELAY} ثانیه...")
                    await asyncio.sleep(BATCH_DELAY)

            save_users(users[num:])
            save_stats(stats)
            await event.reply(f"✅ تعداد {added_count} نفر اضافه شدند.")
            return

        # ────── ارسال پیام ریپلای
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            target_text = reply_msg.message

            if text == "ارسال گروه":
                groups = [d.id async for d in client2.iter_dialogs() if d.is_group]
                await send_in_batches(groups, target_text, event, target_type="گروه")
                return

            if text == "ارسال کاربران":
                users = load_users()
                await send_in_batches(users, target_text, event, target_type="کاربر")
                return

            if text == "ارسال همه":
                groups = [d.id async for d in client2.iter_dialogs() if d.is_group]
                await send_in_batches(groups, target_text, event, target_type="گروه")
                users = load_users()
                await send_in_batches(users, target_text, event, target_type="کاربر")
                return

        # ────── لینک دعوت برای SUDO
        match = re.search(invite_pattern, text)
        if match:
            await join_with_delay(match.group(1), event)

    except Exception:
        print("خطا در main_handler:", traceback.format_exc())

# ────── اجرای کلاینت
async def start_userbot2():
    await client2.start()
    print("⚡ یوزربات فعال شد.")
    try:
        await init_joined_chats()
    except Exception:
        print("خطا هنگام init_joined_chats:", traceback.format_exc())
    await client2.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_userbot2())
