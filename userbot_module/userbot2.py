# -*- coding: utf-8 -*-
"""
Ultra All-in-One Userbot (Fixed single-client version)
- Auto-join links (public + private)
- Silent user collector (group + private), filter out bots & deleted accounts
- Invite (اد) users to target chat with error handling
- Broadcast (ارسال کاربران / گروه‌ها / همه) with rate limits
- Dead-user cleaner (manual + periodic)
- Stats and admin commands (only SUDO)
- Logging to file
"""
import asyncio
import json
import os
import re
import time
import logging
import traceback
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.errors import (
    InviteHashExpiredError,
    InviteHashInvalidError,
    PeerFloodError,
    UserPrivacyRestrictedError,
    RPCError,
    FloodWaitError
)

# ============================
# ========== CONFIG ==========
# ============================
# ← مقدارهای زیر را با مقادیر خودت جایگزین کن
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

# مدیران (SUDO)
SUDO_USERS = [8588347189]   # آیدی‌های عددی مدیران را اینجا قرار بده

# فایل‌ها
USERS_FILE = "users_list.json"
STATS_FILE = "join_stats.json"
PM_TIMES_FILE = "pm_times.json"
ERROR_LOG = "errors.log"

# رفتارها / تنظیمات نرخ
JOIN_DELAY = 60            # فاصله بین join لینک‌ها (ثانیه)
BROADCAST_DELAY = 1.5      # فاصله بین ارسال پیام به کاربران (ثانیه)
INVITE_DELAY = 1.0         # فاصله بین دعوت‌ها
PM_COOLDOWN = 60 * 60      # cooldown پیام خوش‌آمد (ثانیه)
AUTO_CLEAN_INTERVAL = 60 * 60 * 6  # پاکسازی خودکار هر 6 ساعت (ثانیه)

# گزینه‌ها
SILENT_ADD = True         # True -> ذخیره بی‌صدا (بدون پیام خوش‌آمد)
AUTO_CLEAN_ENABLED = True
AUTO_JOIN_ENABLED = True
STORE_FROM_GROUPS = True
STORE_FROM_PV = True

# invite pattern
invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

