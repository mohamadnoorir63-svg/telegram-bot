# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

# ================== تنظیمات ==================
# **مهم**: توکن را مستقیم داخل گیت یا فایل public قرار نده.
# اگر محلی اجرا می‌کنی: مقدار TOKEN را اینجا قرار بده (یا از متغیر محیطی بارگذاری کن).
# اگر در Heroku میزبانی می‌کنی: در Config Vars مقدار TOKEN را قرار بده و اینجا آن را بخوان.
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754   # آیدی سودوی اصلی (اگر آیدی دیگری مد نظرته، این عدد را عوض کن)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🛠 وضعیت ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن]
🖼 ثبت عکس (روی عکس ریپلای کن)
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
🚫 بن / ✅ حذف بن   (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن    (ریپلای)
📋 لیست مدیران گروه | 📋 لیست مدیران ربات
🧹 پاکسازی              (۵۰ پیام)
📢 ارسال                (فقط سودو)
➕ افزودن سودو [آیدی]
➖ حذف سودو [آیدی]
🚪 لفت بده              (فقط سودو)
"""

# ========= سودوها =========
sudo_ids = {SUDO_ID}
def is_sudo(uid): return uid in sudo_ids

# ========= کمک‌تابع =========
def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m):
    return (getattr(m, "text", None) or getattr(m, "caption", None) or "").strip()

# ——— ذخیره گروه‌ها برای ارسال همگانی ———
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
def time_cmd(m): bot.reply_to(m, f"⏰ {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: cmd_text(m) == "تاریخ", content_types=['text'])
def date_cmd(m): bot.reply_to(m, f"📅 {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ایدی", content_types=['text'])
def id_cmd(m): bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار", content_types=['text'])
def stats(m):
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name = (u.first_name or "")
        txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", name)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد روشن", content_types=['text'])
def w_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = True
    bot.reply_to(m, "✅ خوشامد روشن شد.")

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
        return bot.reply_to(m, "❗ باید روی یک عکس ریپلای کنی.")
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
    if not key: return

    if key == "group":
        try:
            bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=not enable))
            locks[key][m.chat.id] = enable
            return bot.reply_to(m, "🔐 گروه قفل شد." if enable else "✅ گروه باز شد.")
        except:
            return bot.reply_to(m, "❗ نیاز به دسترسی محدودسازی")

    locks[key][m.chat.id] = enable
    bot.reply_to(m, f"{'🔒' if enable else '🔓'} {name} {'فعال شد' if enable else 'آزاد شد'}")

# بلاک لینک/فوروارد/مدیا
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def guard(m):
    # ضد فوروارد
    if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat or getattr(m, "forward_sender_name", None)):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return

    # ضد لینک
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
        if locks["gif"].get(m.chat.id) and (m.content_type == "animation" or (m.content_type == "document" and getattr(m.document, "mime_type", "") == "video/mp4")):
            bot.delete_message(m.chat.id, m.message_id)
        if locks["file"].get(m.chat.id) and m.content_type == "document":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["music"].get(m.chat.id) and m.content_type == "audio":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["voice"].get(m.chat.id) and m.content_type == "voice":
            bot.delete_message(m.chat.id, m.message_id)
        if locks["stickers"].get(m.chat.id) and m.content_type == "sticker":
            bot.delete_message(m.chat.id, m.message_id)
    except:
        pass

# ========= بن / سکوت =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن", content_types=['text'])
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "🚫 بن شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن", content_types=['text'])
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "✅ بن حذف شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت", content_types=['text'])
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, can_send_messages=False)
        bot.reply_to(m, "🔕 سکوت شد.")
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
        bot.reply_to(m, "🔊 سکوت برداشته شد.")
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
    c = warnings[m.chat.id][uid]
    if c >= MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id, uid)
            bot.reply_to(m, "🚫 با ۳ اخطار بن شد.")
            warnings[m.chat.id][uid] = 0
        except:
            bot.reply_to(m, "❗ نتوانستم بن کنم.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {c}/{MAX_WARNINGS} ثبت شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار", content_types=['text'])
def reset_warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if uid in warnings.get(m.chat.id, {}):
        warnings[m.chat.id][uid] = 0
        bot.reply_to(m, "✅ اخطارها حذف شد.")
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
        bot.reply_to(m, "👑 مدیر شد.")
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
        bot.reply_to(m, "❌ مدیر حذف شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف مدیر کنم.")

# ========= پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "پن", content_types=['text'])
def pin_msg(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id, disable_notification=True)
        bot.reply_to(m, "📌 پین شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف پن", content_types=['text'])
def unpin_msg(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m, "❌ پین حذف شد.")
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
    ids = "، ".join([f"<code>{i}</code>" for i in sorted(sudo_ids)])
    bot.reply_to(m, f"📋 مدیران ربات (سودو):\n{ids}")

# ========= پاکسازی =========
def bulk_delete(m, n):
    if not is_admin(m.chat.id, m.from_user.id): return
    deleted = 0
    for i in range(m.message_id-1, m.message_id-n-1, -1):
        try:
            bot.delete_message(m.chat.id, i)
            deleted += 1
        except:
            pass
    bot.reply_to(m, f"🧹 {deleted} پیام پاک شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "پاکسازی", content_types=['text'])
def clear_50(m): bulk_delete(m, 50)

# ========= ارسال همگانی =========
waiting_broadcast = {}
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال", content_types=['text'])
def ask_broadcast(m):
    waiting_broadcast[m.from_user.id] = True
    bot.reply_to(m, "📢 پیام/عکس بعدی‌ات را بفرست تا به همه گروه‌ها ارسال شود.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and waiting_broadcast.get(m.from_user.id), content_types=['text','photo'])
def do_broadcast(m):
    waiting_broadcast[m.from_user.id] = False
    sent = 0
    for gid in list(joined_groups):
        try:
            if m.content_type == "text":
                bot.send_message(gid, m.text)
            elif m.content_type == "photo":
                bot.send_photo(gid, m.photo[-1].file_id, caption=(m.caption or ""))
            sent += 1
        except:
            pass
    bot.reply_to(m, f"✅ به {sent} گروه ارسال شد.")

# ========= مدیریت سودو =========
@bot.message_handler(func=lambda m: cmd_text(m).startswith("افزودن سودو "), content_types=['text'])
def add_sudo(m):
    if not is_sudo(m.from_user.id): return
    parts = cmd_text(m).split()
    try:
        uid = int(parts[-1])
    except:
        return bot.reply_to(m, "❗ آیدی صحیح نیست.")
    sudo_ids.add(uid)
    bot.reply_to(m, f"✅ <code>{uid}</code> به سودوها اضافه شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف سودو "), content_types=['text'])
def del_sudo(m):
    if not is_sudo(m.from_user.id): return
    parts = cmd_text(m).split()
    try:
        uid = int(parts[-1])
    except:
        return bot.reply_to(m, "❗ آیدی صحیح نیست.")
    if uid == SUDO_ID:
        return bot.reply_to(m, "❗ سودوی اولیه را نمی‌توان حذف کرد.")
    if uid in sudo_ids:
        sudo_ids.remove(uid)
        bot.reply_to(m, f"✅ <code>{uid}</code> از سودوها حذف شد.")
    else:
        bot.reply_to(m, "ℹ️ این آیدی در سودوها نیست.")

# ========= لفت بده =========
@bot.message_handler(func=lambda m: cmd_text(m) == "لفت بده", content_types=['text'])
def leave_cmd(m):
    if not is_sudo(m.from_user.id): return
    bot.send_message(m.chat.id, "به دستور سودو خارج می‌شوم 👋")
    try: bot.leave_chat(m.chat.id)
    except: pass

# ========= جواب سودو =========
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ربات", content_types=['text'])
def sudo_reply(m): bot.reply_to(m, "جانم سودو 👑")

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
