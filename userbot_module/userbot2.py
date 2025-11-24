# -*- coding: utf-8 -*-
"""
Ultra All-in-One Userbot — کامل و مقاوم
ویژگی‌ها:
 - Auto-join لینک‌ها (عمومی + خصوصی) به صورت دسته‌ای با نرخ‌دهی
 - ذخیرهٔ بی‌صدا از گروه‌ها و پی‌وی (فیلتر ربات / حذف‌شده)
 - دعوت (اد) کاربران به گروه/کانال (اد همه یا اد N)
 - ارسال انبوه (ارسال کاربران / گروه‌ها / همه)
 - پاکسازی مخاطبین مرده (خودکار و دستی)
 - خواندن لینک‌ها از یک کانال لینکدونی و جوین خودکار (با یوزرنیم یا لینک کانال)
 - مدیریت قطع اتصال: reconnect و keep-alive
 - گزارش به سودو پس از جوین‌ها و دستورها
"""
import asyncio
import json
import os
import re
import time
import logging
import traceback
from typing import List, Tuple

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.errors import (
    InviteHashExpiredError,
    InviteHashInvalidError,
    PeerFloodError,
    UserPrivacyRestrictedError,
    FloodWaitError,
)

# ============================
# ======= CONFIG ============
# ============================
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

# سودوها (ID عددی)
SUDO_USERS = [8588347189]

# کانال لینکدونی — میتونی یوزرنیم یا لینک کامل بذاری، مثلاً "Link4you" یا "https://t.me/Link4you"
LINK_CHANNEL = "Link4you"

# فایل‌ها
USERS_FILE = "users_list.json"
STATS_FILE = "join_stats.json"
PM_TIMES_FILE = "pm_times.json"
ERROR_LOG = "errors.log"

# نرخ‌ها و پارامترها
JOIN_DELAY = 20                 # ثانیه بین هر جوین عادی
BATCH_JOIN_COUNT = 5            # بعد از این تعداد لینک، دسته بعدی اعمال می‌شود
BATCH_JOIN_DELAY = 120          # ثانیه تا دسته بعدی (هر BATCH_JOIN_COUNT لینک)
AUTO_JOIN_CHANNEL_INTERVAL = 60 # استخراج لینک از کانال لینکدونی: هر لینک X ثانیه جوین می‌شود

MAX_CONCURRENT_INVITES = 3      # تعداد همزمان دعوت‌ها در هر دسته
BATCH_INVITE_SIZE = 10          # اندازه هر دسته برای دعوت
BATCH_INVITE_DELAY = 20         # فاصله بین دسته‌های دعوت

BROADCAST_DELAY = 1.5
INVITE_DELAY = 1
PM_COOLDOWN = 60 * 60
AUTO_CLEAN_INTERVAL = 60 * 60 * 6

# رفتارها
SILENT_ADD = True
AUTO_CLEAN_ENABLED = True
AUTO_JOIN_ENABLED = True
STORE_FROM_GROUPS = True
STORE_FROM_PV = True

# regex لینک (بدون خطای range)
invite_pattern = r"(https?://t\.me/[A-Za-z0-9_+\-/=]+)"

# ============================
# ===== Logging setup ========
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
# ===== Client setup =========
# ============================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ============================
# ===== File helpers ========
# ============================
def ensure_files():
    defaults = [
        (USERS_FILE, []),
        (STATS_FILE, {"groups": 0, "channels": 0, "banned_groups": 0, "__joined_groups__": [], "__joined_channels__": []}),
        (PM_TIMES_FILE, {})
    ]
    for path, default in defaults:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False, indent=2)

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
# ===== Helper funcs =========
# ============================
async def is_bot_entity(uid) -> Tuple[bool, object]:
    try:
        ent = await client.get_entity(uid)
        if getattr(ent, "deleted", False) or getattr(ent, "bot", False):
            return True, ent
        return False, ent
    except Exception as e:
        logger.debug("get_entity failed for %s: %s", uid, e)
        return True, None

def is_sudo(uid: int) -> bool:
    return uid in SUDO_USERS

# ============================
# ===== Connection helpers ===
# ============================
async def ensure_connected():
    """Ensure the telethon client is connected (non-blocking)"""
    if not client.is_connected():
        try:
            await client.connect()
            logger.info("🔌 client connected")
        except Exception as e:
            logger.warning("⚠️ cannot connect client: %s", e)

