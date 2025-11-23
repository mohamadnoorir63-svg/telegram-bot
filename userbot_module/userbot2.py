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

# ────── اطلاعات تلگرام (مقادیر خودت رو نگه داشتم)
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ────── تنظیمات
SUDO = 8588347189
STATS_FILE = "join_stats.json"
USERS_FILE = "users_list.json"

# زمان آخرین جوین (برای جلوگیری از محدودیت)
LAST_JOIN_TIME = 0
JOIN_DELAY = 60  # ← هر لینک ۶۰ ثانیه فاصله

# ────── ایجاد فایل‌ها در صورت نبودن (و مقداردهی لیست‌های داخلی)
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

# ────── توابع آمار
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

# ────── تابعی که هنگام راه‌اندازی، دیالوگ‌های از قبل عضو شده را اسکن می‌کند
async def init_joined_chats():
    """
    اسکن تمام دیالوگ‌ها و اضافه کردن گروه/کانال‌هایی که از قبل در آن‌ها عضو هستیم
    به آمار (فقط اگر پیشتر وارد لیست نشده باشند).
    """
    stats = load_stats()
    # مطمئن شوید کلیدها وجود دارند
    stats.setdefault("__joined_groups__", [])
    stats.setdefault("__joined_channels__", [])
    stats.setdefault("groups", 0)
    stats.setdefault("channels", 0)
    changed = False

    async for dialog in client2.iter_dialogs():
        try:
            # dialog.is_group و dialog.is_channel پرکاربردترین پرچم‌ها هستند
            chat_id = dialog.id
            if dialog.is_group:
                if chat_id not in stats["__joined_groups__"]:
                    stats["__joined_groups__"].append(chat_id)
                    stats["groups"] = stats.get("groups", 0) + 1
                    changed = True
            elif dialog.is_channel:
                # توجه: کانال‌های خصوصی/عمومی هم اینجا می‌افتند
                if chat_id not in stats["__joined_channels__"]:
                    stats["__joined_channels__"].append(chat_id)
                    stats["channels"] = stats.get("channels", 0) + 1
                    changed = True
        except Exception:
            # فقط لاگ کن، ادامه بده
            print("خطا هنگام اسکن دیالوگ:", traceback.format_exc())

    if changed:
        save_stats(stats)
        print("✅ آمار اولیه (از قبل عضو شده‌ها) به‌روزرسانی شد.")
    else:
        print("ℹ️ هیچ چت جدیدی برای اضافه کردن به آمار وجود نداشت.")

# ────── سیستم جوین با تاخیر
async def join_with_delay(invite_link, event):
    global LAST_JOIN_TIME

    now = time.time()
    wait_time = LAST_JOIN_TIME + JOIN_DELAY - now

    if wait_time > 0:
        try:
            await event.reply(f"⏳ باید {int(wait_time)} ثانیه صبر کنم... (جلوگیری از بلاک)")
        except:
            pass
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
            # بعد از جوین، chat ممکنه به dialogها اضافه شده باشه؛ در init_joined_chats هم حساب میشه اما اینجا افزایش میدیم
            stats["groups"] = stats.get("groups", 0) + 1

        # ── لینک joinchat/
        elif clean.startswith("joinchat/"):
            invite_hash = clean.replace("joinchat/", "")
            await client2(ImportChatInviteRequest(invite_hash))
            stats["groups"] = stats.get("groups", 0) + 1

        # ── کانال‌های عادی / t.me/test123
        else:
            await client2(JoinChannelRequest(clean))
            stats["channels"] = stats.get("channels", 0) + 1

        save_stats(stats)
        try:
            await event.reply("✅ با موفقیت عضو شدم.")
        except:
            pass

    except InviteHashExpiredError:
        try:
            await event.reply("❌ لینک منقضی شده است.")
        except:
            pass
    except InviteHashInvalidError:
        try:
            await event.reply("❌ لینک معتبر نیست.")
        except:
            pass
    except Exception as e:
        # لاگ خطا برای دیباگ
        print("خطا در join_with_delay:", traceback.format_exc())
        try:
            await event.reply(f"⚠️ خطا: {e}")
        except:
            pass

