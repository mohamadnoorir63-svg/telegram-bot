# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re, random

# ================== تنظیمات ==================
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754  # سودوی ربات (فقط این آیدی همه‌کاره است)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🖼 قفل عکس / باز کردن عکس
🎥 قفل ویدیو / باز کردن ویدیو
🎭 قفل گیف / باز کردن گیف
📎 قفل فایل / باز کردن فایل
🎶 قفل موزیک / باز کردن موزیک
🎙 قفل ویس / باز کردن ویس
🔄 قفل فوروارد / باز کردن فوروارد
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار (ریپلای) — سه اخطار = بن
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه | 📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش | ✍️ خوشامد متن [متن]
🖼 ثبت عکس (ریپلای → ثبت عکس)
🧹 پاکسازی (۵۰ پیام) | پاکسازی 9999 | حذف پیام 9999
✍️ فونت [متن دلخواه]
🧾 ثبت اصل [متن] (فقط سودو - ریپلای) | اصل (ریپلای)
🤣 جوک | 🔮 فال | 🧑‍💼 بیو
➕ ثبت جوک / ثبت فال / ثبت بیو  (فقط سودو؛ متن یا عکس+کپشن)
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ========= کمک‌تابع‌ها =========
def is_admin(chat_id, user_id):
    if user_id == SUDO_ID:
        return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m):
    # متن دستور؛ برای عکس/ویدیو هم کپشن را می‌خواند
    return (getattr(m, "text", None) or getattr(m, "caption", None) or "").strip()

# ——— ذخیره گروه‌ها برای «ارسال» ———
joined_groups = set()
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group","supergroup"):
            joined_groups.add(chat.id)
    except:
        pass

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: cmd_text(m) == "راهنما", content_types=['text'])
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت", content_types=['text'])
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: cmd_text(m) == "تاریخ", content_types=['text'])
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ایدی", content_types=['text'])
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار", content_types=['text'])
def stats(m):
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ========= وضعیت ربات =========
@bot.message_handler(func=lambda m: cmd_text(m) == "وضعیت ربات", content_types=['text'])
def bot_perms(m):
    try:
        me_id = bot.get_me().id
        cm = bot.get_chat_member(m.chat.id, me_id)
        if cm.status != "administrator":
            return bot.reply_to(m, "❗ ربات ادمین نیست.")
        flags = {
            "مدیریت چت": getattr(cm, "can_manage_chat", False),
            "حذف پیام": getattr(cm, "can_delete_messages", False),
            "محدودسازی اعضا": getattr(cm, "can_restrict_members", False),
            "پین پیام": getattr(cm, "can_pin_messages", False),
            "دعوت کاربر": getattr(cm, "can_invite_users", False),
            "افزودن مدیر": getattr(cm, "can_promote_members", False),
            "مدیریت ویدیوچت": getattr(cm, "can_manage_video_chats", False),
        }
        lines = [f"{'✅' if v else '❌'} {k}" for k,v in flags.items()]
        bot.reply_to(m, "🛠 وضعیت ربات:\n" + "\n".join(lines))
    except:
        bot.reply_to(m, "نتوانستم وضعیت را بخوانم.")

# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        # ضد ربات/تبچی هنگام ورود
        if u.is_bot and locks["bots"].get(m.chat.id):
            try: bot.ban_chat_member(m.chat.id, u.id)
            except: pass
            continue
        if (not (u.first_name or "").strip()) and locks["tabchi"].get(m.chat.id):
            try: bot.ban_chat_member(m.chat.id, u.id)
            except: pass
            continue

        if not welcome_enabled.get(m.chat.id): 
            continue
        name = u.first_name or ""
        txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", name)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد روشن", content_types=['text'])