async def keep_alive_loop():
    """Periodically do a lightweight call to keep connection alive / reconnect if needed"""
    while True:
        try:
            if not client.is_connected():
                logger.warning("⚠ client disconnected — trying to connect...")
                await ensure_connected()
            else:
                # lightweight call
                await client.get_me()
        except Exception:
            logger.exception("خطا در keep_alive_loop")
            try:
                await client.connect()
            except:
                pass
        await asyncio.sleep(40)

# ============================
# ===== Join handling ========
# ============================
LAST_JOIN_TIME = 0

def _clean_invite_string(link: str) -> str:
    return link.replace("https://", "").replace("http://", "").replace("t.me/", "").strip()

async def join_single_link(link: str) -> Tuple[str, bool, str]:
    """
    Attempt to join a single t.me link.
    Returns (link, ok, reason_text)
    """
    stats = load_stats()
    try:
        clean = _clean_invite_string(link)
        if clean.startswith("+") or clean.startswith("joinchat/"):
            invite_hash = clean.replace("+", "").replace("joinchat/", "")
            await client(ImportChatInviteRequest(invite_hash))
            stats["groups"] = stats.get("groups", 0) + 1
            save_stats(stats)
            return link, True, "joined_private"
        else:
            await client(JoinChannelRequest(clean))
            stats["channels"] = stats.get("channels", 0) + 1
            save_stats(stats)
            return link, True, "joined_public"
    except InviteHashExpiredError:
        return link, False, "invite_expired"
    except InviteHashInvalidError:
        return link, False, "invite_invalid"
    except FloodWaitError as e:
        return link, False, f"flood_wait_{getattr(e, 'seconds', 10)}"
    except Exception as e:
        logger.exception("خطا در join_single_link:")
        return link, False, str(e)

async def join_with_delay(invite_links, source_event=None):
    """
    invite_links: string or list
    - join links one by one respecting JOIN_DELAY and batching rules (BATCH_JOIN_COUNT/BATCH_JOIN_DELAY)
    - replies summary to source_event if sender is sudo
    """
    global LAST_JOIN_TIME
    if not AUTO_JOIN_ENABLED:
        return []

    if isinstance(invite_links, str):
        invite_links = [invite_links]

    results = []
    for idx, link in enumerate(invite_links, start=1):
        await ensure_connected()
        # enforce inter-join delay using LAST_JOIN_TIME
        now = time.time()
        wait_time = LAST_JOIN_TIME + JOIN_DELAY - now
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        LAST_JOIN_TIME = time.time()

        res = await join_single_link(link)
        results.append(res)

        # batching waits
        if idx % BATCH_JOIN_COUNT == 0:
            logger.info("Batch join reached — sleeping %s seconds", BATCH_JOIN_DELAY)
            await asyncio.sleep(BATCH_JOIN_DELAY)
        else:
            # ensure minimum delay between joins
            await asyncio.sleep(JOIN_DELAY)

    # if the trigger was from sudo, send summary
    try:
        if source_event and is_sudo(getattr(source_event, "sender_id", None)):
            lines = []
            for l, ok, reason in results:
                status = "✅ Joined" if ok else f"❌ Failed ({reason})"
                lines.append(f"{l} -> {status}")
            await source_event.reply("📋 Join summary:\n" + "\n".join(lines))
    except Exception:
        logger.exception("خطا در ارسال گزارش join summary")

    return results