# ============================
# ====== logging setup =======
# ============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(ERROR_LOG, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================
# ====== client setup ========
# ============================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ============================
# ====== utils: file io ======
# ============================
def ensure_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "groups": 0,
                "channels": 0,
                "banned_groups": 0,
                "__joined_groups__": [],
                "__joined_channels__": []
            }, f, ensure_ascii=False, indent=2)
    if not os.path.exists(PM_TIMES_FILE):
        with open(PM_TIMES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("خطا هنگام ذخیره فایل %s: %s", path, e)

def load_users():
    return load_json(USERS_FILE, [])

def save_users(u):
    save_json(USERS_FILE, u)

def load_stats():
    return load_json(STATS_FILE, {})

def save_stats(s):
    save_json(STATS_FILE, s)

def load_pm_times():
    return load_json(PM_TIMES_FILE, {})

def save_pm_times(d):
    save_json(PM_TIMES_FILE, d)

# ============================
# ====== helper funcs ========
# ============================
async def is_bot_entity(uid):
    """
    Check whether an entity is a bot or deleted quickly.
    Returns: (is_bot_or_deleted: bool, entity_or_none)
    """
    try:
        ent = await client.get_entity(uid)
        if getattr(ent, "deleted", False):
            return True, ent
        if getattr(ent, "bot", False):
            return True, ent
        return False, ent
    except Exception as e:
        logger.debug("get_entity failed for %s: %s", uid, e)
        return True, None

def is_sudo(uid):
    return uid in SUDO_USERS

# ============================
# ==== init joined chats =====
# ============================
LAST_JOIN_TIME = 0
JOIN_DELAY = 20  # فاصله بین join‌ها ۲۰ ثانیه

async def join_with_delay(invite_links, source_event=None):
    """
    invite_links: می‌تواند یک رشته یا لیست از لینک‌ها باشد.
    بعد از هر join، ۲۰ ثانیه صبر می‌کند.
    در انتها، یک پیام جمع‌بندی برای سودو ارسال می‌کند.
    """
    global LAST_JOIN_TIME
    if not AUTO_JOIN_ENABLED:
        return False, "Auto-join disabled"

    if isinstance(invite_links, str):
        invite_links = [invite_links]

    results = []

    for invite_link in invite_links:
        now = time.time()
        wait_time = LAST_JOIN_TIME + JOIN_DELAY - now
        if wait_time > 0:
            await asyncio.sleep(wait_time)

        LAST_JOIN_TIME = time.time()
        stats = load_stats()

        try:
            clean = invite_link.replace("https://", "").replace("http://", "").replace("t.me/", "").strip()

            if clean.startswith("+") or clean.startswith("joinchat/"):
                invite_hash = clean.replace("+", "").replace("joinchat/", "")
                await client(ImportChatInviteRequest(invite_hash))
                stats["groups"] = stats.get("groups", 0) + 1
                save_stats(stats)
                results.append((invite_link, True, "joined_private"))
            else:
                await client(JoinChannelRequest(clean))
                stats["channels"] = stats.get("channels", 0) + 1
                save_stats(stats)
                results.append((invite_link, True, "joined_public"))

        except InviteHashExpiredError:
            results.append((invite_link, False, "invite_expired"))
        except InviteHashInvalidError:
            results.append((invite_link, False, "invite_invalid"))
        except FloodWaitError as e:
            logger.warning("FloodWait during join: %s", e)
            results.append((invite_link, False, f"flood_wait_{getattr(e, 'seconds', 'x')}"))
        except Exception as e:
            logger.exception("خطا در join_with_delay:")
            results.append((invite_link, False, str(e)))

        # صبر ۲۰ ثانیه قبل از لینک بعدی
        await asyncio.sleep(20)

    # ارسال پیام جمع‌بندی به سودو
    if source_event and is_sudo(source_event.sender_id):
        msg_lines = []
        for link, ok, reason in results:
            status = "✅ Joined" if ok else f"❌ Failed ({reason})"
            msg_lines.append(f"{link} -> {status}")
        summary = "📋 Join summary:\n" + "\n".join(msg_lines)
        await source_event.reply(summary)

    return results

# ============================
# ======= join handling ======
# ============================
LAST_JOIN_TIME = 0

async def join_with_delay(invite_link, source_event=None):
    global LAST_JOIN_TIME
    if not AUTO_JOIN_ENABLED:
        return False, "Auto-join disabled"

    now = time.time()
    wait_time = LAST_JOIN_TIME + JOIN_DELAY - now
    if wait_time > 0:
        await asyncio.sleep(wait_time)

    LAST_JOIN_TIME = time.time()
    stats = load_stats()
    try:
        clean = invite_link.replace("https://", "").replace("http://", "")
        clean = clean.replace("t.me/", "").strip()

        if clean.startswith("+") or clean.startswith("joinchat/"):
            invite_hash = clean.replace("+", "").replace("joinchat/", "")
            await client(ImportChatInviteRequest(invite_hash))
            stats["groups"] = stats.get("groups", 0) + 1
            save_stats(stats)
            return True, "joined_private"
        else:
            await client(JoinChannelRequest(clean))
            stats["channels"] = stats.get("channels", 0) + 1
            save_stats(stats)
            return True, "joined_public"

    except InviteHashExpiredError:
        return False, "invite_expired"
    except InviteHashInvalidError:
        return False, "invite_invalid"
    except FloodWaitError as e:
        logger.warning("FloodWait during join: %s", e)
        return False, f"flood_wait_{getattr(e, 'seconds', 'x')}"
    except Exception as e:
        logger.exception("خطا در join_with_delay:")
        return False, str(e)

# ============================
# ===== invite / add users ===
# ============================
async def invite_users_to_target(target_chat_id, user_ids):
    stats = load_stats()
    added_count = 0
    for uid in user_ids:
        try:
            await client(InviteToChannelRequest(int(target_chat_id), [int(uid)]))
            added_count += 1
            await asyncio.sleep(INVITE_DELAY)
        except PeerFloodError:
            logger.warning("PeerFloodError هنگام دعوت -> توقف دعوت")
            stats["banned_groups"] = stats.get("banned_groups", 0) + 1
            save_stats(stats)
            break
        except UserPrivacyRestrictedError:
            stats["banned_groups"] = stats.get("banned_groups", 0) + 1
            save_stats(stats)
            continue
        except FloodWaitError as e:
            logger.warning("FloodWait during invite: %s", e)
            await asyncio.sleep(min(getattr(e, "seconds", 10), 60))
            continue
        except Exception:
            logger.exception("خطا در invite_users_to_target برای %s", uid)
            stats["banned_groups"] = stats.get("banned_groups", 0) + 1
            save_stats(stats)
            continue
    return added_count

# ============================
# ===== broadcast functions ===
# ============================
async def broadcast_to_users(message_text, user_list=None):
    users = user_list or load_users()
    success = 0
    failed = 0
    for uid in users:
        try:
            await client.send_message(int(uid), message_text)
            success += 1
        except PeerFloodError:
            logger.warning("PeerFloodError during broadcast")
            return success, failed + (len(users) - success)
        except FloodWaitError as e:
            logger.warning("FloodWait during broadcast: %s", e)
            await asyncio.sleep(min(getattr(e, "seconds", 10), 60))
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)
    return success, failed

