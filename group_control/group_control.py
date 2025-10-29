# ======================= Group Control System — Full Single File =======================
# python-telegram-bot v20+
# همه‌ی سیستم‌ها: قفل‌ها (+Alias)، قفل/بازگروه+زمان‌بندی، پاکسازی، پین زمانی،
# فیلتر کلمات، مدیران، «اصل»، «لقب»، تگ، ثبت فعالیت، و هسته Alias + فرمان مرکزی.

import os, json, re, asyncio
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes
from telegram.error import BadRequest, RetryAfter

# ─────────────────────────────── Files & Storage ───────────────────────────────
GROUP_CTRL_FILE = "group_control.json"   # locks, admins, auto_lock ...
ALIASES_FILE    = "aliases.json"
FILTER_FILE     = "filters.json"
ORIGINS_FILE    = "origins.json"         # origins + last activity (for tags)
NICKS_FILE      = "nicks.json"
BACKUP_DIR      = "backups"

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def _load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Load error {path}: {e} — trying backup...")
    bkp = os.path.join(BACKUP_DIR, f"backup_{os.path.basename(path)}")
    if os.path.exists(bkp):
        try:
            with open(bkp, "r", encoding="utf-8") as f:
                print(f"♻️ Recovered {path} from backup ✅")
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Backup invalid {bkp}: {e}")
    return default

