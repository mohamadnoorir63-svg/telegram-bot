# -*- coding: utf-8 -*-
import asyncio
import json
import os
import re
import time
import traceback
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.errors import (
    InviteHashExpiredError,
    InviteHashInvalidError,
    PeerFloodError,
    UserPrivacyRestrictedError,
    RPCError
)

# ────── تنظیمات تلگرام (مقادیر خودت)
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ────── فایل‌ها و متغیرها
STATS_FILE = "join_stats.json"
USERS_FILE = "users_list.json"
PM_TIMES_FILE = "pm_times.json"  # نگهداری زمان آخرین پیام خوش‌آمد
JOIN_DELAY = 60        # هر جوین بین لینک‌ها (ثانیه)
BROADCAST_DELAY = 1.5  # فاصله بین پیام به هر کاربر هنگام ارسال انبوه (ثانیه)
PM_COOLDOWN = 60 * 60  # یک ساعت: فاصلهٔ ارسال پیام خوش‌آمد تکراری به یک کاربر

SUDO = 8588347189  # آی‌دی صاحب یا مدیر اصلی

LAST_JOIN_TIME = 0

invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

# ────── اطمینان از وجود فایل‌ها
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

    if not os.path.exists(PM_TIMES_FILE):
        with open(PM_TIMES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

ensure_files()

# ────── خواندن/نوشتن JSON
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_stats():
    return load_json(STATS_FILE, {})

def save_stats(data):
    save_json(STATS_FILE, data)

def load_users():
    return load_json(USERS_FILE, [])

def save_users(users):
    save_json(USERS_FILE, users)

def load_pm_times():
    return load_json(PM_TIMES_FILE, {})

def save_pm_times(d):
    save_json(PM_TIMES_FILE, d)

# ────── اسکن اولیهٔ دیالوگ‌ها (مثل قبل)
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
            if dialog.is_group:
                if chat_id not in stats["__joined_groups__"]:
                    stats["__joined_groups__"].append(chat_id)
                    stats["groups"] = stats.get("groups", 0) + 1
                    changed = True
            elif dialog.is_channel:
                if chat_id not in stats["__joined_channels__"]:
                    stats["__joined_channels__"].append(chat_id)
                    stats["channels"] = stats.get("channels", 0) + 1
                    changed = True
        except Exception:
            print("خطا هنگام اسکن دیالوگ:", traceback.format_exc())

    if changed:
        save_stats(stats)
        print("✅ آمار اولیه (از قبل عضو شده‌ها) به‌روزرسانی شد.")
    else:
        print("ℹ️ هیچ چت جدیدی برای اضافه کردن به آمار وجود نداشت.")

# ────── تابع جوین با تاخیر و هندلینگ خطا
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

        if clean.startswith("+") or clean.startswith("joinchat/"):
            # لینک خصوصی
            invite_hash = clean.replace("+", "").replace("joinchat/", "")
            await client2(ImportChatInviteRequest(invite_hash))
            stats["groups"] = stats.get("groups", 0) + 1
        else:
            # کانال یا یوزرنیم
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
        print("خطا در join_with_delay:", traceback.format_exc())
        try:
            await event.reply(f"⚠️ خطا: {e}")
        except:
            pass

# ────── ارسال پیام خوش‌آمد در PV (با cooldown و ذخیرهٔ کاربر فقط در PV)
async def send_welcome_pm_if_needed(sender_id):
    """
    وقتی کاربر در گروه پیام داد، این تابع تلاش می‌کند در PV برای او خوش‌آمد بفرستد.
    فقط اگر در  PM_TIMES بیشتر از PM_COOLDOWN گذشته باشد یا هنوز پیامی فرستاده نشده باشد.
    """
    pm_times = load_pm_times()
    last = pm_times.get(str(sender_id), 0)
    now = time.time()
    if now - last < PM_COOLDOWN:
        return False  # اخیراً پیام فرستاده شده؛ نپریزیم

    welcome_text = (
        "سلام! 👋\n"
        "برای فعال شدن خدمات ربات و دریافت پیام‌ها، لطفاً همین‌جا یک پیام بفرستید.\n"
        "این کار باعث می‌شود شما در لیست پیام‌رسانی قرار بگیرید."
    )
    try:
        await client2.send_message(sender_id, welcome_text)
        pm_times[str(sender_id)] = now
        save_pm_times(pm_times)
        return True
    except (UserPrivacyRestrictedError, RPCError):
        # کاربر امکان دریافت پیام از ادمین/ربات را بسته یا خطای RPC
        return False
    except Exception:
        print("خطا در send_welcome_pm_if_needed:", traceback.format_exc())
        return False

# ────── تابع ارسال پیام انبوه به کاربران (با تاخیر، گزارش)
async def broadcast_to_users(message_text):
    users = load_users()
    success = 0
    failed = 0
    for uid in users:
        try:
            await client2.send_message(int(uid), message_text)
            success += 1
        except PeerFloodError:
            print("⚠️ PeerFloodError during broadcast -> توقف ارسال")
            # وقتی flood میاد، بهتره متوقف کنیم
            return success, failed + (len(users) - success)
        except Exception:
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)
    return success, failed