# ============================
# ===== Invite (اد) users ====
# ============================
async def invite_users_to_target(target_entity, user_ids: List[int]):
    """
    target_entity: chat id (int) or username string acceptable by Telethon
    user_ids: list of user ids (ints or strings convertible)
    This function will:
      - invite users in batches (BATCH_INVITE_SIZE) with concurrency limit
      - respect INVITE_DELAY and BATCH_INVITE_DELAY
      - handle privacy/flood exceptions and log stats
    """
    await ensure_connected()

    stats = load_stats()
    added = 0
    failed = 0
    blocked_privacy = 0
    flood_errors = 0

    sem = asyncio.Semaphore(MAX_CONCURRENT_INVITES)

    async def invite_single(uid):
        nonlocal added, failed, blocked_privacy, flood_errors
        async with sem:
            try:
                ent = await client.get_entity(int(uid))
                if getattr(ent, "deleted", False) or getattr(ent, "bot", False):
                    failed += 1
                    return
                # InviteToChannelRequest expects (channel, users_list)
                await client(InviteToChannelRequest(int(target_entity), [int(uid)]))
                added += 1
                await asyncio.sleep(INVITE_DELAY)
            except UserPrivacyRestrictedError:
                blocked_privacy += 1
            except PeerFloodError:
                flood_errors += 1
                logger.warning("⚠ PeerFlood detected — pausing 30 minutes")
                await asyncio.sleep(1800)
            except FloodWaitError as e:
                sec = getattr(e, "seconds", 10)
                logger.warning("⏳ FloodWait during invite: %s", sec)
                await asyncio.sleep(sec)
            except Exception as e:
                failed += 1
                logger.exception("خطا در invite_single %s: %s", uid, e)

    # batch-run invites
    for i in range(0, len(user_ids), BATCH_INVITE_SIZE):
        batch = user_ids[i:i + BATCH_INVITE_SIZE]
        tasks = [invite_single(uid) for uid in batch]
        await asyncio.gather(*tasks)
        logger.info("Invited batch of %s users, sleeping %s seconds", len(batch), BATCH_INVITE_DELAY)
        await asyncio.sleep(BATCH_INVITE_DELAY)

    logger.info("Invite summary -> added: %s failed: %s privacy_blocked: %s flood_errors: %s", added, failed, blocked_privacy, flood_errors)
    return added, failed, blocked_privacy, flood_errors

# ============================
# ===== Broadcast funcs ======
# ============================
async def broadcast_to_users(message_text: str, user_list: List[int] = None):
    users = user_list or load_users()
    success = 0
    failed = 0
    for uid in users:
        try:
            await client.send_message(int(uid), message_text)
            success += 1
        except PeerFloodError:
            logger.warning("PeerFlood during broadcast -> stopping")
            return success, failed + (len(users) - success)
        except FloodWaitError as e:
            logger.warning("FloodWait during broadcast: %s", e)
            await asyncio.sleep(min(getattr(e, "seconds", 10), 60))
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)
    return success, failed

async def broadcast_to_groups(message_text: str):
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
# ===== Dead user cleaner ====
# ============================
async def clean_dead_users():
    users = load_users()
    cleaned = []
    for uid in users:
        try:
            ent = await client.get_entity(int(uid))
            if getattr(ent, "deleted", False) or getattr(ent, "bot", False):
                continue
            cleaned.append(uid)
        except Exception:
            # treat as dead/unreachable and drop
            continue
    save_users(cleaned)
    return len(users), len(cleaned)

# ============================
# ===== Auto-clean loop ======
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
# ===== Auto-join from link channel ======
# ============================
async def auto_join_from_channel_loop():
    if not AUTO_JOIN_ENABLED:
        return

    await ensure_connected()

    # resolve channel entity (accept username or link)
    try:
        channel_entity = await client.get_entity(LINK_CHANNEL)
        channel_id = channel_entity.id
        logger.info("Auto-join channel resolved: %s -> %s", LINK_CHANNEL, channel_id)
    except Exception as e:
        logger.exception("خطا در resolve کانال لینکدونی: %s", e)
        # اگر resolve نشد، تلاش مجدد هر 60 ثانیه
        while True:
            try:
                await asyncio.sleep(15)
                channel_entity = await client.get_entity(LINK_CHANNEL)
                channel_id = channel_entity.id
                logger.info("Resolved channel on retry: %s -> %s", LINK_CHANNEL, channel_id)
                break
            except Exception:
                logger.warning("هنوز نتوانستم کانال را resolve کنم، دوباره تلاش می‌کنم...")
                await asyncio.sleep(30)

    seen = set()
    while True:
        try:
            await ensure_connected()
            async for msg in client.iter_messages(channel_id, limit=10):
                text = msg.message or ""
                links = re.findall(invite_pattern, text)
                for link in links:
                    if link in seen:
                        continue
                    # join link
                    res = await join_with_delay(link)
                    # mark seen regardless of result to avoid repeated attempts
                    seen.add(link)
                    # بین لینک‌های کانال یک تأخیر کوتاه بگذار
                    await asyncio.sleep(AUTO_JOIN_CHANNEL_INTERVAL)
            # بعد از یک دور خواندن، منتظر بمان
            await asyncio.sleep(30)
        except ConnectionError:
            logger.warning("Connection lost while auto-joining from channel — reconnecting...")
            try:
                await client.connect()
            except:
                pass
            await asyncio.sleep(5)
        except Exception:
            logger.exception("خطا در auto_join_from_channel_loop")
            await asyncio.sleep(20)

