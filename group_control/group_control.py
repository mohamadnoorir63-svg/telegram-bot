# ======================= Group Control System — Full Single File =======================
# python-telegram-bot v20+

import os, json, re, asyncio
from datetime import datetime, timedelta
from telegram import (
    Update, ChatPermissions, MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import ContextTypes
from telegram.error import BadRequest, RetryAfter

# ─────────────────────────────── Files & Storage ───────────────────────────────

GROUP_CTRL_FILE = "group_control.json"    # locks, admins, auto_lock ...
ALIASES_FILE    = "aliases.json"
FILTER_FILE     = "filters.json"
ORIGINS_FILE    = "origins.json"
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

# ─────────────────────────────── Load Data ───────────────────────────────

group_data  = _load_json(GROUP_CTRL_FILE, {})
ALIASES     = _load_json(ALIASES_FILE, {})
filters_db  = _load_json(FILTER_FILE, {})
origins_db  = _load_json(ORIGINS_FILE, {})
nicks_db    = _load_json(NICKS_FILE, {})

# ─────────────────────────────── Access Control ───────────────────────────────

SUDO_IDS = [7089376754]

async def _is_admin_or_sudo_uid(context, chat_id: int, user_id: int) -> bool:
    """بررسی مجوز مدیر/سودو"""
    uid = str(user_id)
    cid = str(chat_id)
    if user_id in SUDO_IDS:
        return True
    admins = group_data.get(cid, {}).get("admins", [])
    if uid in admins:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی دسترسی کاربر"""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    uid = str(user.id)
    cid = str(chat.id)
    if user.id in SUDO_IDS:
        return True
    admins = group_data.get(cid, {}).get("admins", [])
    if uid in admins:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except:
        return False

# ─────────────────────────────── LOCKS (25 types) ───────────────────────────────

LOCK_TYPES = {
    "links": "ارسال لینک", "photos": "ارسال عکس", "videos": "ارسال ویدیو",
    "files": "ارسال فایل", "voices": "ارسال ویس", "vmsgs": "ارسال ویدیو مسیج",
    "stickers": "ارسال استیکر", "gifs": "ارسال گیف", "media": "ارسال همه رسانه‌ها",
    "forward": "ارسال فوروارد", "ads": "ارسال تبلیغ/تبچی", "usernames": "ارسال یوزرنیم/تگ",
    "mention": "منشن با @", "bots": "افزودن ربات", "join": "ورود عضو جدید",
    "tgservices": "پیام‌های سیستمی تلگرام", "joinmsg": "پیام ورود",
    "arabic": "حروف عربی (غیر فارسی)", "english": "حروف انگلیسی",
    "text": "ارسال پیام متنی", "audio": "ارسال آهنگ/موسیقی",
    "emoji": "پیام فقط ایموجی", "caption": "ارسال کپشن", "edit": "ویرایش پیام",
    "reply": "ریپلای/پاسخ", "all": "قفل کلی"
}

PERSIAN_TO_KEY = {
    "لینک": "links", "عکس": "photos", "تصویر": "photos", "ویدیو": "videos", "فیلم": "videos",
    "فایل": "files", "ویس": "voices", "ویدیو مسیج": "vmsgs", "استیکر": "stickers",
    "گیف": "gifs", "رسانه": "media", "فوروارد": "forward", "تبچی": "ads",
    "تبلیغ": "ads", "یوزرنیم": "usernames", "تگ": "usernames", "منشن": "mention",
    "ربات": "bots", "ورود": "join", "سرویس": "tgservices", "پیام ورود": "joinmsg",
    "عربی": "arabic", "انگلیسی": "english", "متن": "text", "آهنگ": "audio",
    "موزیک": "audio", "ایموجی": "emoji", "کپشن": "caption", "ویرایش": "edit",
    "ریپلای": "reply", "کلی": "all"
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
    await update.message.reply_text(f"🔒 قفل **{LOCK_TYPES[key]}** فعال شد.", parse_mode="HTML")

async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ همچین قفلی نیست.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    chat = update.effective_chat
    if not _locks_get(chat.id).get(key):
        return await update.message.reply_text(f"🔓 «{LOCK_TYPES[key]}» از قبل باز بوده.")
    _locks_set(chat.id, key, False)
    await update.message.reply_text(f"🔓 قفل **{LOCK_TYPES[key]}** باز شد.", parse_mode="HTML")

async def handle_locks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    locks = _locks_get(update.effective_chat.id)
    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست.", parse_mode="HTML")
    text = "🧱 **وضعیت قفل‌های گروه:**\n\n"
    for k, d in LOCK_TYPES.items():
        text += f"▫️ {d}: {'🔒 فعال' if locks.get(k) else '🔓 غیرفعال'}\n"
    await update.message.reply_text(text, parse_mode="HTML")
  # ─────────────────────────────── بررسی پیام‌ها (Locks Check) ───────────────────────────────

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
    """چک کردن پیام‌ها برای قفل‌ها و فیلترها"""
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user:
        return

    # معاف: مدیر یا سودو
    if await _is_admin_or_sudo_uid(context, chat.id, user.id):
        return

    locks = _locks_get(chat.id)
    if not locks and not filters_db.get(str(chat.id)):
        return

    text = (msg.text or msg.caption or "") or ""
    text_l = text.lower()

    async def _del(reason: str, filtered_word: str = None):
        """حذف پیام و نمایش دلیل"""
        try:
            await msg.delete()
        except:
            return
        try:
            message_text = (
                f"⫸ <b>کاربر:</b> <a href='tg://user?id={user.id}'>{user.first_name}</a>\n"
                f"◂ پیام شما حذف شد.\n"
            )
            if filtered_word:
                message_text += f"• <b>کلمه فیلتر شده:</b> <code>{filtered_word}</code>"
            else:
                message_text += f"• <b>دلیل:</b> {reason}"
            sent_msg = await context.bot.send_message(
                chat.id, message_text, parse_mode="HTML", disable_notification=True
            )
            await asyncio.sleep(10)
            try:
                await sent_msg.delete()
            except:
                pass
        except Exception as e:
            print(f"[Filter Delete Error]: {e}")

    # فیلتر کلمات
    chat_id = str(chat.id)
    chat_filters = filters_db.get(chat_id, [])
    if msg.text and chat_filters:
        tl = msg.text.lower()
        for w in chat_filters:
            if w and w in tl:
                return await _del("کلمه فیلترشده", filtered_word=w)

    # قفل کلی
    if locks.get("all"):
        return await _del("قفل کلی")

    # قفل پیام متنی
    if msg.text and locks.get("text"):
        return await _del("ارسال پیام متنی")

    # لینک
    if locks.get("links"):
        if any(x in text_l for x in ["http://", "https://", "t.me/"]):
            return await _del("ارسال لینک")
        if msg.entities:
            for e in msg.entities:
                if e.type in (MessageEntity.URL, MessageEntity.TEXT_LINK):
                    return await _del("ارسال لینک")

    # رسانه‌ها
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

    # تبلیغ / تبچی
    if locks.get("ads"):
        if any(w in text_l for w in ["join", "channel", "تبچی", "تبلیغ", "free followers", "free views"]):
            return await _del("ارسال تبلیغ/تبچی")

    # زبان‌ها
    if locks.get("english") and _english_pat.search(text):
        return await _del("استفاده از حروف انگلیسی")
    if locks.get("arabic") and _arabic_specific.search(text):
        return await _del("استفاده از حروف عربی")

    # ایموجی
    if locks.get("emoji") and msg.text and _emoji_only(msg.text):
        return await _del("پیام فقط ایموجی")

    # ریپلای
    if locks.get("reply") and msg.reply_to_message:
        return await _del("ریپلای/پاسخ")

# ─────────────────────────────── پیام‌های ورود / سرویس / اد ربات ───────────────────────────────

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
                await context.bot.unban_chat_member(chat.id, m.id)
            except:
                pass
            try:
                await msg.delete()
            except:
                pass
            continue

        if locks.get("join"):
            try:
                await context.bot.ban_chat_member(chat.id, m.id)
                await context.bot.unban_chat_member(chat.id, m.id)
            except:
                pass
            try:
                await msg.delete()
            except:
                pass
            continue

        if locks.get("joinmsg"):
            try:
                await msg.delete()
            except:
                pass

async def handle_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not chat:
        return
    if _locks_get(chat.id).get("tgservices"):
        try:
            await msg.delete()
        except:
            pass

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
        try:
            await edited.delete()
        except:
            pass

# ─────────────────────────────── قفل گروه / بازکردن / خودکار ───────────────────────────────

async def handle_lockgroup(update, context):
    """قفل کل گروه برای اعضا"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را قفل کنند!")

    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))

        # آزاد گذاشتن مدیران و سودوها
        try:
            admins_real = await context.bot.get_chat_administrators(chat.id)
            admins_registered = group_data.get(str(chat.id), {}).get("admins", [])
            allowed_ids = set([a.user.id for a in admins_real]) | set(map(int, admins_registered)) | set(SUDO_IDS)
            for uid in allowed_ids:
                try:
                    await context.bot.restrict_chat_member(
                        chat.id, uid,
                        ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_send_other_messages=True,
                            can_add_web_page_previews=True,
                        )
                    )
                except Exception as e:
                    print(f"⚠️ خطا در آزاد کردن {uid}: {e}")
        except Exception as e:
            print(f"⚠️ خطا در بررسی مدیران: {e}")

        await update.message.reply_text(
            f"🔒 <b>گروه قفل شد!</b>\n📅 {datetime.now().strftime('%H:%M - %d/%m/%Y')}\n👑 {update.effective_user.first_name}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

async def handle_unlockgroup(update, context):
    """بازکردن گروه برای اعضا"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را باز کنند!")
    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=True))
        await update.message.reply_text(
            f"🔓 **گروه باز شد!**\n📅 {datetime.now().strftime('%H:%M - %d/%m/%Y')}\n👑 {update.effective_user.first_name}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

async def handle_auto_lockgroup(update, context):
    """تنظیم قفل خودکار گروه"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند قفل خودکار تنظیم کنند!")
    chat_id = str(update.effective_chat.id)
    args = context.args
    if len(args) != 2:
        return await update.message.reply_text("🕒 استفاده:\n`قفل خودکار گروه 23:00 07:00`", parse_mode="HTML")
    start, end = args
    g = group_data.get(chat_id, {})
    g["auto_lock"] = {"enabled": True, "start": start, "end": end}
    group_data[chat_id] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text(f"✅ قفل خودکار فعال شد.\n⏰ از {start} تا {end} هر روز.", parse_mode="HTML")

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
    """زمان‌بندی اجرای قفل خودکار"""
    now = datetime.now().time()
    for chat_id, data in list(group_data.items()):
        auto = data.get("auto_lock", {})
        if not auto.get("enabled"):
            continue
        try:
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
          # ─────────────────────────────── پاکسازی پیام‌ها ───────────────────────────────