# ────── تابع افزودن اعضا به کانال/گروه با رعایت خطاها
async def invite_users_to_target(target_chat, user_ids):
    stats = load_stats()
    added_count = 0
    for user_id in user_ids:
        try:
            await client2(InviteToChannelRequest(int(target_chat), [int(user_id)]))
            added_count += 1
            await asyncio.sleep(1.0)  # فاصله کوتاه بین دعوت‌ها
        except PeerFloodError:
            print("⚠️ محدودیت تلگرام: PeerFloodError هنگام دعوت")
            stats["banned_groups"] = stats.get("banned_groups", 0) + 1
            save_stats(stats)
            break
        except UserPrivacyRestrictedError:
            # کاربر پرایوسی دارد؛ نمی‌توان دعوت کرد
            stats["banned_groups"] = stats.get("banned_groups", 0) + 1
            save_stats(stats)
            continue
        except Exception:
            print("خطا در invite_users_to_target:", traceback.format_exc())
            stats["banned_groups"] = stats.get("banned_groups", 0) + 1
            save_stats(stats)
            continue
    return added_count

# ────── هندلر پیام‌ها (اصلاح‌شده)
@client2.on(events.NewMessage)
async def main_handler(event):
    try:
        sender = getattr(event, "sender_id", None)
        text = (event.raw_text or "").strip()
        is_sudo = (sender == SUDO)

        # همیشه چک کن آمار چت‌ها
        stats = load_stats()
        stats.setdefault("__joined_groups__", [])
        stats.setdefault("__joined_channels__", [])
        stats.setdefault("groups", 0)
        stats.setdefault("channels", 0)
        updated = False

        chat_id = getattr(event, "chat_id", None)
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

        # ────── رفتار برای پیام‌های غیر-SUDO (کاربران عادی)
        # 1) اگر پیام در گروه باشد → به کاربر پی‌وی خوش‌آمد بفرست و از ذخیره در لیست گروهی خودداری کن
        if not is_sudo:
            # اگر در گروه پیام دادیم، تلاش کن در پی‌وی برایش خوش‌آمد بفرستی
            if getattr(event, "is_group", False) and sender is not None:
                # ارسال پیام خوش‌آمد در PV (در صورت عدم cooldown)
                await send_welcome_pm_if_needed(sender)
                # دقت: ذخیره فقط وقتی انجام می‌شود که کاربر در پی‌وی با ما پیام بزند (بخش بعد)
                # همچنین اگر پیام شامل لینک دعوت بود، سعی در جوین شدن کن
                match = re.search(invite_pattern, text)
                if match:
                    await join_with_delay(match.group(1), event)
                return  # کاربران عادی در این بخش کار دیگری انجام نمی‌دهند

        # ────── رفتار برای پیام‌های SUDO (دستورات مدیریت)
        if is_sudo:
            # نمایش آمار
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

            # پاکسازی بن‌ها
            if text == "پاکسازی بن":
                stats = load_stats()
                stats["banned_groups"] = 0
                save_stats(stats)
                await event.reply("✅ گروه‌های بن شده پاکسازی شدند.")
                return

            # دستور اد: "اد <تعداد> [target_chat_id]"
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
                added_count = await invite_users_to_target(target_chat, target_users)
                # حذف کاربرانی که تلاش برای دعوت شده‌اند (چه دعوت موفق باشد چه نه، آن‌ها از لیست حذف می‌شوند تا دوباره تلاش نکنیم)
                remaining = users[num:]
                save_users(remaining)
                await event.reply(f"✅ تعداد {added_count} نفر اضافه شدند.")
                return

            # ارسال پیام به گروه‌ها / کاربران / همه — با ریپلای کردن پیام هدف
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_text = reply_msg.message or reply_msg.raw_text or ""
                if text == "ارسال گروه":
                    sent = 0
                    async for dialog in client2.iter_dialogs():
                        if dialog.is_group:
                            try:
                                await client2.send_message(dialog.id, target_text)
                                sent += 1
                                await asyncio.sleep(0.5)
                            except Exception:
                                pass
                    await event.reply(f"✅ پیام به {sent} گروه ارسال شد.")
                    return

                if text == "ارسال کاربران":
                    users = load_users()
                    success, failed = 0, 0
                    for uid in users:
                        try:
                            await client2.send_message(int(uid), target_text)
                            success += 1
                        except PeerFloodError:
                            await event.reply("⚠️ محدودیت تلگرام: عملیات متوقف شد.")
                            break
                        except Exception:
                            failed += 1
                        await asyncio.sleep(BROADCAST_DELAY)
                    await event.reply(f"✅ پیام به کاربران ارسال شد. موفق: {success} | ناموفق: {failed}")
                    return

                if text == "ارسال همه":
                    # ارسال به گروه‌ها
                    sent_groups = 0
                    async for dialog in client2.iter_dialogs():
                        if dialog.is_group:
                            try:
                                await client2.send_message(dialog.id, target_text)
                                sent_groups += 1
                                await asyncio.sleep(0.5)
                            except Exception:
                                pass
                    # ارسال به کاربران
                    users = load_users()
                    success, failed = 0, 0
                    for uid in users:
                        try:
                            await client2.send_message(int(uid), target_text)
                            success += 1
                        except Exception:
                            failed += 1
                        await asyncio.sleep(BROADCAST_DELAY)
                    await event.reply(f"✅ ارسال کامل شد. گروه‌ها: {sent_groups} | کاربران موفق: {success} | ناموفق: {failed}")
                    return

            # اگر SUDO لینک فرستاد، جوین شو
            match = re.search(invite_pattern, text)
            if match:
                await join_with_delay(match.group(1), event)

    except Exception:
        print("خطا در main_handler:", traceback.format_exc())

# ────── وقتی کاربر در پی‌وی به یوزربات پیام داد: ذخیره کن (فقط در PV)
@client2.on(events.NewMessage(incoming=True))
async def pv_handler(event):
    try:
        # فقط پی‌وی
        if not getattr(event, "is_private", False):
            return
        sender = getattr(event, "sender_id", None)
        if sender is None:
            return
        users = load_users()
        if sender not in users:
            users.append(sender)
            save_users(users)
            # ذخیره به محض اولین پیام در پی‌وی — می‌تونیم تشکر هم کنیم
            try:
                await event.reply("✅ شما در لیست پیام‌رسانی ثبت شدید. ممنون از پیام شما!")
            except:
                pass
    except Exception:
        print("خطا در pv_handler:", traceback.format_exc())

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