# ────── هندلر پیام‌ها
@client2.on(events.NewMessage)
async def main_handler(event):
    """
    هر پیام جدید (از هرکس) اینجا میاد.
    - اگر پیام از SUDO باشه: دستورات مدیریتی را پردازش کن
    - اگر پیام از کاربر عادی باشه: کاربر را ذخیره کن و در صورت وجود لینک، جوین شو
    - همیشه: اگر چت (گروه/کانال) شناخته نشده باشه، به آمار اضافه کن
    """
    try:
        # sender_id ممکنه None باشه (مثلاً پیام کانال بدون sender). از getattr استفاده می‌کنیم
        sender = getattr(event, "sender_id", None)
        text = (event.raw_text or "").strip()
        is_sudo = (sender == SUDO)

        # اول: اگر پیام در گروه/کانال باشد، مطمئن شویم آن چت به آمار اضافه شده
        stats = load_stats()
        stats.setdefault("__joined_groups__", [])
        stats.setdefault("__joined_channels__", [])
        updated = False

        # chat_id برای دیالوگ جاری
        chat_id = getattr(event, "chat_id", None)
        # event.is_group و event.is_channel را چک کن (این‌ها در telethon موجودند)
        if getattr(event, "is_group", False) or getattr(event, "is_channel", False):
            if getattr(event, "is_group", False):
                if chat_id is not None and chat_id not in stats["__joined_groups__"]:
                    stats["__joined_groups__"].append(chat_id)
                    stats["groups"] = stats.get("groups", 0) + 1
                    updated = True
            if getattr(event, "is_channel", False):
                if chat_id is not None and chat_id not in stats["__joined_channels__"]:
                    stats["__joined_channels__"].append(chat_id)
                    stats["channels"] = stats.get("channels", 0) + 1
                    updated = True

        if updated:
            save_stats(stats)
            # اگر مایل بودی می‌توانی این پیام را به SUDO اطلاع بدی؛ الان اعلان نمی‌فرستم تا اسپم نشه.

        # ────── ادامه پردازش پیام
        # ────── جمع‌آوری کاربران عادی
        if not is_sudo:
            # اگر فرستنده کاربر معمولی و داخل گروه است، ذخیره کن
            if sender is not None and getattr(event, "is_group", False):
                users = load_users()
                if sender not in users:
                    users.append(sender)
                    save_users(users)

            # کاربران عادی هم اگر لینک بفرستند → خودکار جوین شو
            match = re.search(invite_pattern, text)
            if match:
                await join_with_delay(match.group(1), event)
            return

        # ────── اگر SUDO هست، دستورات مدیریتی
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
                    stats["banned_groups"] = stats.get("banned_groups", 0) + 1
                    break
                except Exception:
                    # اگر خطا شد فقط آمار بن را افزایش بده
                    stats["banned_groups"] = stats.get("banned_groups", 0) + 1
                    pass

            save_users(users[num:])
            save_stats(stats)
            await event.reply(f"✅ تعداد {added_count} نفر اضافه شدند.")
            return

        
        # ────── تعداد پیام در هر Batch و تاخیر بین Batchها
MESSAGE_BATCH_SIZE = 50      # هر ۵۰ نفر/گروه یک توقف
MESSAGE_BATCH_DELAY = 120    # ۲ دقیقه توقف

if event.is_reply:
    reply_msg = await event.get_reply_message()
    target_text = reply_msg.message

    # ────── ارسال به گروه‌ها با Batch
    if text == "ارسال گروه":
        count = 0
        async for dialog in client2.iter_dialogs():
            if dialog.is_group:
                try:
                    await client2.send_message(dialog.id, target_text)
                    count += 1
                    if count % MESSAGE_BATCH_SIZE == 0:
                        await asyncio.sleep(MESSAGE_BATCH_DELAY)
                except:
                    pass
        await event.reply("✅ پیام به همه گروه‌ها ارسال شد.")
        return

    # ────── ارسال به کاربران با Batch
    if text == "ارسال کاربران":
        users = load_users()
        count = 0
        for uid in users:
            try:
                await client2.send_message(uid, target_text)
                count += 1
                if count % MESSAGE_BATCH_SIZE == 0:
                    await asyncio.sleep(MESSAGE_BATCH_DELAY)
            except:
                pass
        await event.reply("✅ پیام به همه کاربران ارسال شد.")
        return

    # ────── ارسال به همه (گروه + کاربران) با Batch
    if text == "ارسال همه":
        # ارسال به گروه‌ها
        count = 0
        async for dialog in client2.iter_dialogs():
            if dialog.is_group:
                try:
                    await client2.send_message(dialog.id, target_text)
                    count += 1
                    if count % MESSAGE_BATCH_SIZE == 0:
                        await asyncio.sleep(MESSAGE_BATCH_DELAY)
                except:
                    pass
        # ارسال به کاربران
        users = load_users()
        count = 0
        for uid in users:
            try:
                await client2.send_message(uid, target_text)
                count += 1
                if count % MESSAGE_BATCH_SIZE == 0:
                    await asyncio.sleep(MESSAGE_BATCH_DELAY)
            except:
                pass
        await event.reply("✅ پیام به همه ارسال شد.")
        return
        # ────── لینک دعوت (مدیریت خودکار) برای SUDO هم
        match = re.search(invite_pattern, text)
        if match:
            await join_with_delay(match.group(1), event)

    except Exception:
        # لاگ کامل خطا برای دیباگ
        print("خطا در main_handler:", traceback.format_exc())

# ────── اجرای کلاینت
async def start_userbot2():
    await client2.start()
    print("⚡ یوزربات فعال شد.")
    # اسکن اولیهٔ دیالوگ‌ها تا گروه/کانال‌های از قبل عضو شده رو بشماره
    try:
        await init_joined_chats()
    except Exception:
        print("خطا هنگام init_joined_chats:", traceback.format_exc())

    await client2.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_userbot2())
