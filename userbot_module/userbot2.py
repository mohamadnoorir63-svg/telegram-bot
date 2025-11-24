# -*- coding: utf-8 -*-
"""
Ultra All-in-One Userbot v3
- Auto-join links (public + private) in batches
- Silent user collector (group + private)
- Invite users to target chat
- Broadcast messages
- Dead-user cleaner (manual + periodic)
- Auto join from link channels every 1 minute
- SUDO-only commands & logging
"""
import asyncio
import json
import os
import re
import time
import logging
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
    FloodWaitError,
    RPCError
)

# ============================
# CONFIG
# ============================
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

LINK_CHANNEL = "https://t.me/Link4you"  # لینک کانال لینکدونی

async def auto_join_from_channel_loop():
    if not AUTO_JOIN_ENABLED:
        return
    last_joined = set()
    # تبدیل لینک یا یوزرنیم به entity.id
    channel_entity = await client.get_entity(LINK_CHANNEL)
    channel_id = channel_entity.id
    while True:
        try:
            async for msg in client.iter_messages(channel_id, limit=5):
                links = re.findall(invite_pattern, msg.message or "")
                for link in links:
                    if link not in last_joined:
                        await join_with_delay(link)
                        last_joined.add(link)
                        await asyncio.sleep(AUTO_JOIN_CHANNEL_INTERVAL)
        except Exception:
            logger.exception("خطا در auto_join_from_channel_loop")
            await asyncio.sleep(60)


USERS_FILE = "users_list.json"
STATS_FILE = "join_stats.json"
PM_TIMES_FILE = "pm_times.json"
ERROR_LOG = "errors.log"

JOIN_DELAY = 20          # فاصله بین join‌ها
BATCH_JOIN_COUNT = 5     # بعد از چند لینک دسته بعدی
BATCH_JOIN_DELAY = 120   # فاصله بین دسته‌ها (ثانیه)
AUTO_JOIN_CHANNEL_INTERVAL = 60  # هر ۱ دقیقه لینک بعدی از کانال

BROADCAST_DELAY = 1.5
INVITE_DELAY = 1
PM_COOLDOWN = 60*60
AUTO_CLEAN_INTERVAL = 60*60*6

SILENT_ADD = True
AUTO_CLEAN_ENABLED = True
AUTO_JOIN_ENABLED = True
STORE_FROM_GROUPS = True
STORE_FROM_PV = True

invite_pattern = r"(https?://t.me/[\w\d_-+/=]+)"

# ============================
# Logging setup
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
# Client setup
# ============================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ============================
# Utils: File IO
# ============================
def ensure_files():
    for f, default in [(USERS_FILE, []), 
                       (STATS_FILE, {"groups":0,"channels":0,"banned_groups":0,"__joined_groups__":[],"__joined_channels__":[]}),
                       (PM_TIMES_FILE, {})]:
        if not os.path.exists(f):
            with open(f,"w",encoding="utf-8") as file:
                json.dump(default,file,ensure_ascii=False,indent=2)