def w_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = True
    bot.reply_to(m, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد خاموش", content_types=['text'])
def w_off(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = False
    bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن"), content_types=['text'])
def w_txt(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    txt = cmd_text(m).replace("خوشامد متن", "", 1).strip()
    welcome_texts[m.chat.id] = txt
    bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "ثبت عکس", content_types=['text'])
def w_photo(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if not m.reply_to_message or not m.reply_to_message.photo:
        return bot.reply_to(m, "❗ باید روی یک عکس ریپلای کنید.")
    welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
    bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")

# ========= قفل‌ها =========
locks = {k:{} for k in ["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}

LOCK_MAP = {
    "لینک": "links",
    "استیکر": "stickers",
    "ربات": "bots",
    "تبچی": "tabchi",
    "گروه": "group",
    "عکس": "photo",
    "ویدیو": "video",
    "گیف": "gif",
    "فایل": "file",
    "موزیک": "music",
    "ویس": "voice",
    "فوروارد": "forward",
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("باز کردن "), content_types=['text'])
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    t = cmd_text(m)
    enable = t.startswith("قفل ")
    name = t.replace("قفل ", "", 1).replace("باز کردن ", "", 1).strip()
    key = LOCK_MAP.get(name)
    if not key:
        return
    if key == "group":
        # قفل/باز گروه با Permission
        try:
            bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=not enable))
            locks[key][m.chat.id] = enable
            return bot.reply_to(m, "🔐 گروه قفل شد." if enable else "✅ گروه باز شد.")
        except:
            return bot.reply_to(m, "❗ دسترسی محدودسازی لازم است.")
    locks[key][m.chat.id] = enable
    msg = "فعال شد." if enable else "آزاد شد."
    icons = {
        "links": "🔒/🔓", "stickers":"🧷", "bots":"🤖", "tabchi":"🚫", "photo":"🖼",
        "video":"🎥", "gif":"🎭", "file":"📎", "music":"🎶", "voice":"🎙", "forward":"🔄"
    }
    icon = icons.get(key, "✅")
    bot.reply_to(m, f"{icon.split('/')[0] if enable else icon.split('/')[-1]} {name} {msg}")

# بلاک مدیا + ضد لینک/فوروارد
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def global_guard(m):
    # ضد فوروارد
    if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat or getattr(m, "forward_sender_name", None)):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return

    # ضد لینک (فقط برای غیر ادمین و روی متن/کپشن)
    if locks["links"].get(m.chat.id) and not is_admin(m.chat.id, m.from_user.id):
        txt = cmd_text(m).lower()
        if re.search(r"(t\.me|telegram\.me|telegram\.org|https?://)", txt):
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass
            return

    # قفل مدیا
    try:
        if locks["photo"].get(m.chat.id) and m.content_type == "photo":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["video"].get(m.chat.id) and m.content_type == "video":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["gif"].get(m.chat.id) and m.content_type == "animation":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["file"].get(m.chat.id) and m.content_type == "document":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["music"].get(m.chat.id) and m.content_type == "audio":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["voice"].get(m.chat.id) and m.content_type == "voice":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["stickers"].get(m.chat.id) and m.content_type == "sticker":
            bot.delete_message(m.chat.id, m.message_id)
        # بعضی GIF ها به صورت document با mime_type=video/mp4 می‌آیند
        if locks["gif"].get(m.chat.id) and m.content_type == "document":
            if m.document and getattr(m.document, "mime_type", "") == "video/mp4":
                bot.delete_message(m.chat.id, m.message_id)
    except:
        pass

    # پاسخ ویژه سودو
    if m.content_type == 'text' and m.from_user.id == SUDO_ID and cmd_text(m) == "ربات":
        bot.reply_to(m, "جانم سودو 👑")

# ========= بن / سکوت =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن", content_types=['text'])
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "🚫 کاربر بن شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن", content_types=['text'])
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "✅ کاربر از بن خارج شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت", content_types=['text'])
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, can_send_messages=False)
        bot.reply_to(m, "🔕 کاربر سکوت شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم سکوت کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت", content_types=['text'])
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        )
        bot.reply_to(m, "🔊 کاربر از سکوت خارج شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف سکوت کنم.")