async def handle_clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی n پیام اخیر"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    args = context.args
    if not args:
        return await update.message.reply_text("⚙️ مثال:\n`پاکسازی 50`", parse_mode="Markdown")

    try:
        count = int(args[0])
    except:
        return await update.message.reply_text("⚠️ لطفاً تعداد پیام معتبر وارد کنید.")

    chat_id = update.effective_chat.id
    try:
        msgs = await context.bot.get_chat_history(chat_id, limit=count + 1)
        for m in msgs:
            try:
                await context.bot.delete_message(chat_id, m.message_id)
            except:
                pass
        await update.message.reply_text(f"🧹 {count} پیام پاکسازی شد ✅", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── پین / آن‌پین ───────────────────────────────

async def handle_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پین کردن پیام"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند پین کنند.")
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("⚠️ روی پیامی ریپلای کنید تا پین شود.")
    try:
        await context.bot.pin_chat_message(update.effective_chat.id, reply.message_id, disable_notification=False)
        await update.message.reply_text("📌 پیام پین شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در پین:\n<code>{e}</code>", parse_mode="HTML")

async def handle_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """برداشتن پین"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    try:
        await context.bot.unpin_chat_message(update.effective_chat.id)
        await update.message.reply_text("📍 پین برداشته شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── بن / آن‌بن ───────────────────────────────

async def handle_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 مجاز نیستید.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🚫 کاربر {user.first_name} بن شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

async def handle_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 مجاز نیستید.")
    args = context.args
    if not args:
        return await update.message.reply_text("⚙️ استفاده: `حذف بن <id>`", parse_mode="Markdown")
    try:
        uid = int(args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, uid)
        await update.message.reply_text("✅ کاربر از بن خارج شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── سکوت / اخطار ───────────────────────────────

async def handle_mute(update, context):
    """ساکت کردن کاربر"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 مجاز نیستید.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user.id, ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"🔇 کاربر {user.first_name} ساکت شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