# ============================
# ===== Event handler ========
# ============================
@client.on(events.NewMessage(incoming=True))
async def main_handler(event):
    try:
        await ensure_connected()
        text = (event.raw_text or "").strip()
        sender = event.sender_id

        # Auto join links contained in ANY message
        if AUTO_JOIN_ENABLED:
            links = re.findall(invite_pattern, text)
            if links:
                # pass event to get summary if sudo triggered it
                asyncio.create_task(join_with_delay(links, source_event=event))

        # Silent save from groups
        if STORE_FROM_GROUPS and getattr(event, "is_group", False):
            is_bad, _ = await is_bot_entity(sender)
            if not is_bad:
                users = load_users()
                if sender not in users:
                    users.append(sender)
                    save_users(users)

        # Silent save from pv
        if STORE_FROM_PV and getattr(event, "is_private", False):
            is_bad, _ = await is_bot_entity(sender)
            if not is_bad:
                users = load_users()
                if sender not in users:
                    users.append(sender)
                    save_users(users)

        # Admin / SUDO commands
        if is_sudo(sender):
            lower = text.lower()
            if lower in ["آمار", "/stats", "stats"]:
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

            if lower in ["پاکسازی بن", "/clean", "clean"]:
                before, after = await clean_dead_users()
                await event.reply(f"🧹 پاکسازی انجام شد:\nقبل: {before}\nبعد: {after}")
                return

            # دعوت (اد)
            # فرمت‌ها:
            #   اد N              -> دعوت N نفر از بالای لیست به گروه فعلی (event.chat_id)
            #   اد همه            -> دعوت همه کاربران ذخیره‌شده به گروه فعلی
            #   اد N <chat_id>    -> دعوت N نفر به chat_id مشخص
            #   اد همه <chat_id>  -> دعوت همه به chat_id مشخص
            if text.startswith("اد "):
                parts = text.split()
                if len(parts) >= 2:
                    target_chat = event.chat_id  # پیش‌فرض گروه فعلی
                    if len(parts) == 2:
                        param = parts[1]
                    else:
                        # اگر دو پارامتر یا بیشتر: parts[1] می‌تواند 'همه' یا عدد؛ اگر پارامتر سوم هست آن را به عنوان chat id بگیر
                        param = parts[1]
                        if len(parts) >= 3:
                            try:
                                target_chat = int(parts[2])
                            except:
                                # ممکن است username گروه باشد
                                try:
                                    ent = await client.get_entity(parts[2])
                                    target_chat = ent.id
                                except Exception:
                                    await event.reply("❌ chat id معتبر نیست.")
                                    return
                    users = load_users()
                    if not users:
                        await event.reply("❌ لیست کاربران خالی است.")
                        return

                    if param == "همه" or param == "all":
                        to_invite = users[:]
                    else:
                        try:
                            num = int(param)
                            to_invite = users[:num]
                        except:
                            await event.reply("❌ پارامتر عدد یا 'همه' باشد.")
                            return

                    # run invite and reply summary
                    await event.reply("⏳ شروع دعوت ...")
                    added, failed, blocked_privacy, flood_errors = await invite_users_to_target(int(target_chat), to_invite)
                    # remove invited slice from stored users (we remove the same count as attempted to avoid retries)
                    remaining = users[len(to_invite):]
                    save_users(remaining)
                    await event.reply(f"✅ دعوت انجام شد. موفق: {added} | ناموفق: {failed} | پرایوسی: {blocked_privacy} | Flood: {flood_errors}")
                    return

            # Broadcast commands via reply
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

            # Manual join: سودو می‌فرستد لینک و یوزربات جوین می‌شود و گزارش داده می‌شود
            match = re.search(invite_pattern, text)
            if match:
                await event.reply("⏳ تلاش برای جوین لینک(ها)...")
                res = await join_with_delay([match.group(0)], source_event=event)
                return

    except Exception:
        logger.exception("خطا در main_handler: %s", traceback.format_exc())

# ============================
# ===== Startup / wrapper ====
# ============================
async def start_userbot2():
    """Compatibility wrapper for external bot.py that imports start_userbot2"""
    await main()

async def main():
    ensure_files()
    await ensure_connected()
    logger.info("Userbot starting...")

    # background tasks
    if AUTO_CLEAN_ENABLED:
        asyncio.create_task(auto_clean_loop())
    asyncio.create_task(keep_alive_loop())
    if AUTO_JOIN_ENABLED:
        asyncio.create_task(auto_join_from_channel_loop())

    # run handlers
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception:
        logger.exception("Fatal error: %s", traceback.format_exc())