async def broadcast_to_groups(message_text):
    sent = 0
    async for dialog in client.iter_dialogs():
        try:
            if dialog.is_group:
                await client.send_message(dialog.id, message_text)
                sent += 1
                await asyncio.sleep(0.5)
        except Exception:
            logger.exception("خطا در broadcast_to_groups برای dialog %s", dialog.id)
    return sent

# ============================
# ====== dead user cleaner ====
# ============================
async def clean_dead_users():
    users = load_users()
    cleaned = []
    for uid in users:
        try:
            entity = await client.get_entity(int(uid))
            if getattr(entity, "deleted", False):
                continue
            if getattr(entity, "bot", False):
                continue
            cleaned.append(uid)
        except Exception:
            continue
    save_users(cleaned)
    return len(users), len(cleaned)

# ============================
# ====== auto-clean scheduler ==
# ============================
async def auto_clean_loop():
    if not AUTO_CLEAN_ENABLED:
        return
    while True:
        try:
            logger.info("Auto-clean starting...")
            before, after = await clean_dead_users()
            logger.info("Auto-clean done: before=%s after=%s", before, after)
        except Exception:
            logger.exception("خطا در auto_clean_loop")
        await asyncio.sleep(AUTO_CLEAN_INTERVAL)

# ============================
# ====== event handlers =======
# ============================
@client.on(events.NewMessage(incoming=True))
async def main_handler(event):
    try:
        text = (event.raw_text or "").strip()
        sender = event.sender_id

        # فقط اگر Auto-Join فعال باشد
        if AUTO_JOIN_ENABLED:
            # پیدا کردن همه لینک‌ها در پیام
            links = re.findall(invite_pattern, text)
            if links:
                # join همه لینک‌ها یکی‌یکی با تاخیر
                await join_with_delay(links, source_event=event)
    except Exception:
        logger.exception("خطا در main_handler: %s", traceback.format_exc())

        # ذخیره بی‌صدا (group)
        if STORE_FROM_GROUPS and event.is_group:
            is_bad, ent = await is_bot_entity(sender)
            if not is_bad:
                users = load_users()
                if sender not in users:
                    users.append(sender)
                    save_users(users)
            match = re.search(invite_pattern, text)
            if match and AUTO_JOIN_ENABLED:
                ok, reason = await join_with_delay(match.group(1), event)
                if not ok:
                    logger.info("join failed from group: %s", reason)
            return

        # ذخیره بی‌صدا (pv)
        if STORE_FROM_PV and event.is_private:
            is_bad, ent = await is_bot_entity(sender)
            if not is_bad:
                users = load_users()
                if sender not in users:
                    users.append(sender)
                    save_users(users)
            match = re.search(invite_pattern, text)
            if match and AUTO_JOIN_ENABLED:
                ok, reason = await join_with_delay(match.group(1), event)
                if not ok:
                    logger.info("join failed from pv: %s", reason)
            return

        # ADMIN / SUDO commands
        if is_sudo(sender):
            # آمار
            if text.lower() in ["آمار", "/stats", "stats"]:
                stats = load_stats()
                users = load_users()
                await event.reply(
                    f"📊 آمار ربات:\n\n"
                    f"👥 کاربران ذخیره‌شده: `{len(users)}`\n"
                    f"📢 کانال‌ها: `{stats.get('channels', 0)}`\n"
                    f"👥 گروه‌ها: `{stats.get('groups', 0)}`\n"
                    f"⛔ گروه‌های بن شده: `{stats.get('banned_groups', 0)}`"
                )
                return

            # پاکسازی
            if text.lower() in ["پاکسازی بن", "/clean", "clean"]:
                before, after = await clean_dead_users()
                await event.reply(f"🧹 پاکسازی انجام شد:\nقبل: {before}\nبعد: {after}")
                return

            # اد
            if text.startswith("اد "):
                parts = text.split()
                if len(parts) < 2:
                    await event.reply("❌ فرمت: `اد تعداد [گروه_id]`")
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
                added = await invite_users_to_target(target_chat, target_users)
                remaining = users[num:]
                save_users(remaining)
                await event.reply(f"✅ تعداد {added} نفر اضافه شدند.")
                return

            # Broadcast با ریپلای
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_text = (reply_msg.message or reply_msg.raw_text or "").strip()
                if text == "ارسال کاربران":
                    users = load_users()
                    succ, fail = await broadcast_to_users(target_text, users)
                    await event.reply(f"✅ ارسال به کاربران: موفق {succ} | ناموفق {fail}")
                    return
                if text == "ارسال گروه":
                    sent = await broadcast_to_groups(target_text)
                    await event.reply(f"✅ پیام به {sent} گروه ارسال شد.")
                    return
                if text == "ارسال همه":
                    sent_groups = await broadcast_to_groups(target_text)
                    succ, fail = await broadcast_to_users(target_text, load_users())
                    await event.reply(f"✅ ارسال کامل شد.\nگروه‌ها: {sent_groups} | کاربران موفق: {succ} | ناموفق: {fail}")
                    return

            # manual join (SUDO can paste link and bot joins)
            match = re.search(invite_pattern, text)
            if match:
                ok, reason = await join_with_delay(match.group(1), event)
                await event.reply(f"Join result: {ok} | {reason}")
                return

    except Exception:
        logger.exception("خطا در main_handler: %s", traceback.format_exc())