def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        bkp = os.path.join(BACKUP_DIR, f"backup_{os.path.basename(path)}")
        with open(bkp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Save error {path}: {e}")

group_data  = _load_json(GROUP_CTRL_FILE, {})  # {"chat_id": {"locks": {...}, "admins": [...], "auto_lock": {...}}}
ALIASES     = _load_json(ALIASES_FILE, {})
filters_db  = _load_json(FILTER_FILE, {})
origins_db  = _load_json(ORIGINS_FILE, {})     # {"chat_id": {"origins": {uid: txt}, "users": {uid: iso}}}
nicks_db    = _load_json(NICKS_FILE, {})       # {"chat_id": {uid: nick}}

# ─────────────────────────────── Access Control ───────────────────────────────
SUDO_IDS = [1777319036, 7089376754]

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except:
        return False

async def _is_admin_or_sudo_uid(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

# ─────────────────────────────── LOCKS (25 types) ───────────────────────────────
LOCK_TYPES = {
    "links": "ارسال لینک",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
    "files": "ارسال فایل",
    "voices": "ارسال ویس",
    "vmsgs": "ارسال ویدیو مسیج",
    "stickers": "ارسال استیکر",
    "gifs": "ارسال گیف",
    "media": "ارسال همه رسانه‌ها",
    "forward": "ارسال فوروارد",
    "ads": "ارسال تبلیغ/تبچی",
    "usernames": "ارسال یوزرنیم/تگ",
    "mention": "منشن با @",
    "bots": "افزودن ربات",
    "join": "ورود عضو جدید",
    "tgservices": "پیام‌های سیستمی تلگرام",
    "joinmsg": "پیام ورود",
    "arabic": "حروف عربی (غیر فارسی)",
    "english": "حروف انگلیسی",
    "text": "ارسال پیام متنی",
    "audio": "ارسال آهنگ/موسیقی",
    "emoji": "پیام فقط ایموجی",
    "caption": "ارسال کپشن",
    "edit": "ویرایش پیام",
    "reply": "ریپلای/پاسخ",
    "all": "قفل کلی"
}

PERSIAN_TO_KEY = {
    "لینک":"links", "عکس":"photos","تصویر":"photos","ویدیو":"videos","فیلم":"videos","فایل":"files","ویس":"voices",
    "ویدیو مسیج":"vmsgs","ویدیو مسج":"vmsgs","استیکر":"stickers","گیف":"gifs","رسانه":"media","فوروارد":"forward",
    "تبچی":"ads","تبلیغ":"ads","یوزرنیم":"usernames","تگ":"usernames","منشن":"mention","ربات":"bots","ورود":"join",
    "سرویس":"tgservices","پیام ورود":"joinmsg","عربی":"arabic","انگلیسی":"english","متن":"text","آهنگ":"audio",
    "موزیک":"audio","ایموجی":"emoji","کپشن":"caption","ویرایش":"edit","ریپلای":"reply","کلی":"all"
}

def _locks_get(chat_id: int) -> dict:
    g = group_data.get(str(chat_id), {})
    return g.get("locks", {})

def _locks_set(chat_id: int, key: str, status: bool):
    cid = str(chat_id)
    g = group_data.get(cid, {})
    locks = g.get("locks", {})
    locks[key] = bool(status)
    g["locks"] = locks
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)

async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ همچین قفلی نیست.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    chat = update.effective_chat
    if _locks_get(chat.id).get(key):
        return await update.message.reply_text(f"⚠️ «{LOCK_TYPES[key]}» از قبل قفل بوده.")
    _locks_set(chat.id, key, True)
    await update.message.reply_text(f"🔒 قفل <b>{LOCK_TYPES[key]}</b> فعال شد.", parse_mode="HTML")

async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ همچین قفلی نیست.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    chat = update.effective_chat
    if not _locks_get(chat.id).get(key):
        return await update.message.reply_text(f"🔓 «{LOCK_TYPES[key]}» از قبل باز بوده.")
    _locks_set(chat.id, key, False)
    await update.message.reply_text(f"🔓 قفل <b>{LOCK_TYPES[key]}</b> باز شد.", parse_mode="HTML")

async def handle_locks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    locks = _locks_get(update.effective_chat.id)
    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست.", parse_mode="HTML")
    text = "🧱 <b>وضعیت قفل‌های گروه:</b>\n\n"
    for k, d in LOCK_TYPES.items():
        text += f"▫️ {d}: {'🔒 فعال' if locks.get(k) else '🔓 غیرفعال'}\n"
    await update.message.reply_text(text, parse_mode="HTML")

# قفل/بازکردن به فارسی: «قفل لینک»، «بازکردن لینک»
_lock_cmd_regex = re.compile(r"^(قفل|باز ?کردن)\s+(.+)$")

def _map_persian_to_key(name: str) -> str | None:
    name = name.strip()
    if name in PERSIAN_TO_KEY:
        return PERSIAN_TO_KEY[name]
    for fa, key in PERSIAN_TO_KEY.items():
        if fa in name:
            return key
    for key in LOCK_TYPES:
        if key in name:
            return key
    return None

async def handle_locks_with_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    tx = update.message.text.strip().lower()
    m = _lock_cmd_regex.match(tx)
    if not m:
        return
    action, rest = m.groups()
    key = _map_persian_to_key(rest)
    if not key:
        return await update.message.reply_text("⚠️ نام قفل نامعتبر است.")
    if action.startswith("قفل"):
        return await handle_lock(update, context, key)
    else:
        return await handle_unlock(update, context, key)

# ───── اجرای قفل‌ها روی پیام‌ها
_english_pat = re.compile(r"[A-Za-z]")
_arabic_specific = re.compile(r"[يكۀةًٌٍَُِّْٰ]")
_emoji_pat = re.compile(
    r"[\U0001F300-\U0001F6FF\U0001F900-\U0001FAFF\U0001F1E6-\U0001F1FF"
    r"\U00002700-\U000027BF\U00002600-\U000026FF]"
)

def _emoji_only(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    non = re.sub(_emoji_pat, "", s)
    return non.strip() == ""

async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user:
        return

    # معاف: مدیر/سودو
    if await _is_admin_or_sudo_uid(context, chat.id, user.id):
        return

    locks = _locks_get(chat.id)
    if not locks:
        # اگر فیلتر کلمات داریم، پایین‌تر چک می‌شود (ادغام شده)
        pass

    text = (msg.text or msg.caption or "")  # کپشن هم
    text_l = text.lower()

    async def _del(reason: str):
        try:
            await msg.delete()
        except:
            return
        try:
            await context.bot.send_message(chat.id, f"🚫 پیام <b>{user.first_name}</b> حذف شد.\n🎯 دلیل: <b>{reason}</b>", parse_mode="HTML")
        except:
            pass

    # قفل کلی
    if locks.get("all"):
        return await _del("قفل کلی")

    # قفل متن
    if msg.text and locks.get("text"):
        return await _del("ارسال پیام متنی")

    # لینک‌ها
    if locks.get("links"):
        if "http://" in text_l or "https://" in text_l or "t.me/" in text_l:
            return await _del("ارسال لینک")
        if msg.entities:
            for e in msg.entities:
                if e.type in (MessageEntity.URL, MessageEntity.TEXT_LINK):
                    return await _del("ارسال لینک")

    # یوزرنیم/منشن
    if locks.get("usernames") and ("@" in text_l or (msg.entities and any(e.type == MessageEntity.MENTION for e in msg.entities))):
        return await _del("ارسال یوزرنیم/تگ")
    if locks.get("mention") and ("@" in text_l or (msg.entities and any(e.type == MessageEntity.MENTION for e in msg.entities))):
        return await _del("منشن")

    # رسانه
    if locks.get("photos") and msg.photo:
        return await _del("ارسال عکس")
    if locks.get("videos") and msg.video:
        return await _del("ارسال ویدیو")
    if locks.get("gifs") and msg.animation:
        return await _del("ارسال گیف")
    if locks.get("files") and msg.document:
        return await _del("ارسال فایل")
    if locks.get("audio") and (msg.audio or (msg.document and getattr(msg.document, "mime_type", "").startswith("audio/"))):
        return await _del("ارسال آهنگ/موسیقی")
    if locks.get("voices") and msg.voice:
        return await _del("ارسال ویس")
    if locks.get("vmsgs") and msg.video_note:
        return await _del("ارسال ویدیو مسیج")
    if locks.get("media") and (msg.photo or msg.video or msg.animation or msg.document or msg.audio or msg.voice or msg.video_note):
        return await _del("ارسال رسانه")

    # کپشن
    if locks.get("caption") and msg.caption:
        return await _del("ارسال کپشن")

    # فوروارد
    if locks.get("forward") and (msg.forward_from or msg.forward_from_chat):
        return await _del("ارسال فوروارد")

    # تبلیغ/تبچی
    if locks.get("ads"):
        if any(w in text_l for w in ["join", "channel", "تبچی", "تبلیغ", "free followers", "free views"]):
            return await _del("ارسال تبلیغ/تبچی")

    # زبان
    if locks.get("english") and _english_pat.search(text):
        return await _del("حروف انگلیسی")
    if locks.get("arabic") and _arabic_specific.search(text):
        return await _del("حروف عربی")

    # ایموجی
    if locks.get("emoji") and msg.text and _emoji_only(msg.text):
        return await _del("پیام فقط ایموجی")

    # ریپلای
    if locks.get("reply") and msg.reply_to_message:
        return await _del("ریپلای/پاسخ")

    # ── فیلتر کلمات (ادغام شده)
    chat_id = str(chat.id)
    chat_filters = filters_db.get(chat_id, [])
    if msg.text and chat_filters:
        tl = msg.text.lower()
        for w in chat_filters:
            if w and w in tl:
                return await _del(f"کلمه فیلترشده: «{w}»")

# رویدادهای ورود/ربات/سرویس
async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not msg.new_chat_members:
        return
    locks = _locks_get(chat.id)
    if not locks:
        return
    for m in msg.new_chat_members:
        if locks.get("bots") and m.is_bot:
            try:
                await context.bot.ban_chat_member(chat.id, m.id)
                await context.bot.unban_chat_member(chat.id, m.id)  # kick
            except: pass
            try: await msg.delete()
            except: pass
            continue
        if locks.get("join"):
            try:
                await context.bot.ban_chat_member(chat.id, m.id)
                await context.bot.unban_chat_member(chat.id, m.id)
            except: pass
            try: await msg.delete()
            except: pass
            continue
        if locks.get("joinmsg"):
            try: await msg.delete()
            except: pass

async def handle_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not chat:
        return
    if _locks_get(chat.id).get("tgservices"):
        try: await msg.delete()
        except: pass

async def handle_edited_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    edited = update.edited_message or update.edited_channel_post
    if not edited:
        return
    chat = edited.chat
    user = edited.from_user
    locks = _locks_get(chat.id)
    if not locks:
        return
    if await _is_admin_or_sudo_uid(context, chat.id, user.id):
        return
    if locks.get("edit"):
        try: await edited.delete()
        except: pass

# ─────────────────────── Group lock/unlock + Auto lock ───────────────────────
async def handle_lockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را قفل کنند!")
    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))
        await update.message.reply_text(
            f"🔒 <b>گروه قفل شد!</b>\n📅 {datetime.now().strftime('%H:%M - %d/%m/%Y')}\n👑 {update.effective_user.first_name}",
            parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

async def handle_unlockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را باز کنند!")
    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=True))
        await update.message.reply_text(
            f"🔓 <b>گروه باز شد!</b>\n📅 {datetime.now().strftime('%H:%M - %d/%m/%Y')}\n👑 {update.effective_user.first_name}",
            parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

async def handle_auto_lockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند قفل خودکار تنظیم کنند!")
    chat_id = str(update.effective_chat.id)
    args = context.args
    if len(args) != 2:
        return await update.message.reply_text(
            "🕒 استفاده:\n<code>قفل خودکار گروه 23:00 07:00</code>", parse_mode="HTML")
    start, end = args
    g = group_data.get(chat_id, {})
    g["auto_lock"] = {"enabled": True, "start": start, "end": end}
    group_data[chat_id] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text(
        f"✅ قفل خودکار فعال شد.\n⏰ از {start} تا {end} هر روز.", parse_mode="HTML")

async def handle_disable_auto_lock(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    chat_id = str(update.effective_chat.id)
    g = group_data.get(chat_id, {})
    if "auto_lock" not in g or not g["auto_lock"].get("enabled"):
        return await update.message.reply_text("ℹ️ قفل خودکار فعال نیست.")
    g["auto_lock"]["enabled"] = False
    group_data[chat_id] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text("❌ قفل خودکار غیرفعال شد.")

async def auto_group_lock_scheduler(context):
    now = datetime.now().time()
    for chat_id, data in list(group_data.items()):
        auto = data.get("auto_lock", {})
        if not auto.get("enabled"):
            continue
        try:
            from datetime import time as _t
            s = datetime.strptime(auto["start"], "%H:%M").time()
            e = datetime.strptime(auto["end"], "%H:%M").time()
        except:
            continue
        try:
            if s > e:
                in_lock = now >= s or now <= e
            else:
                in_lock = s <= now <= e
            cid = int(chat_id)
            await context.bot.set_chat_permissions(cid, ChatPermissions(can_send_messages=not in_lock))
        except Exception as ex:
            print(f"auto lock err {chat_id}: {ex}")

# ─────────────────────────────── Clean System ───────────────────────────────
async def handle_clean(update, context):
    """پاکسازی: عدد/کامل/کاربر خاص (ریپلای)"""
    user = update.effective_user
    chat = update.effective_chat
    message = update.message
    args = context.args if context.args else []

    if not await is_authorized(update, context):
        return await message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    limit = 100
    mode = "range"
    target_id = None

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        mode = "user"
    elif args and args[0].isdigit():
        limit = min(int(args[0]), 1000)
        mode = "count"
    elif any(w in " ".join(args).lower() for w in ["all", "همه", "کامل", "full"]):
        limit = 1000
        mode = "full"

    deleted = 0
    last_id = message.message_id
    batch = []

    async def safe_delete(mid):
        try:
            await context.bot.delete_message(chat.id, mid)
            return 1
        except (BadRequest, RetryAfter):
            return 0
        except:
            return 0

    for _ in range(limit):
        last_id -= 1
        if last_id <= 0:
            break
        try:
            fwd = await context.bot.forward_message(chat.id, chat.id, last_id)
            sender = fwd.forward_from.id if fwd.forward_from else None
            await context.bot.delete_message(chat.id, fwd.message_id)
            if mode == "user" and sender != target_id:
                continue
            batch.append(asyncio.create_task(safe_delete(last_id)))
            if len(batch) >= 50:
                res = await asyncio.gather(*batch)
                deleted += sum(res)
                batch = []
                await asyncio.sleep(0.4)
        except Exception:
            continue

    if batch:
        res = await asyncio.gather(*batch)
        deleted += sum(res)

    try:
        await context.bot.delete_message(chat.id, message.message_id)
    except:
        pass

    labels = {
        "user": "پاکسازی پیام‌های کاربر خاص",
        "count": f"پاکسازی عددی ({limit} پیام)",
        "full": "پاکسازی کامل",
        "range": "پاکسازی عمومی"
    }
    report = (
        f"🧹 <b>گزارش پاکسازی</b>\n\n"
        f"🏷 حالت: {labels[mode]}\n"
        f"👤 توسط: {user.first_name}\n"
        f"🗑 حذف‌شده: {deleted}\n"
        f"🕒 {datetime.now().strftime('%H:%M:%S - %Y/%m/%d')}"
    )
    try:
        await context.bot.send_message(user.id, report, parse_mode="HTML")
    except:
        await message.reply_text(report, parse_mode="HTML")

# ─────────────────────────────── Pin / Unpin (Timed) ───────────────────────────────
async def handle_pin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند پین کنند!")
    msg = update.message
    chat = update.effective_chat
    if not msg.reply_to_message:
        return await msg.reply_text("🔹 روی پیام مورد نظر ریپلای بزن و «پن» بنویس.")
    text = msg.text.lower().strip()
    duration = None
    for w in text.split():
        if w.isdigit():
            duration = int(w); break
    try:
        await context.bot.pin_chat_message(chat.id, msg.reply_to_message.message_id)
        if duration:
            await msg.reply_text(f"📌 پین شد و {duration} دقیقه بعد حذف می‌شود.", parse_mode="HTML")
            await asyncio.sleep(duration * 60)
            try:
                await context.bot.unpin_chat_message(chat.id, msg.reply_to_message.message_id)
                await context.bot.send_message(chat.id, f"⌛ پین خودکار حذف شد (پس از {duration} دقیقه).")
            except:
                pass
        else:
            await msg.reply_text("📍 پیام با موفقیت پین شد.", parse_mode="HTML")
    except Exception as e:
        await msg.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

async def handle_unpin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.message.reply_text("📍 تمام پین‌ها حذف شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")
        # ─────────────────────────────── User Management (Ban / Mute / Warn) ───────────────────────────────
 # سایر importها بالا
from datetime import datetime, timedelta
import asyncio
from telegram import ChatPermissions

def _ensure_user_system(chat_id: str):
    """اطمینان از وجود ساختار بن / سکوت / اخطار برای گروه"""
    if chat_id not in group_data:
        group_data[chat_id] = {}
    g = group_data[chat_id]
    g.setdefault("bans", [])
    g.setdefault("mutes", {})
    g.setdefault("warns", {})
    group_data[chat_id] = g


# 🔒 کمکی برای بررسی نقش کاربر
async def _check_protected_target(update, context, target):
    """بررسی اینکه آیا هدف، خود ربات یا مدیر/سودو است"""
    bot_id = context.bot.id
    if target.id == bot_id:
        await update.message.reply_text("😅 من نمی‌تونم روی خودم کاری انجام بدم!")
        return True
    if target.id in SUDO_IDS:
        await update.message.reply_text("😎 من نمی‌تونم سازنده‌ام رو محدود کنم!")
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, target.id)
        if member.status in ("administrator", "creator"):
            await update.message.reply_text("👮‍♂️ من نمی‌تونم مدیر گروه رو محدود کنم!")
            return True
    except:
        pass
    return False


# 📛 بن کاربر
async def handle_ban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند بن کنند!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای بزن.")
    target = update.message.reply_to_message.from_user
    if await _check_protected_target(update, context, target):
        return
    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    bans = group_data[cid]["bans"]
    if str(target.id) in bans:
        return await update.message.reply_text("⚠️ کاربر از قبل بن شده.")
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        bans.append(str(target.id))
        group_data[cid]["bans"] = bans
        _save_json(GROUP_CTRL_FILE, group_data)
        await update.message.reply_text(f"⛔ {target.first_name} بن شد!", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")


# 🟢 حذف بن
async def handle_unban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام بن‌شده ریپلای بزن.")
    target = update.message.reply_to_message.from_user
    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    bans = group_data[cid]["bans"]
    if str(target.id) not in bans:
        return await update.message.reply_text("⚠️ این کاربر بن نیست.")
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        bans.remove(str(target.id))
        group_data[cid]["bans"] = bans
        _save_json(GROUP_CTRL_FILE, group_data)
        await update.message.reply_text(f"✅ {target.first_name} از بن آزاد شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")


# 📋 لیست بن‌ها
async def handle_list_bans(update, context):
    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    bans = group_data[cid]["bans"]
    if not bans:
        return await update.message.reply_text("ℹ️ لیست بن خالی است.")
    txt = "🚫 <b>لیست کاربران بن‌شده:</b>\n\n"
    for i, uid in enumerate(bans, 1):
        txt += f"{i}. <a href='tg://user?id={uid}'>کاربر</a>\n"
    await update.message.reply_text(txt, parse_mode="HTML")


# 🤐 سکوت کاربر (اختیاری با زمان)
async def handle_mute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند سکوت کنند!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای بزن.")
    target = update.message.reply_to_message.from_user
    if await _check_protected_target(update, context, target):
        return

    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    mutes = group_data[cid]["mutes"]

    duration = 0
    text = update.message.text.lower()
    if "ثانیه" in text:
        nums = [int(s) for s in text.split() if s.isdigit()]
        duration = nums[0] if nums else 20
        delta = timedelta(seconds=duration)
    elif "دقیقه" in text:
        nums = [int(s) for s in text.split() if s.isdigit()]
        duration = nums[0] if nums else 1
        delta = timedelta(minutes=duration)
    else:
        delta = None

    until = datetime.now() + delta if delta else None
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        mutes[str(target.id)] = until.isoformat() if until else "permanent"
        group_data[cid]["mutes"] = mutes
        _save_json(GROUP_CTRL_FILE, group_data)
        if until:
            await update.message.reply_text(
                f"🤐 {target.first_name} به مدت {duration} {'ثانیه' if 'ثانیه' in text else 'دقیقه'} ساکت شد.",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(f"🤐 {target.first_name} ساکت شد (بدون زمان).", parse_mode="HTML")

        if until:
            async def _auto_unmute():
                await asyncio.sleep(delta.total_seconds())
                try:
                    await context.bot.restrict_chat_member(
                        update.effective_chat.id,
                        target.id,
                        ChatPermissions(can_send_messages=True),
                    )
                    del mutes[str(target.id)]
                    group_data[cid]["mutes"] = mutes
                    _save_json(GROUP_CTRL_FILE, group_data)
                    await context.bot.send_message(update.effective_chat.id, f"✅ سکوت {target.first_name} تمام شد.")
                except:
                    pass
            asyncio.create_task(_auto_unmute())
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")


# 🔊 حذف سکوت
async def handle_unmute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام فرد ساکت ریپلای بزن.")
    target = update.message.reply_to_message.from_user
    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    mutes = group_data[cid]["mutes"]
    if str(target.id) not in mutes:
        return await update.message.reply_text("⚠️ این کاربر در سکوت نیست.")
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id, ChatPermissions(can_send_messages=True)
        )
        del mutes[str(target.id)]
        group_data[cid]["mutes"] = mutes
        _save_json(GROUP_CTRL_FILE, group_data)
        await update.message.reply_text(f"🔊 سکوت {target.first_name} برداشته شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")


# 📋 لیست سکوت‌ها
async def handle_list_mutes(update, context):
    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    mutes = group_data[cid]["mutes"]
    if not mutes:
        return await update.message.reply_text("ℹ️ هیچ کاربری در سکوت نیست.")
    txt = "🤐 <b>لیست کاربران در سکوت:</b>\n\n"
    for i, (uid, until) in enumerate(mutes.items(), 1):
        if until == "permanent":
            txt += f"{i}. <a href='tg://user?id={uid}'>کاربر</a> → دائمی\n"
        else:
            t = datetime.fromisoformat(until).strftime("%H:%M:%S")
            txt += f"{i}. <a href='tg://user?id={uid}'>کاربر</a> → تا {t}\n"
    await update.message.reply_text(txt, parse_mode="HTML")


# ⚠️ اخطار کاربر
async def handle_warn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای بزن.")
    target = update.message.reply_to_message.from_user
    if await _check_protected_target(update, context, target):
        return

    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    warns = group_data[cid]["warns"]
    count = warns.get(str(target.id), 0) + 1
    warns[str(target.id)] = count
    group_data[cid]["warns"] = warns
    _save_json(GROUP_CTRL_FILE, group_data)
    if count >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
            await update.message.reply_text(
                f"⚠️ {target.first_name} سومین اخطارش را گرفت و بن شد.", parse_mode="HTML"
            )
            group_data[cid]["bans"].append(str(target.id))
            del warns[str(target.id)]
            _save_json(GROUP_CTRL_FILE, group_data)
        except:
            pass
    else:
        await update.message.reply_text(f"⚠️ اخطار {count}/3 برای {target.first_name}", parse_mode="HTML")


# 🧹 حذف اخطار کاربر
async def handle_unwarn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای بزن.")
    target = update.message.reply_to_message.from_user
    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    warns = group_data[cid]["warns"]
    if str(target.id) not in warns:
        return await update.message.reply_text("ℹ️ کاربر اخطاری ندارد.")
    del warns[str(target.id)]
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text(f"✅ اخطار {target.first_name} حذف شد.", parse_mode="HTML")


# 📋 لیست اخطارها
async def handle_list_warns(update, context):
    cid = str(update.effective_chat.id)
    _ensure_user_system(cid)
    warns = group_data[cid]["warns"]
    if not warns:
        return await update.message.reply_text("ℹ️ لیست اخطارها خالی است.")
    txt = "⚠️ <b>لیست اخطارها:</b>\n\n"
    for i, (uid, c) in enumerate(warns.items(), 1):
        txt += f"{i}. <a href='tg://user?id={uid}'>کاربر</a> → {c}/3 اخطار\n"
    await update.message.reply_text(txt, parse_mode="HTML")
# ─────────────────────────────── Admins Management ───────────────────────────────
async def handle_addadmin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند مدیر اضافه کنند!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای بزن.")
    target = update.message.reply_to_message.from_user
    cid = str(update.effective_chat.id)
    g = group_data.get(cid, {})
    admins = g.get("admins", [])
    if str(target.id) in admins:
        return await update.message.reply_text("⚠️ این کاربر قبلاً مدیر شده.")
    admins.append(str(target.id))
    g["admins"] = admins
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text(f"👑 {target.first_name} مدیر شد ✅", parse_mode="HTML")

async def handle_removeadmin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام مدیر ریپلای بزن.")
    target = update.message.reply_to_message.from_user
    cid = str(update.effective_chat.id)
    g = group_data.get(cid, {})
    admins = g.get("admins", [])
    if str(target.id) not in admins:
        return await update.message.reply_text("⚠️ این کاربر مدیر نیست.")
    admins.remove(str(target.id))
    g["admins"] = admins
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text(f"❌ {target.first_name} از مدیران حذف شد.", parse_mode="HTML")

async def handle_admins(update, context):
    cid = str(update.effective_chat.id)
    admins = group_data.get(cid, {}).get("admins", [])
    if not admins:
        return await update.message.reply_text("ℹ️ هنوز هیچ مدیری ثبت نشده.", parse_mode="HTML")
    txt = "👑 <b>لیست مدیران:</b>\n\n" + "\n".join([f"{i+1}. <a href='tg://user?id={aid}'>مدیر</a>" for i, aid in enumerate(admins)])
    await update.message.reply_text(txt, parse_mode="HTML")

async def handle_clearadmins(update, context):
    if update.effective_user.id not in SUDO_IDS:
        return await update.message.reply_text("🚫 فقط سودو مجاز است!")
    cid = str(update.effective_chat.id)
    if cid not in group_data or "admins" not in group_data[cid]:
        return await update.message.reply_text("ℹ️ لیست مدیران خالی است.")
    group_data[cid]["admins"] = []
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text("🧹 لیست مدیران پاک شد.", parse_mode="HTML")

# ─────────────────────────────── Filters (words) ───────────────────────────────
async def _can_manage(update, context):
    return await is_authorized(update, context)

async def handle_addfilter(update, context):
    if not await _can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیر یا سودو!")
    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: افزودن فیلتر [کلمه]")
    word = " ".join(context.args).strip().lower()
    cid = str(update.effective_chat.id)
    lst = filters_db.get(cid, [])
    if word in lst:
        return await update.message.reply_text("⚠️ از قبل فیلتر شده.")
    lst.append(word)
    filters_db[cid] = lst
    _save_json(FILTER_FILE, filters_db)
    await update.message.reply_text(f"✅ «{word}» فیلتر شد.", parse_mode="HTML")

async def handle_delfilter(update, context):
    if not await _can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیر یا سودو!")
    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: حذف فیلتر [کلمه]")
    word = " ".join(context.args).strip().lower()
    cid = str(update.effective_chat.id)
    lst = filters_db.get(cid, [])
    if word not in lst:
        return await update.message.reply_text("⚠️ چنین کلمه‌ای در فیلتر نیست.")
    lst.remove(word)
    filters_db[cid] = lst
    _save_json(FILTER_FILE, filters_db)
    await update.message.reply_text(f"🗑️ «{word}» از فیلتر حذف شد.", parse_mode="HTML")

async def handle_filters(update, context):
    cid = str(update.effective_chat.id)
    lst = filters_db.get(cid, [])
    if not lst:
        return await update.message.reply_text("ℹ️ فیلترها خالی است.")
    txt = "🚫 <b>کلمات فیلتر شده:</b>\n\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(lst, 1)])
    await update.message.reply_text(txt, parse_mode="HTML")

# ─────────────────────────────── Origins (اصل) ───────────────────────────────
async def _can_manage_origin(update, context):
    return await is_authorized(update, context)

def _ensure_chat_in_origins(cid: str):
    if cid not in origins_db:
        origins_db[cid] = {"origins": {}, "users": {}}

async def handle_set_origin(update, context):
    msg = update.message
    user = update.effective_user
    cid = str(update.effective_chat.id)
    raw = msg.text.strip()

    allowed = await _can_manage_origin(update, context) or msg.reply_to_message
    if not allowed:
        return await msg.reply_text("🚫 فقط مدیران یا خود فرد (با ریپلای)!")
    origin_text = ""
    for ph in ["ثبت اصل", "setorigin", "set origin"]:
        if raw.lower().startswith(ph):
            origin_text = raw[len(ph):].strip()
            break
    if not origin_text and msg.reply_to_message:
        origin_text = msg.reply_to_message.text or ""
    if not origin_text:
        return await msg.reply_text("⚠️ متن اصل را بنویس یا روی پیامِ شخص ریپلای کن.")

    target = msg.reply_to_message.from_user if msg.reply_to_message else user
    _ensure_chat_in_origins(cid)
    origins_db[cid]["origins"][str(target.id)] = origin_text
    _save_json(ORIGINS_FILE, origins_db)
    sent = await msg.reply_text(f"✅ اصل برای <b>{target.first_name}</b> ثبت شد:\n🧿 {origin_text}", parse_mode="HTML")
    await asyncio.sleep(8)
    try:
        await sent.delete()
        await msg.delete()
    except:
        pass

async def handle_show_origin(update, context):
    msg = update.message
    user = update.effective_user
    cid = str(update.effective_chat.id)
    tx = msg.text.lower().strip()
    target = msg.reply_to_message.from_user if msg.reply_to_message else (user if "من" in tx else None)
    if not target:
        return await msg.reply_text("📘 بنویس «اصل من» یا روی پیام کسی ریپلای کن و «اصل» بنویس.")
    group = origins_db.get(cid, {}).get("origins", {})
    val = group.get(str(target.id))
    if not val:
        return await msg.reply_text("ℹ️ اصلی ثبت نشده.")
    await msg.reply_text(f"🌿 <b>اصل {target.first_name}:</b>\n{val}", parse_mode="HTML")

async def handle_del_origin(update, context):
    if not await _can_manage_origin(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها!")
    msg = update.message
    cid = str(update.effective_chat.id)
    target = msg.reply_to_message.from_user if msg.reply_to_message else update.effective_user
    group = origins_db.get(cid, {}).get("origins", {})
    if str(target.id) not in group:
        return await msg.reply_text("⚠️ اصلی برای این کاربر ثبت نشده.")
    del origins_db[cid]["origins"][str(target.id)]
    _save_json(ORIGINS_FILE, origins_db)
    await msg.reply_text(f"🗑️ اصل {target.first_name} حذف شد.")

async def handle_list_origins(update, context):
    cid = str(update.effective_chat.id)
    group = origins_db.get(cid, {}).get("origins", {})
    if not group:
        return await update.message.reply_text("ℹ️ هیچ اصلی ثبت نشده.")
    txt = "💎 <b>لیست اصل‌ها:</b>\n\n"
    for uid, val in group.items():
        txt += f"👤 <a href='tg://user?id={uid}'>کاربر</a>:\n🧿 {val}\n\n"
    await update.message.reply_text(txt, parse_mode="HTML")

# ثبت فعالیت کاربران (برای تگ فعال/غیرفعال)
async def auto_clean_old_origins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    cid = str(update.effective_chat.id)
    uid = str(update.effective_user.id)
    if cid not in origins_db:
        origins_db[cid] = {"origins": {}, "users": {}}
    origins_db[cid]["users"][uid] = datetime.now().isoformat()
    _save_json(ORIGINS_FILE, origins_db)

async def handle_bot_removed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.effective_chat.id)
    if cid in origins_db:
        del origins_db[cid]
        _save_json(ORIGINS_FILE, origins_db)

# ─────────────────────────────── Nicknames (لقب) ───────────────────────────────
def _ensure_chat_nicks(cid: str):
    if cid not in nicks_db:
        nicks_db[cid] = {}

async def _can_manage_nick(update, context):
    return await is_authorized(update, context)

async def handle_set_nick(update, context):
    msg = update.message
    cid = str(update.effective_chat.id)
    user = update.effective_user
    text = msg.text.strip()
    nick_text = ""
    for phrase in ["ثبت لقب", "set nick", "setnickname", "setnick"]:
        if text.lower().startswith(phrase):
            nick_text = text[len(phrase):].strip()
            break
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        if not await _can_manage_nick(update, context):
            return await msg.reply_text("🚫 فقط مدیر/سودو می‌تواند برای دیگران لقب تعیین کند!")
    else:
        target = user
    if not nick_text:
        return await msg.reply_text("📝 مثال: <code>ثبت لقب فرمانده</code>", parse_mode="HTML")
    _ensure_chat_nicks(cid)
    nicks_db[cid][str(target.id)] = nick_text
    _save_json(NICKS_FILE, nicks_db)
    await msg.reply_text(f"✅ لقب <b>{target.first_name}</b> ثبت شد:\n👑 {nick_text}", parse_mode="HTML")

async def handle_show_nick(update, context):
    msg = update.message
    cid = str(update.effective_chat.id)
    tx = msg.text.lower().strip()
    user = update.effective_user
    target = msg.reply_to_message.from_user if msg.reply_to_message else (user if "من" in tx else None)
    if not target:
        return await msg.reply_text("📘 «لقب من» یا ریپلای+«لقب».")
    nick = nicks_db.get(cid, {}).get(str(target.id))
    if not nick:
        return await msg.reply_text("ℹ️ لقبی ثبت نشده.")
    await msg.reply_text(f"👑 <b>لقب {target.first_name}:</b>\n{nick}", parse_mode="HTML")

async def handle_del_nick(update, context):
    msg = update.message
    cid = str(update.effective_chat.id)
    target = msg.reply_to_message.from_user if msg.reply_to_message else update.effective_user
    if msg.reply_to_message and not await _can_manage_nick(update, context):
        return await msg.reply_text("🚫 فقط مدیر/سودو!")
    if cid not in nicks_db or str(target.id) not in nicks_db[cid]:
        return await msg.reply_text("⚠️ لقبی ثبت نشده.")
    del nicks_db[cid][str(target.id)]
    _save_json(NICKS_FILE, nicks_db)
    await msg.reply_text(f"🗑️ لقب {target.first_name} حذف شد.", parse_mode="HTML")

async def handle_list_nicks(update, context):
    cid = str(update.effective_chat.id)
    g = nicks_db.get(cid, {})
    if not g:
        return await update.message.reply_text("ℹ️ هیچ لقبی ثبت نشده.")
    txt = "👑 <b>لیست لقب‌ها:</b>\n\n"
    for uid, nick in g.items():
        txt += f"👤 <a href='tg://user?id={uid}'>کاربر</a> → {nick}\n"
    await update.message.reply_text(txt, parse_mode="HTML")

# ─────────────────────────────── Tag System ───────────────────────────────
async def handle_tag(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها!")
    text = update.message.text.lower().strip()
    chat = update.effective_chat
    cid = str(chat.id)
    now = datetime.now()

    data = origins_db.get(cid, {})
    users = data.get("users", {})
    if not users and "همه" in text:
        return await update.message.reply_text("⚠️ هنوز فعالیتی ثبت نشده.")

    targets = []
    title = "کاربران"
    if "همه" in text:
        targets = list(users.keys())
        title = "همه کاربران"
    elif "فعال" in text:
        th = now - timedelta(days=3)
        targets = [u for u, t in users.items() if datetime.fromisoformat(t) >= th]
        title = "کاربران فعال (۳ روز اخیر)"
    elif "غیرفعال" in text:
        th = now - timedelta(days=3)
        targets = [u for u, t in users.items() if datetime.fromisoformat(t) < th]
        title = "کاربران غیرفعال"
    elif "مدیر" in text:
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            targets = [str(a.user.id) for a in admins]
            title = "مدیران گروه"
        except:
            return await update.message.reply_text("⚠️ خطا در دریافت مدیران")
    elif "تگ " in text and ("@" in text or any(ch.isdigit() for ch in text.split())):
        raw = text.replace("تگ", "").strip()
        targets = [raw.replace("@", "")]
        title = f"کاربر {raw}"
    else:
        return await update.message.reply_text(
            "📌 نمونه: «تگ همه» | «تگ فعال» | «تگ غیرفعال» | «تگ مدیران» | «تگ @123»",
            parse_mode="HTML"
        )

    if not targets:
        return await update.message.reply_text("⚠️ کاربری برای تگ یافت نشد.")
    await update.message.reply_text(f"📢 شروع تگ {title} ...", parse_mode="HTML")
    batch, cnt = [], 0
    for i, uid in enumerate(targets, 1):
        batch.append(f"<a href='tg://user?id={uid}'>🟢</a>")
        if len(batch) >= 5 or i == len(targets):
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                cnt += len(batch)
                batch = []
                await asyncio.sleep(1)
            except:
                pass
    await update.message.reply_text(f"✅ {cnt} کاربر {title} تگ شدند.", parse_mode="HTML")

# ─────────────────────────────── Alias + Command Core ───────────────────────────────
DEFAULT_ALIASES = {
    # قفل گروه
    "lockgroup": ["قفل گروه", "ببند گروه", "lock group"],
    "unlockgroup": ["بازکردن گروه", "باز گروه", "unlock group"],
    "autolockgroup": ["قفل خودکار گروه", "تنظیم قفل خودکار", "auto lock group"],
    "disableautolock": ["غیرفعال کردن قفل خودکار", "لغو قفل خودکار"],

    # فیلترها
    "addfilter": ["افزودن فیلتر", "فیلترکن", "addfilter"],
    "delfilter": ["حذف فیلتر", "پاک فیلتر", "delfilter"],
    "filters": ["لیست فیلترها", "فیلترها", "filters"],

    # تگ‌ها
    "tagall": ["تگ همه", "منشن همگانی", "tagall"],
    "tagactive": ["تگ فعال", "tagactive"],
    "taginactive": ["تگ غیرفعال", "taginactive"],
    "tagadmins": ["تگ مدیران", "tagadmins"],

    # لقب‌ها
    "setnick": ["ثبت لقب", "set nick", "setnickname", "setnick"],
    "shownick": ["لقب", "لقب من", "mynick"],
    "delnick": ["حذف لقب", "پاک لقب", "delnick"],
    "listnicks": ["لیست لقب‌ها", "نمایش لقب‌ها", "nicknames"],

    # اصل‌ها
    "setorigin": ["ثبت اصل", "set origin", "setorigin"],
    "showorigin": ["اصل", "اصل من", "origin"],
    "delorigin": ["حذف اصل", "delorigin"],
    "listorigins": ["لیست اصل‌ها", "origins"],
    # ───── مدیریت کاربران (بن / سکوت / اخطار) ─────
    "ban": ["بن", "بن کاربر", "مسدود", "ban"],
    "unban": ["حذف بن", "آزاد", "unban"],
    "listbans": ["لیست بن", "کاربران بن‌شده", "bans"],

    "mute": ["سکوت", "ساکت", "mute"],
    "unmute": ["حذف سکوت", "بازکردن سکوت", "unmute"],
    "listmutes": ["لیست سکوت", "کاربران ساکت", "mutes"],

    "warn": ["اخطار", "warn"],
    "unwarn": ["حذف اخطار", "پاک اخطار", "unwarn"],
    "listwarns": ["لیست اخطار", "اخطارها", "warns"],

    # پین
    "pin": ["پن", "پین", "سنجاق", "pin"],
    "unpin": ["حذف پن", "بردار پین", "unpin"],

    # پاکسازی
    "clean": ["پاکسازی", "پاک کن", "پاک", "clear", "delete", "clean"],

    # وضعیت قفل‌ها
    "locks": ["وضعیت قفل", "وضعیت قفل‌ها", "locks", "lock status"]
}

if not ALIASES:
    ALIASES = DEFAULT_ALIASES
    _save_json(ALIASES_FILE, ALIASES)

async def execute_command(cmd, update, context):
    mapping = {
        # قفل گروه
        "lockgroup": handle_lockgroup,
        "unlockgroup": handle_unlockgroup,
        "autolockgroup": handle_auto_lockgroup,
        "disableautolock": handle_disable_auto_lock,

        # فیلتر
        "addfilter": handle_addfilter,
        "delfilter": handle_delfilter,
        "filters": handle_filters,
        # ───── مدیریت مدیران ─────
        "addadmin": ["افزودن مدیر", "مدیر کن", "add admin"],
        "removeadmin": ["حذف مدیر", "بردار مدیر", "remove admin"],
        "admins": ["لیست مدیران", "مدیران", "admins"],
        "clearadmins": ["پاکسازی مدیران", "پاک مدیران", "clear admins"],
        # بن / سکوت / اخطار
        "ban": handle_ban,
        "unban": handle_unban,
        "listbans": handle_list_bans,

        "mute": handle_mute,
        "unmute": handle_unmute,
        "listmutes": handle_list_mutes,

        "warn": handle_warn,
        "unwarn": handle_unwarn,
        "listwarns": handle_list_warns,
        # مدیریت مدیران
        "addadmin": handle_addadmin,
        "removeadmin": handle_removeadmin,
        "admins": handle_admins,
        "clearadmins": handle_clearadmins,

        # تگ
        "tagall": handle_tag,
        "tagactive": handle_tag,
        "taginactive": handle_tag,
        "tagadmins": handle_tag,

        # لقب
        "setnick": handle_set_nick,
        "shownick": handle_show_nick,
        "delnick": handle_del_nick,
        "listnicks": handle_list_nicks,

        # اصل
        "setorigin": handle_set_origin,
        "showorigin": handle_show_origin,
        "delorigin": handle_del_origin,
        "listorigins": handle_list_origins,

        # پین
        "pin": handle_pin,
        "unpin": handle_unpin,

        # پاکسازی
        "clean": handle_clean,

        # وضعیت قفل‌ها
        "locks": handle_locks_status,
    }
    if cmd in mapping:
        return await mapping[cmd](update, context)
    else:
        return await update.message.reply_text("⚠️ دستور ناشناخته.", parse_mode="HTML")

# ─────────────────────────────── Command Core ───────────────────────────────
async def handle_locks_with_alias(update, context):
    """مدیریت قفل‌ها با پشتیبانی alias (فارسی و انگلیسی)"""

    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    lower_text = update.message.text.strip().lower()

    # ✅ بررسی ویژه: قفل کامل گروه / بازکردن گروه
    if "قفل گروه" in lower_text or "ببند گروه" in lower_text or "lock group" in lower_text:
        return await handle_lockgroup(update, context)

    if "باز گروه" in lower_text or "بازکردن گروه" in lower_text or "unlock group" in lower_text:
        return await handle_unlockgroup(update, context)

    # ✅ بررسی ویژه: قفل خودکار گروه (زمان‌بندی شبانه یا ساعتی)
    if "قفل خودکار" in lower_text or "auto lock group" in lower_text:
        return await handle_auto_lockgroup(update, context)

    if "غیرفعال قفل خودکار" in lower_text or "لغو قفل خودکار" in lower_text or "disable auto lock" in lower_text:
        return await handle_disable_auto_lock(update, context)

    # ✅ از اینجا به بعد بقیه‌ی قفل‌های معمولی (لینک، عکس، استیکر و...) بررسی می‌شن
    text = update.message.text.strip().lower()
    parts = text.split()

    if len(parts) < 2:
        return await update.message.reply_text("⚠️ نام قفل نامعتبر است.")

    action, lock_name = parts[0], parts[1]
    chat_id = str(update.effective_chat.id)
    _ensure_locks(chat_id)

    # جستجو بین قفل‌ها
    found_lock = None
    for key, names in LOCK_ALIASES.items():
        if lock_name in names:
            found_lock = key
            break

    if not found_lock:
        return await update.message.reply_text("⚠️ نام قفل نامعتبر است.")

    locks = group_data[chat_id]["locks"]

    if action == "قفل" or action == "lock":
        if locks.get(found_lock):
            return await update.message.reply_text(f"🔒 قفل <b>{LOCK_ALIASES[found_lock][0]}</b> از قبل فعال است.", parse_mode="HTML")
        locks[found_lock] = True
        await update.message.reply_text(f"🔒 قفل <b>{LOCK_ALIASES[found_lock][0]}</b> فعال شد.", parse_mode="HTML")

    elif action == "باز" or action == "unlock" or action == "بازکردن":
        if not locks.get(found_lock):
            return await update.message.reply_text(f"🔓 قفل <b>{LOCK_ALIASES[found_lock][0]}</b> از قبل باز است.", parse_mode="HTML")
        locks[found_lock] = False
        await update.message.reply_text(f"🔓 قفل <b>{LOCK_ALIASES[found_lock][0]}</b> باز شد.", parse_mode="HTML")

    group_data[chat_id]["locks"] = locks
    _save_json(GROUP_CTRL_FILE, group_data)


# ─────────────────────────────── پایان فایل ───────────────────────────────
print("✅ [Group Control System] با موفقیت بارگذاری شد.")
