# userbot.py
# Telethon userbot — دستورات فارسی بدون نقطه
# نیاز: telethon 1.x, و تنظیم env: API_ID, API_HASH, SESSION_STRING (اختیاری)
import os
import asyncio
import json
from datetime import datetime, timedelta
from telethon import TelegramClient, events, errors, functions
from telethon.sessions import StringSession
from telethon.tl.types import ChatBannedRights

# ---------- پیکربندی ----------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")  # اگر نیست، client فایل session می‌سازد

# آیدی(های) صاحب/ادمین — تو گذاشتی این آیدی: 7089376754
# اگر خواستی می‌تونی با ویرایش ENV متغیر ADMIN_IDS="7089376754,..." استفاده کنی
OWNER_IDS = set()
try:
    env_admins = os.getenv("ADMIN_IDS", "")
    if env_admins:
        OWNER_IDS.update(int(x.strip()) for x in env_admins.split(",") if x.strip())
except:
    pass
OWNER_IDS.add(7089376754)

if not API_ID or not API_HASH:
    raise SystemExit("API_ID یا API_HASH تنظیم نشده‌اند. (ENV متغیرها را بررسی کن)")

# فایل ذخیرهٔ سکوت‌ها
MUTES_FILE = "userbot_mutes.json"
if not os.path.exists(MUTES_FILE):
    with open(MUTES_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def load_mutes():
    try:
        with open(MUTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_mutes(data):
    try:
        with open(MUTES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[MUTES SAVE ERROR]", e)

# ---------- client ----------
client = TelegramClient(StringSession(SESSION) if SESSION else "userbot.session", API_ID, API_HASH)

# وضعیت نابودی (برای توقف)
nuke_task = {"running": False, "cancel": False}

# کمکی برای تقسیم لیست
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# ---------- Command handlers ----------

@client.on(events.NewMessage(pattern=r"^(?i)پینگ$"))
async def cmd_ping(event):
    await event.reply("🏓 یوزربات فعاله ✅")

# نابود سریع — مثال: "نابود" یا "نابود 500" یا "نابود 5000"
@client.on(events.NewMessage(pattern=r"^(?i)نابود(?:\s+(\d+))?$"))
async def cmd_nuke(event):
    sender = await event.get_sender()
    sender_id = sender.id if sender else None
    if sender_id not in OWNER_IDS:
        return await event.reply("🚫 شما مجوز اجرای این فرمان را ندارید.")

    m = event.pattern_match.group(1)
    limit = int(m) if m else 5000
    if limit > 20000:
        limit = 20000

    # پیام تأیید مختصر
    status_msg = await event.reply(f"🔥 در حال آماده‌سازی برای حذف تا {limit} پیام...")

    chat = await event.get_chat()
    chat_id = event.chat_id

    # شروع نابودی
    nuke_task["running"] = True
    nuke_task["cancel"] = False

    try:
        messages = await client.get_messages(chat_id, limit=limit)
        if not messages:
            await status_msg.edit("ℹ️ هیچ پیامی برای حذف یافت نشد.")
            nuke_task["running"] = False
            return

        ids = [m.id for m in messages]
        total = len(ids)
        deleted = 0
        failed = 0
        BATCH = 100

        await status_msg.edit(f"🧹 حذف آغاز شد — {total} پیام جمع‌آوری شده.")

        for batch in chunks(ids, BATCH):
            if nuke_task.get("cancel"):
                await status_msg.edit(f"⛔ عملیات متوقف شد — حذف شده: {deleted}/{total}")
                nuke_task["running"] = False
                nuke_task["cancel"] = False
                return

            try:
                await client.delete_messages(chat_id, batch, revoke=True)
                deleted += len(batch)
            except errors.FloodWait as fw:
                await status_msg.edit(f"⚠️ FloodWait: صبر {fw.seconds}s ...")
                await asyncio.sleep(fw.seconds + 1)
                try:
                    await client.delete_messages(chat_id, batch, revoke=True)
                    deleted += len(batch)
                except Exception as e:
                    print("[NUKE] after flood error:", e)
                    failed += len(batch)
            except Exception as e:
                print("[NUKE] batch delete error:", e)
                failed += len(batch)

            try:
                await status_msg.edit(f"🧹 حذف شد: {deleted}/{total} (ناموفق: {failed})")
            except: pass

            await asyncio.sleep(0.35)

        await status_msg.edit(f"✅ پاکسازی پایان یافت.\n✔️ حذف شده: {deleted}\n❗ ناموفق: {failed}")
    except Exception as e:
        await status_msg.edit(f"❌ خطا در پاکسازی: {e}")
    finally:
        nuke_task["running"] = False
        nuke_task["cancel"] = False

# توقف عملیات نابود (فوری)
@client.on(events.NewMessage(pattern=r"^(?i)توقف$"))
async def cmd_stop(event):
    if nuke_task.get("running"):
        nuke_task["cancel"] = True
        await event.reply("⛔ درخواست توقف ارسال شد — در حال توقف عملیات...")
    else:
        await event.reply("ℹ️ هیچ عملیات نابودی در حال اجرا نیست.")

# بن کاربر — باید روی پیام کاربر ریپلای کنی: "بن"
@client.on(events.NewMessage(pattern=r"^(?i)بن$"))
async def cmd_ban(event):
    if not event.is_reply:
        return await event.reply("🔹 برای بن کردن روی پیام فرد ریپلای کن و بن بزن.")
    sender = await event.get_sender()
    sender_id = sender.id if sender else None
    # فقط OWNER می‌تواند بن کند
    if sender_id not in OWNER_IDS:
        return await event.reply("🚫 شما مجوز بن کردن را ندارید.")

    target = await event.get_reply_message()
    if not target:
        return await event.reply("⚠️ پیام ریپلای معتبر نیست.")
    user = target.from_id.user_id if target.from_id else None
    if not user:
        return await event.reply("⚠️ اطلاعات کاربر قابل دریافت نیست.")

    try:
        # ban: view_messages=True
        rights = ChatBannedRights(
            until_date=None,
            view_messages=True
        )
        await client(functions.channels.EditBannedRequest(event.chat_id, user, rights))
        await event.reply(f"⛔ کاربر بن شد.")
    except Exception as e:
        await event.reply(f"⚠️ خطا در بن: {e}")

# سکوت کردن — مثال‌ها:
# سکوت 30 ثانیه   -> ساکت به مدت 30 ثانیه
# سکوت 5 دقیقه    -> ساکت به مدت 5 دقیقه
# سکوت           -> ساکت دائم (تا حذف سکوت)
@client.on(events.NewMessage(pattern=r"^(?i)سکوت(?:\s+(\d+))?(?:\s*(ثانیه|دقیقه))?$"))
async def cmd_mute(event):
    if not event.is_reply:
        return await event.reply("🔹 برای سکوت روی پیام فرد ریپلای کن و بنویس: سکوت 30 ثانیه (یا سکوت 5 دقیقه یا سکوت).")
    target_msg = await event.get_reply_message()
    target_id = target_msg.from_id.user_id if target_msg.from_id else None
    if not target_id:
        return await event.reply("⚠️ کاربر قابل شناسایی نیست.")

    # parse time
    num = event.pattern_match.group(1)
    unit = event.pattern_match.group(2) or ""
    seconds = None
    if num:
        try:
            n = int(num)
            if "دقیقه" in unit:
                seconds = n * 60
            else:
                seconds = n  # default seconds
        except:
            seconds = None

    until = None
    if seconds:
        until = datetime.utcnow() + timedelta(seconds=seconds)

    try:
        # send_messages=True means banned from sending -> so to mute set send_messages=True
        rights = ChatBannedRights(
            until_date=until,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True
        )
        await client(functions.channels.EditBannedRequest(event.chat_id, target_id, rights))

        # ذخیره در فایل برای قابلیت حذف سکوت
        mutes = load_mutes()
        cid = str(event.chat_id)
        mutes.setdefault(cid, {})
        mutes[cid][str(target_id)] = {
            "until": until.isoformat() if until else "permanent",
            "by": (await event.get_sender()).id,
            "ts": datetime.utcnow().isoformat()
        }
        save_mutes(mutes)

        if until:
            await event.reply(f"🤐 {target_msg.sender.first_name} برای {num} {unit} سکوت شد.")
        else:
            await event.reply(f"🤐 {target_msg.sender.first_name} سکوت دائم شد.")
    except Exception as e:
        await event.reply(f"⚠️ خطا در سکوت: {e}")

# حذف سکوت — ریپلای به کاربر: "حذف سکوت"
# یا "حذف سکوت همه" -> فقط OWNER ها می‌توانند اجرا کنند
@client.on(events.NewMessage(pattern=r"^(?i)حذف\s+سکوت(?:\s+همه)?$"))
async def cmd_unmute(event):
    text = event.raw_text.strip()
    is_all = text.endswith("همه") or "همه" in text
    # اگر حذف همه خواسته شد فقط OWNER
    sender = await event.get_sender()
    if is_all and (sender.id not in OWNER_IDS):
        return await event.reply("🚫 فقط صاحب مجاز به حذف سکوت همه است.")

    if is_all:
        mutes = load_mutes()
        cid = str(event.chat_id)
        if cid in mutes:
            failed = 0
            removed = 0
            for uid in list(mutes[cid].keys()):
                try:
                    rights = ChatBannedRights(
                        until_date=None,
                        send_messages=False,
                        send_media=False,
                        send_stickers=False,
                        send_gifs=False,
                        send_games=False,
                        send_inline=False,
                        embed_links=False
                    )
                    await client(functions.channels.EditBannedRequest(event.chat_id, int(uid), rights))
                    removed += 1
                    del mutes[cid][uid]
                except Exception as e:
                    print("[UNMUTE ALL ERROR]", e)
                    failed += 1
            save_mutes(mutes)
            await event.reply(f"✅ حذف سکوت انجام شد: {removed} حذف / {failed} ناموفق")
        else:
            await event.reply("ℹ️ هیچ سکوت ذخیره‌شده‌ای برای این گروه نیست.")
        return

    # حالت عادی: باید روی پیام کاربر ریپلای باشه
    if not event.is_reply:
        return await event.reply("🔹 برای حذف سکوت روی پیام فرد ریپلای بزن و «حذف سکوت» را بنویس.")
    target_msg = await event.get_reply_message()
    uid = target_msg.from_id.user_id if target_msg.from_id else None
    if not uid:
        return await event.reply("⚠️ کاربر قابل شناسایی نیست.")

    try:
        rights = ChatBannedRights(
            until_date=None,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            embed_links=False
        )
        await client(functions.channels.EditBannedRequest(event.chat_id, uid, rights))

        # حذف از فایل ذخیره
        mutes = load_mutes()
        cid = str(event.chat_id)
        if cid in mutes and str(uid) in mutes[cid]:
            del mutes[cid][str(uid)]
            save_mutes(mutes)

        await event.reply("🔊 سکوت کاربر برداشته شد.")
    except Exception as e:
        await event.reply(f"⚠️ خطا در حذف سکوت: {e}")

# اخطار — فقط ریپلای روی پیام
@client.on(events.NewMessage(pattern=r"^(?i)اخطار$"))
async def cmd_warn(event):
    if not event.is_reply:
        return await event.reply("🔹 برای اخطار روی پیام کاربر ریپلای کن و «اخطار» بنویس.")
    target_msg = await event.get_reply_message()
    name = target_msg.sender.first_name if target_msg.sender else "کاربر"
    await event.reply(f"⚠️ اخطار صادر شد برای {name}")

# ---------- شروع userbot ----------
async def start_userbot():
    print("🔌 شروع Userbot ...")
    await client.start()
    me = await client.get_me()
    print(f"✅ Userbot آنلاین شد: {me.first_name} [{me.id}]")
    # client.run_until_disconnected() را در caller اجرا خواهیم کرد، این فانکشن فقط استارت می‌دهد
    # اما برای سادگی، اینجا صبر می‌کنیم:
    await client.run_until_disconnected()

# اگر فایل مستقیماً اجرا شود:
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_userbot())