# ========= اخطار =========
warnings = {}
MAX_WARNINGS = 3

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار", content_types=['text'])
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id, {})
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid, 0) + 1
    count = warnings[m.chat.id][uid]
    if count >= MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id, uid)
            bot.reply_to(m, "🚫 کاربر با ۳ اخطار بن شد.")
            warnings[m.chat.id][uid] = 0
        except:
            bot.reply_to(m, "❗ نتوانستم بن کنم.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {count}/{MAX_WARNINGS} ثبت شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار", content_types=['text'])
def reset_warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if uid in warnings.get(m.chat.id, {}):
        warnings[m.chat.id][uid] = 0
        bot.reply_to(m, f"✅ اخطارهای {uid} حذف شد.")
    else:
        bot.reply_to(m, "ℹ️ اخطاری برای این کاربر ثبت نشده.")

# ========= مدیر / حذف مدیر =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "مدیر", content_types=['text'])
def promote_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status != "administrator" or not getattr(me, "can_promote_members", False):
            return bot.reply_to(m, "❗ ربات مجوز افزودن مدیر ندارد.")
        bot.promote_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True,
            can_restrict_members=True, can_pin_messages=True,
            can_invite_users=True, can_manage_video_chats=True,
            can_promote_members=False
        )
        bot.reply_to(m, "👑 کاربر مدیر شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم مدیر کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف مدیر", content_types=['text'])
def demote_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.promote_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False,
            can_restrict_members=False, can_pin_messages=False,
            can_invite_users=False, can_manage_video_chats=False,
            can_promote_members=False
        )
        bot.reply_to(m, "❌ کاربر از مدیریت حذف شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف مدیر کنم.")

# ========= پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "پن", content_types=['text'])
def pin_msg(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id, disable_notification=True)
        bot.reply_to(m, "📌 پیام پین شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف پن", content_types=['text'])
def unpin_msg(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m, "❌ پین پیام برداشته شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف پین کنم.")

# ========= لیست‌ها =========
@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران گروه", content_types=['text'])
def list_group_admins(m):
    try:
        admins = bot.get_chat_administrators(m.chat.id)
        lines = []
        for a in admins:
            u = a.user
            name = ((u.first_name or "") + (" " + u.last_name if u.last_name else "")).strip() or "بدون‌نام"
            lines.append(f"• {name} — <code>{u.id}</code>")
        bot.reply_to(m, "📋 مدیران گروه:\n" + "\n".join(lines))
    except:
        bot.reply_to(m, "❗ نتوانستم لیست مدیران را بگیرم.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران ربات", content_types=['text'])
def list_bot_admins(m):
    bot.reply_to(m, f"📋 مدیران ربات:\n• سودو: <code>{SUDO_ID}</code>")