async def handle_unmute(update, context):
    """آزاد کردن از سکوت"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 مجاز نیستید.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, user.id, ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(f"🔈 کاربر {user.first_name} آزاد شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── مدیران ───────────────────────────────

async def handle_addadmin(update, context):
    """افزودن مدیر جدید"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران ارشد مجازند.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    cid = str(update.effective_chat.id)
    admins = group_data.get(cid, {}).get("admins", [])
    if str(user.id) in admins:
        return await update.message.reply_text("⚠️ این کاربر از قبل مدیر است.")
    admins.append(str(user.id))
    g = group_data.get(cid, {})
    g["admins"] = admins
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text(f"👑 کاربر {user.first_name} مدیر شد.")

async def handle_removeadmin(update, context):
    """حذف مدیر ثبت‌شده"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران ارشد مجازند.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ روی پیام کاربر ریپلای کنید.")
    user = update.message.reply_to_message.from_user
    cid = str(update.effective_chat.id)
    admins = group_data.get(cid, {}).get("admins", [])
    if str(user.id) not in admins:
        return await update.message.reply_text("⚠️ این کاربر مدیر نیست.")
    admins.remove(str(user.id))
    g = group_data.get(cid, {})
    g["admins"] = admins
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text(f"❌ کاربر {user.first_name} از مدیران حذف شد.")

async def handle_admins(update, context):
    """نمایش لیست مدیران ثبت‌شده"""
    cid = str(update.effective_chat.id)
    admins = group_data.get(cid, {}).get("admins", [])
    if not admins:
        return await update.message.reply_text("👑 هیچ مدیری ثبت نشده است.")
    text = "👑 <b>لیست مدیران ثبت‌شده:</b>\n" + "\n".join(admins)
    await update.message.reply_text(text, parse_mode="HTML")

async def handle_clearadmins(update, context):
    """پاکسازی لیست مدیران"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط سودو مجاز است.")
    cid = str(update.effective_chat.id)
    g = group_data.get(cid, {})
    g["admins"] = []
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text("🧹 لیست مدیران پاک شد.")
  # ─────────────────────────────── لقب‌ها ───────────────────────────────