# ============================
# ===== commands via pattern =
# ============================
@client.on(events.NewMessage(pattern=r"^/stats$"))
async def stats_cmd(event):
    if not is_sudo(event.sender_id):
        return
    stats = load_stats()
    users = load_users()
    await event.reply(
        f"📊 آمار ربات:\n\n"
        f"👥 کاربران ذخیره‌شده: `{len(users)}`\n"
        f"📢 کانال‌ها: `{stats.get('channels', 0)}`\n"
        f"👥 گروه‌ها: `{stats.get('groups', 0)}`\n"
        f"⛔ گروه‌های بن شده: `{stats.get('banned_groups', 0)}`"
    )

@client.on(events.NewMessage(pattern=r"^/clean$"))
async def clean_cmd(event):
    if not is_sudo(event.sender_id):
        return
    before, after = await clean_dead_users()
    await event.reply(f"🧹 پاکسازی انجام شد:\nقبل: {before}\nبعد: {after}")

# ============================
# ====== startup / wrappers ==
# ============================
async def start_userbot2():
    """Compatibility wrapper for bot.py"""
    ensure_files()
    await client.start()
    try:
        await init_joined_chats()
    except Exception:
        logger.exception("init_joined_chats failed in start_userbot2")
    if AUTO_CLEAN_ENABLED:
        asyncio.create_task(auto_clean_loop())
    await client.run_until_disconnected()

async def main():
    ensure_files()
    await client.start()
    logger.info("Userbot started.")
    try:
        await init_joined_chats()
    except Exception:
        logger.exception("init_joined_chats failed")
    if AUTO_CLEAN_ENABLED:
        asyncio.create_task(auto_clean_loop())
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception:
        logger.exception("Fatal error: %s", traceback.format_exc())