# ========= «اصل» (پروفایل/معرفی کاربر) =========
originals_global = {}  # uid -> text

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل"), content_types=['text'])
def set_original(m):
    if m.from_user.id != SUDO_ID: return
    txt = cmd_text(m).replace("ثبت اصل", "", 1).strip()
    if not txt: return bot.reply_to(m, "❗ متن معرفی را بعد از «ثبت اصل» بنویس.")
    uid = m.reply_to_message.from_user.id
    originals_global[uid] = txt
    bot.reply_to(m, f"✅ اصل برای <code>{uid}</code> ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "اصل", content_types=['text'])
def show_original(m):
    uid = m.reply_to_message.from_user.id if m.reply_to_message else m.from_user.id
    if uid in originals_global:
        bot.reply_to(m, f"🧾 اصل کاربر <code>{uid}</code>:\n{originals_global[uid]}")
    else:
        bot.reply_to(m, "ℹ️ اصل برای این کاربر ثبت نشده.")

# ========= دیتابیس جوک / فال / بیو (متن یا عکس) =========
jokes_db, fortunes_db, bios_db = [], [], []

def add_item_to_db(m, target_list, label, keyword):
    if m.from_user.id != SUDO_ID: return
    text_all = cmd_text(m)
    if m.content_type == "text":
        txt = text_all.replace(keyword, "", 1).strip()
        if not txt: return bot.reply_to(m, f"❗ بعد از «{keyword}» متن بنویس.")
        target_list.append({'type':'text','data':txt,'caption':''})
        bot.reply_to(m, f"✅ {label} متنی ذخیره شد. مجموع: {len(target_list)}")
    elif m.content_type == "photo":
        # کپشن باید با «ثبت X» شروع شود
        cap = text_all
        cap_txt = cap.replace(keyword, "", 1).strip() if cap.startswith(keyword) else (cap or "")
        target_list.append({'type':'photo','data':m.photo[-1].file_id,'caption':cap_txt})
        bot.reply_to(m, f"✅ {label} عکسی ذخیره شد. مجموع: {len(target_list)}")
    else:
        bot.reply_to(m, "❗ فقط متن یا عکس پشتیبانی می‌شود.")

@bot.message_handler(content_types=['text','photo'], func=lambda m: cmd_text(m).startswith("ثبت جوک"))
def add_joke(m): add_item_to_db(m, jokes_db, "جوک", "ثبت جوک")

@bot.message_handler(content_types=['text','photo'], func=lambda m: cmd_text(m).startswith("ثبت فال"))
def add_fortune(m): add_item_to_db(m, fortunes_db, "فال", "ثبت فال")

@bot.message_handler(content_types=['text','photo'], func=lambda m: cmd_text(m).startswith("ثبت بیو"))
def add_bio(m): add_item_to_db(m, bios_db, "بیو", "ثبت بیو")

def send_random_from_db(m, target_list, empty_msg):
    if not target_list:
        return bot.reply_to(m, empty_msg)
    item = random.choice(target_list)
    if item['type'] == "text":
        bot.reply_to(m, item['data'])
    else:
        try:
            bot.send_photo(m.chat.id, item['data'], caption=item['caption'])
        except:
            bot.reply_to(m, "❗ نتوانستم عکس را ارسال کنم.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک", content_types=['text'])
def get_joke(m): send_random_from_db(m, jokes_db, "ℹ️ هنوز جوکی ثبت نشده.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال", content_types=['text'])
def get_fortune(m): send_random_from_db(m, fortunes_db, "ℹ️ هنوز فالی ثبت نشده.")

@bot.message_handler(func=lambda m: cmd_text(m) == "بیو", content_types=['text'])
def get_bio(m): send_random_from_db(m, bios_db, "ℹ️ هنوز بیویی ثبت نشده.")

# ========= فونت‌ها =========
def spaced(t):    return " ".join(list(t))
def heart(t):     return f"💖 {t} 💖"
def danger(t):    return f"☠️ {t.upper().replace('A','Λ').replace('E','Σ').replace('O','Ø')} ☠️"
def strike(t):    return ''.join([c + '̶' for c in t])
def underline(t): return ''.join([c + '̲' for c in t])
def boxen(t):     return "【 " + " ".join(list(t)) + " 】"
def stars(t):     return "✦ " + " ✦ ".join(list(t)) + " ✦"

fonts = [spaced, lambda t: t.upper(), lambda t: f"★ {t} ★", heart, danger, strike, underline, boxen, stars]

@bot.message_handler(func=lambda m: cmd_text(m).startswith("فونت"), content_types=['text'])
def font_cmd(m):
    txt = cmd_text(m).replace("فونت", "", 1).strip()
    if not txt: return bot.reply_to(m, "❗ متنی وارد کن")
    out = "\n".join([f"{i+1}- {f(txt)}" for i, f i