def _ensure_chat_nicks(cid: str):
    if cid not in nicks_db:
        nicks_db[cid] = {}

async def handle_set_nick(update, context):
    """ثبت لقب برای خود یا دیگران"""
    msg = update.message
    user = update.effective_user
    cid = str(update.effective_chat.id)

    text = msg.text.strip().replace("ثبت لقب", "").strip()
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        if not await is_authorized(update, context):
            return await msg.reply_text("🚫 فقط مدیر می‌تونه برای دیگران لقب بزنه.")
    else:
        target = user

    if not text:
        return await msg.reply_text("📝 مثال: `ثبت لقب فرمانده`", parse_mode="Markdown")

    _ensure_chat_nicks(cid)
    nicks_db[cid][str(target.id)] = text
    _save_json(NICKS_FILE, nicks_db)
    await msg.reply_text(f"✅ لقب برای {target.first_name} ثبت شد:\n👑 {text}")

async def handle_show_nick(update, context):
    """نمایش لقب خود یا دیگری"""
    msg = update.message
    user = update.effective_user
    cid = str(update.effective_chat.id)

    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
    else:
        target = user

    nick = nicks_db.get(cid, {}).get(str(target.id))
    if not nick:
        return await msg.reply_text("ℹ️ لقبی ثبت نشده.")
    await msg.reply_text(f"👑 لقب {target.first_name}: {nick}")

async def handle_del_nick(update, context):
    """حذف لقب"""
    msg = update.message
    cid = str(update.effective_chat.id)
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
    else:
        target = update.effective_user
    if not await is_authorized(update, context):
        return await msg.reply_text("🚫 فقط مدیر مجاز است.")
    if str(target.id) not in nicks_db.get(cid, {}):
        return await msg.reply_text("⚠️ لقبی برای این کاربر نیست.")
    del nicks_db[cid][str(target.id)]
    _save_json(NICKS_FILE, nicks_db)
    await msg.reply_text(f"🗑️ لقب {target.first_name} حذف شد.")