def load_json(path, default):
    try:
        with open(path,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
    except Exception as e:
        logger.exception("خطا هنگام ذخیره فایل %s: %s", path, e)

def load_users(): return load_json(USERS_FILE,[])
def save_users(u): save_json(USERS_FILE,u)
def load_stats(): return load_json(STATS_FILE,{})
def save_stats(s): save_json(STATS_FILE,s)
def load_pm_times(): return load_json(PM_TIMES_FILE,{})
def save_pm_times(d): save_json(PM_TIMES_FILE,d)

# ============================
# Helper functions
# ============================
async def is_bot_entity(uid):
    try:
        ent = await client.get_entity(uid)
        if getattr(ent,"deleted",False) or getattr(ent,"bot",False):
            return True, ent
        return False, ent
    except Exception as e:
        logger.debug("get_entity failed for %s: %s", uid, e)
        return True, None

def is_sudo(uid): return uid in SUDO_USERS

# ============================
# Join links with delay
# ============================
LAST_JOIN_TIME = 0
async def join_with_delay(invite_links, source_event=None):
    global LAST_JOIN_TIME
    if not AUTO_JOIN_ENABLED:
        return False, "Auto-join disabled"
    if isinstance(invite_links,str):
        invite_links = [invite_links]
    results = []
    for idx, link in enumerate(invite_links,1):
        now = time.time()
        wait_time = LAST_JOIN_TIME + JOIN_DELAY - now
        if wait_time>0:
            await asyncio.sleep(wait_time)
        LAST_JOIN_TIME = time.time()
        stats = load_stats()
        try:
            clean = link.replace("https://","").replace("http://","").replace("t.me/","").strip()
            if clean.startswith("+") or clean.startswith("joinchat/"):
                invite_hash = clean.replace("+","").replace("joinchat/","")
                await client(ImportChatInviteRequest(invite_hash))
                stats["groups"]=stats.get("groups",0)+1
                results.append((link,True,"joined_private"))
            else:
                await client(JoinChannelRequest(clean))
                stats["channels"]=stats.get("channels",0)+1
                results.append((link,True,"joined_public"))
            save_stats(stats)
        except (InviteHashExpiredError,InviteHashInvalidError) as e:
            results.append((link,False,str(e)))
        except FloodWaitError as e:
            results.append((link,False,f"flood_wait_{getattr(e,'seconds',10)}"))
        except Exception as e:
            results.append((link,False,str(e)))
        # دسته‌بندی هر 5 لینک
        if idx%BATCH_JOIN_COUNT==0:
            await asyncio.sleep(BATCH_JOIN_DELAY)
        else:
            await asyncio.sleep(JOIN_DELAY)
    # گزارش به سودو
    if source_event and is_sudo(source_event.sender_id):
        summary=[]
        for l,ok,reason in results:
            status = "✅ Joined" if ok else f"❌ Failed ({reason})"
            summary.append(f"{l} -> {status}")
        await source_event.reply("📋 Join summary:\n"+ "\n".join(summary))
    return results

# ============================
# Invite / Add Users
# ============================
MAX_CONCURRENT_INVITES = 3
BATCH_SIZE = 10
BATCH_DELAY = 20

async def invite_users_to_target(target_chat_id,user_ids):
    stats=load_stats()
    added=0;failed=0;blocked_privacy=0;flood_errors=0
    sem = asyncio.Semaphore(MAX_CONCURRENT_INVITES)
    async def invite_single(uid):
        nonlocal added,failed,blocked_privacy,flood_errors
        async with sem:
            try:
                entity = await client.get_entity(int(uid))
                if getattr(entity,"deleted",False) or getattr(entity,"bot",False):
                    failed+=1; return
                await client(InviteToChannelRequest(int(target_chat_id),[int(uid)]))
                added+=1
                await asyncio.sleep(INVITE_DELAY)
            except UserPrivacyRestrictedError:
                blocked_privacy+=1
            except PeerFloodError:
                flood_errors+=1
                logger.warning("⚠ PeerFlood → توقف ۳۰ دقیقه")
                await asyncio.sleep(1800)
            except FloodWaitError as e:
                sec=getattr(e,'seconds',10)
                logger.warning(f"⏳ FloodWait: {sec} ثانیه")
                await asyncio.sleep(sec)
            except Exception as e:
                failed+=1
                logger.error(f"❌ خطا در دعوت {uid}: {e}")
    for i in range(0,len(user_ids),BATCH_SIZE):
        batch=user_ids[i:i+BATCH_SIZE]
        tasks=[invite_single(uid) for uid in batch]
        await asyncio.gather(*tasks)
        logger.info(f"Batch invited: {len(batch)} → sleeping {BATCH_DELAY}s...")
        await asyncio.sleep(BATCH_DELAY)
    logger.info(f"🎯 نتیجه نهایی دعوت → موفق {added} | ناموفق {failed} | پرایوسی {blocked_privacy} | Flood {flood_errors}")
    return added

# ============================
# Broadcast functions
# ============================
async def broadcast_to_users(message_text,user_list=None):
    users=user_list or load_users()
    success=0;failed=0
    for uid in users:
        try:
            await client.send_message(int(uid),message_text)
            success+=1
        except PeerFloodError:
            logger.warning("PeerFloodError during broadcast")
            return success, failed+(len(users)-success)
        except FloodWaitError as e:
            logger.warning("FloodWait during broadcast: %s", e)
            await asyncio.sleep(min(getattr(e,'seconds',10),60))
            failed+=1
        except Exception:
            failed+=1
        await asyncio.sleep(BROADCAST_DELAY)
    return success,failed

async def broadcast_to_groups(message_text):
    sent=0
    async for dialog in client.iter_dialogs():
        try:
            if dialog.is_group:
                await client.send_message(dialog.id,message_text)
                sent+=1
                await asyncio.sleep(0.5)
        except Exception:
            logger.exception("خطا در broadcast_to_groups برای dialog %s",dialog.id)
    return sent

# ============================
# Dead user cleaner
# ============================
async def clean_dead_users():
    users=load_users()
    cleaned=[]
    for uid in users:
        try:
            ent = await client.get_entity(int(uid))
            if getattr(ent,"deleted",False) or getattr(ent,"bot",False):
                continue
            cleaned.append(uid)
        except:
            continue
    save_users(cleaned)
    return len(users),len(cleaned)

# ============================
# Auto-clean loop
# ============================
async def auto_clean_loop():
    if not AUTO_CLEAN_ENABLED:
        return
    while True:
        try:
            logger.info("Auto-clean starting...")
            before,after=await clean_dead_users()
            logger.info("Auto-clean done: before=%s after=%s",before,after)
        except:
            logger.exception("خطا در auto_clean_loop")
        await asyncio.sleep(AUTO_CLEAN_INTERVAL)

# ============================
# Auto join from link channel
# ============================
async def auto_join_from_channel_loop():
    if not AUTO_JOIN_ENABLED:
        return
    last_joined = set()
    while True:
        try:
            async for msg in client.iter_messages(LINK_CHANNEL_ID, limit=5):
                links = re.findall(invite_pattern, msg.message or "")
                for link in links:
                    if link not in last_joined:
                        await join_with_delay(link)
                        last_joined.add(link)
                        await asyncio.sleep(AUTO_JOIN_CHANNEL_INTERVAL)
        except Exception:
            logger.exception("خطا در auto_join_from_channel_loop")
            await asyncio.sleep(60)

# ============================
# Event handler
# ============================
@client.on(events.NewMessage(incoming=True))
async def main_handler(event):
    try:
        text=(event.raw_text or "").strip()
        sender=event.sender_id

        # Auto join links
        if AUTO_JOIN_ENABLED:
            links=re.findall(invite_pattern,text)
            if links:
                await join_with_delay(links,source_event=event)

        # Silent add
        if STORE_FROM_GROUPS and event.is_group:
            is_bad,_=await is_bot_entity(sender)
            if not is_bad:
                users=load_users()
                if sender not in users:
                    users.append(sender)
                    save_users(users)

        if STORE_FROM_PV and event.is_private:
            is_bad,_=await is_bot_entity(sender)
            if not is_bad:
                users=load_users()
                if sender not in users:
                    users.append(sender)
                    save_users(users)

        # SUDO commands
        if is_sudo(sender):
            if text.lower() in ["آمار","/stats","stats"]:
                stats=load_stats()
                users=load_users()
                await event.reply(f"📊 آمار ربات:\n\n👥 کاربران ذخیره‌شده: {len(users)}\n📢 کانال‌ها: {stats.get('channels',0)}\n👥 گروه‌ها: {stats.get('groups',0)}\n⛔ گروه‌های بن شده: {stats.get('banned_groups',0)}")
                return
            if text.lower() in ["پاکسازی بن","/clean","clean"]:
                before,after=await clean_dead_users()
                await event.reply(f"🧹 پاکسازی انجام شد:\nقبل: {before}\nبعد: {after}")
                return
            if text.startswith("اد "):
                parts=text.split()
                if len(parts)<2:
                    await event.reply("❌ فرمت: `اد تعداد [گروه_id]`"); return
                try: num=int(parts[1])
                except: await event.reply("❌ عدد معتبر نیست."); return
                target_chat=event.chat_id if len(parts)==2 else int(parts[2])
                users=load_users()
                if not users: await event.reply("❌ لیست کاربران خالی است."); return
                target_users=users[:num]
                added=await invite_users_to_target(target_chat,target_users)
                remaining=users[num:]
                save_users(remaining)
                await event.reply(f"✅ تعداد {added} نفر اضافه شدند.")
                return
            if event.is_reply:
                reply_msg=await event.get_reply_message()
                target_text=(reply_msg.message or reply_msg.raw_text or "").strip()
                if text=="ارسال کاربران":
                    users=load_users()
                    succ,fail=await broadcast_to_users(target_text,users)
                    await event.reply(f"✅ ارسال به کاربران: موفق {succ} | ناموفق {fail}")
                    return
                if text=="ارسال گروه":
                    sent=await broadcast_to_groups(target_text)
                    await event.reply(f"✅ پیام به {sent} گروه ارسال شد.")
                    return
                if text=="ارسال همه":
                    sent_groups=await broadcast_to_groups(target_text)
                    succ,fail=await broadcast_to_users(target_text,load_users())
                    await event.reply(f"✅ ارسال کامل شد.\nگروه‌ها: {sent_groups} | کاربران موفق: {succ} | ناموفق: {fail}")
                    return
            # Manual join
            match=re.search(invite_pattern,text)
            if match:
                ok,reason=await join_with_delay(match.group(1),event)
                await event.reply(f"Join result: {ok} | {reason}")
                return
    except Exception:
        logger.exception("خطا در main_handler: %s", traceback.format_exc())

# ============================
# Startup
# ============================
async def main():
    ensure_files()
    await client.start()
    logger.info("Userbot started.")
    if AUTO_CLEAN_ENABLED:
        asyncio.create_task(auto_clean_loop())
    if AUTO_JOIN_ENABLED:
        asyncio.create_task(auto_join_from_channel_loop())
    await client.run_until_disconnected()

if __name__=="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception:
        logger.exception("Fatal error: %s", traceback.format_exc())