async def handle_list_nicks(update, context):
    """نمایش لیست لقب‌ها"""
    cid = str(update.effective_chat.id)
    g = nicks_db.get(cid, {})
    if not g:
        return await update.message.reply_text("ℹ️ هیچ لقبی ثبت نشده.")
    text = "👑 **لیست لقب‌ها:**\n\n" + "\n".join(
        [f"{i+1}. {nick}" for i, nick in enumerate(g.values())]
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─────────────────────────────── اصل‌ها ───────────────────────────────

def _ensure_chat_in_origins(cid: str):
    if cid not in origins_db:
        origins_db[cid] = {"origins": {}, "users": {}}

async def handle_set_origin(update, context):
    """ثبت اصل برای خود یا دیگری"""
    msg = update.message
    user = update.effective_user
    cid = str(update.effective_chat.id)
    text = msg.text.strip().replace("ثبت اصل", "").strip()
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        if not await is_authorized(update, context):
            return await msg.reply_text("🚫 فقط مدیر می‌تواند برای دیگران اصل ثبت کند.")
    else:
        target = user
    if not text:
        return await msg.reply_text("🧿 مثال: `ثبت اصل تهرانی`", parse_mode="Markdown")
    _ensure_chat_in_origins(cid)
    origins_db[cid]["origins"][str(target.id)] = text
    _save_json(ORIGINS_FILE, origins_db)
    await msg.reply_text(f"✅ اصل برای {target.first_name} ثبت شد:\n🪶 {text}")

async def handle_show_origin(update, context):
    """نمایش اصل"""
    msg = update.message
    user = update.effective_user
    cid = str(update.effective_chat.id)
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
    else:
        target = user
    val = origins_db.get(cid, {}).get("origins", {}).get(str(target.id))
    if not val:
        return await msg.reply_text("ℹ️ اصلی ثبت نشده.")
    await msg.reply_text(f"🌿 اصل {target.first_name}: {val}")

async def handle_list_origins(update, context):
    """لیست همه اصل‌ها"""
    cid = str(update.effective_chat.id)
    group = origins_db.get(cid, {}).get("origins", {})
    if not group:
        return await update.message.reply_text("ℹ️ هیچ اصلی ثبت نشده.")
    txt = "💎 **لیست اصل‌ها:**\n\n"
    for uid, val in group.items():
        txt += f"👤 {uid} → {val}\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

# ─────────────────────────────── هندلر دستورات ───────────────────────────────

async def group_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر مرکزی برای تشخیص خودکار دستورات فارسی"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    tx = text.lower()

    # 🔒 قفل/بازکردن محتوا
    if tx.startswith("قفل ") or tx.startswith("باز "):
        return await handle_locks_with_alias(update, context)

    # 🔒 قفل یا باز کردن گروه
    if tx in ["قفل گروه", "ببند گروه"]:
        return await handle_lockgroup(update, context)
    if tx in ["باز گروه", "بازکردن گروه"]:
        return await handle_unlockgroup(update, context)

    # 🧹 پاکسازی
    if tx.startswith("پاکسازی"):
        context.args = tx.split()[1:]
        return await handle_clean(update, context)

    # 👑 مدیران
    if tx.startswith("افزودن مدیر"):
        return await handle_addadmin(update, context)
    if tx.startswith("حذف مدیر"):
        return await handle_removeadmin(update, context)
    if "لیست مدیر" in tx:
        return await handle_admins(update, context)

    # 📌 پین
    if tx in ["پین", "پن", "سنجاق"]:
        return await handle_pin(update, context)
    if "حذف پین" in tx or "بردار پین" in tx:
        return await handle_unpin(update, context)

    # 🚫 بن / سکوت / اخطار
    if tx.startswith("بن "):
        return await handle_ban(update, context)
    if "حذف بن" in tx or "آزاد" in tx:
        return await handle_unban(update, context)
    if "سکوت" in tx:
        return await handle_mute(update, context)
    if "باز سکوت" in tx or "حذف سکوت" in tx:
        return await handle_unmute(update, context)

    # 🧿 اصل / لقب
    if tx.startswith("ثبت اصل"):
        return await handle_set_origin(update, context)
    if tx.startswith("ثبت لقب"):
        return await handle_set_nick(update, context)
    if "لقب" in tx:
        return await handle_show_nick(update, context)
    if "اصل" in tx:
        return await handle_show_origin(update, context)
    if "لیست اصل" in tx:
        return await handle_list_origins(update, context)
    if "لیست لقب" in tx:
        return await handle_list_nicks(update, context)

    # 😴 اگر هیچ دستور معتبری نبود
    print("😴 هیچ دستور خاصی شناسایی نشد.")
    return
