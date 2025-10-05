# -*- coding: utf-8 -*-
# Group Manager – Full Persian Edition (pyTelegramBotAPI)
# Features: Locks (لینک/استیکر/ربات/تبچی/گروه/عکس/ویدیو/گیف/فایل/موزیک/ویس/فوروارد),
# خوشامد(روشن/خاموش/متن/عکس), بن/حذف‌بن, سکوت/حذف‌سکوت, مدیر/حذف‌مدیر,
# پین/حذف‌پین, لیست مدیران گروه/ربات, پاکسازی, اخطار (Auto-mute/ban),
# ارسال همگانی (سودو), لفت, وضعیت ربات, پاسخ «ربات» ← «جانم سودو»

import telebot
from telebot import types
from datetime import datetime
import re

# ====== تنظیمات ======
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"   # توکن ربات
SUDO_ID = 7089376754                                         # آیدی عددی سودو
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ====== راهنما ======
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
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (روی عکس ریپلای کن و بفرست: ثبت عکس)
⚠️ اخطار (ریپلای) — 3 اخطار = بن خودکار
🧹 پاکسازی (حذف ۵۰ پیام آخر)
🛠 وضعیت ربات
📢 ارسال (فقط سودو)
🚪 لفت بده (فقط سودو)
"""

# ====== ابزارها/داده‌های درون‌حافظه ======
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator") or user_id == SUDO_ID
    except:
        return False

# قفل‌ها
locks = {
    "links": {}, "stickers": {}, "bots": {}, "tabchi": {}, "group": {},
    "photo": {}, "video": {}, "gif": {}, "file": {}, "music": {}, "voice": {}, "forward": {}
}

def lock_set(chat_id, key, state=True):
    locks[key][chat_id] = state

# خوشامد
welcome_enabled = {}      # chat_id -> bool
welcome_texts   = {}      # chat_id -> str (can use {name})
welcome_photos  = {}      # chat_id -> file_id

# اخطارها
warnings = {}             # chat_id -> { user_id -> count }
WARN_MUTE_THRESHOLD = 2   # بعد از 2 اخطار → سکوت
WARN_BAN_THRESHOLD  = 3   # بعد از 3 اخطار → بن

def warn_inc(chat_id, user_id):
    if chat_id not in warnings: warnings[chat_id] = {}
    warnings[chat_id][user_id] = warnings[chat_id].get(user_id, 0) + 1
    return warnings[chat_id][user_id]

# لیست گروه‌هایی که ربات داخل‌شان است (برای ارسال همگانی)
joined_groups = set()

@bot.my_chat_member_handler()
def track_groups(update):
    chat = update.chat
    if chat and chat.type in ("group", "supergroup"):
        joined_groups.add(chat.id)

# ====== دستورات پایه ======
@bot.message_handler(func=lambda m: m.text == "راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text == "ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text == "تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text == "ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text == "آمار")
def stats(m):
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ====== وضعیت ربات (مجوزها) ======
@bot.message_handler(func=lambda m: m.text == "وضعیت ربات")
def bot_perms(m):
    try:
        me_id = bot.get_me().id
        cm = bot.get_chat_member(m.chat.id, me_id)
        if cm.status != "administrator":
            return bot.reply_to(m, "❗ ربات ادمین نیست. لطفاً ربات را ادمین کنید.")
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

# ====== خوشامد ======
@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        # ضد ربات/تبچی در لحظه ورود
        if u.is_bot and locks["bots"].get(m.chat.id):
            try: bot.ban_chat_member(m.chat.id, u.id)
            except: pass
            continue
        if (not u.first_name or u.first_name.strip()=="") and locks["tabchi"].get(m.chat.id):
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

@bot.message_handler(func=lambda m: m.text == "خوشامد روشن")
def welcome_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = True
    bot.reply_to(m, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: m.text == "خوشامد خاموش")
def welcome_off(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = False
    bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    txt = m.text.replace("خوشامد متن", "", 1).strip()
    welcome_texts[m.chat.id] = txt
    bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "ثبت عکس")
def save_photo(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
    bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")

# ====== لفت (سودو) ======
@bot.message_handler(func=lambda m: m.text == "لفت بده")
def leave_cmd(m):
    if m.from_user.id != SUDO_ID: return
    bot.send_message(m.chat.id, "به دستور سودو خارج می‌شوم 👋")
    try: bot.leave_chat(m.chat.id)
    except: pass

# ====== قفل‌ها ======
@bot.message_handler(func=lambda m: m.text in [
    "قفل گروه","باز کردن گروه",
    "قفل لینک","باز کردن لینک",
    "قفل استیکر","باز کردن استیکر",
    "قفل ربات","باز کردن ربات",
    "قفل تبچی","باز کردن تبچی",
    "قفل عکس","باز کردن عکس",
    "قفل ویدیو","باز کردن ویدیو",
    "قفل گیف","باز کردن گیف",
    "قفل فایل","باز کردن فایل",
    "قفل موزیک","باز کردن موزیک",
    "قفل ویس","باز کردن ویس",
    "قفل فوروارد","باز کردن فوروارد"
])
def toggle_locks(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    t = m.text
    cid = m.chat.id
    try:
        if   t == "قفل گروه":        lock_set(cid,"group",True);  bot.set_chat_permissions(cid, types.ChatPermissions(can_send_messages=False)); bot.reply_to(m,"🔐 گروه قفل شد.")
        elif t == "باز کردن گروه":   lock_set(cid,"group",False); bot.set_chat_permissions(cid, types.ChatPermissions(can_send_messages=True)); bot.reply_to(m,"✅ گروه باز شد.")
        elif t == "قفل لینک":        lock_set(cid,"links",True);  bot.reply_to(m,"🔒 لینک قفل شد.")
        elif t == "باز کردن لینک":   lock_set(cid,"links",False); bot.reply_to(m,"🔓 لینک آزاد شد.")
        elif t == "قفل استیکر":      lock_set(cid,"stickers",True); bot.reply_to(m,"🧷 استیکر قفل شد.")
        elif t == "باز کردن استیکر": lock_set(cid,"stickers",False); bot.reply_to(m,"🧷 استیکر آزاد شد.")
        elif t == "قفل ربات":        lock_set(cid,"bots",True);   bot.reply_to(m,"🤖 ربات‌ها قفل شدند.")
        elif t == "باز کردن ربات":   lock_set(cid,"bots",False);  bot.reply_to(m,"🤖 ربات‌ها آزاد شدند.")
        elif t == "قفل تبچی":        lock_set(cid,"tabchi",True); bot.reply_to(m,"🚫 تبچی قفل شد.")
        elif t == "باز کردن تبچی":   lock_set(cid,"tabchi",False);bot.reply_to(m,"🚫 تبچی آزاد شد.")
        elif t == "قفل عکس":         lock_set(cid,"photo",True);  bot.reply_to(m,"🖼 عکس قفل شد.")
        elif t == "باز کردن عکس":    lock_set(cid,"photo",False); bot.reply_to(m,"🖼 عکس آزاد شد.")
        elif t == "قفل ویدیو":       lock_set(cid,"video",True);  bot.reply_to(m,"🎥 ویدیو قفل شد.")
        elif t == "باز کردن ویدیو":  lock_set(cid,"video",False); bot.reply_to(m,"🎥 ویدیو آزاد شد.")
        elif t == "قفل گیف":         lock_set(cid,"gif",True);    bot.reply_to(m,"🎭 گیف قفل شد.")
        elif t == "باز کردن گیف":    lock_set(cid,"gif",False);   bot.reply_to(m,"🎭 گیف آزاد شد.")
        elif t == "قفل فایل":        lock_set(cid,"file",True);   bot.reply_to(m,"📎 فایل قفل شد.")
        elif t == "باز کردن فایل":   lock_set(cid,"file",False);  bot.reply_to(m,"📎 فایل آزاد شد.")
        elif t == "قفل موزیک":       lock_set(cid,"music",True);  bot.reply_to(m,"🎶 موزیک قفل شد.")
        elif t == "باز کردن موزیک":  lock_set(cid,"music",False); bot.reply_to(m,"🎶 موزیک آزاد شد.")
        elif t == "قفل ویس":         lock_set(cid,"voice",True);  bot.reply_to(m,"🎙 ویس قفل شد.")
        elif t == "باز کردن ویس":    lock_set(cid,"voice",False); bot.reply_to(m,"🎙 ویس آزاد شد.")
        elif t == "قفل فوروارد":     lock_set(cid,"forward",True);bot.reply_to(m,"🔄 فوروارد قفل شد.")
        elif t == "باز کردن فوروارد":lock_set(cid,"forward",False);bot.reply_to(m,"🔄 فوروارد آزاد شد.")
    except:
        bot.reply_to(m,"❗ نیاز به مجوز مناسب ادمین برای ربات است.")

# ====== فیلتر محتوا بر اساس قفل‌ها ======
@bot.message_handler(content_types=['photo','video','document','audio','voice','sticker','animation'])
def block_media(m):
    if not is_admin(m.chat.id, m.from_user.id):
        try:
            if locks["photo"].get(m.chat.id)   and m.content_type == "photo":    return bot.delete_message(m.chat.id, m.message_id)
            if locks["video"].get(m.chat.id)   and m.content_type == "video":    return bot.delete_message(m.chat.id, m.message_id)
            if locks["file"].get(m.chat.id)    and m.content_type == "document": return bot.delete_message(m.chat.id, m.message_id)
            if locks["music"].get(m.chat.id)   and m.content_type == "audio":    return bot.delete_message(m.chat.id, m.message_id)
            if locks["voice"].get(m.chat.id)   and m.content_type == "voice":    return bot.delete_message(m.chat.id, m.message_id)
            if locks["gif"].get(m.chat.id):
                # گیف به صورت animation یا document با mime_type=video/mp4 می‌آید
                if m.content_type == "animation": return bot.delete_message(m.chat.id, m.message_id)
                if m.content_type == "document" and getattr(m.document, "mime_type", "") == "video/mp4":
                    return bot.delete_message(m.chat.id, m.message_id)
            if locks["stickers"].get(m.chat.id) and m.content_type == "sticker":
                return bot.delete_message(m.chat.id, m.message_id)
        except:
            pass

@bot.message_handler(content_types=['text'])
def text_guard_and_super(m):
    # پاسخ اختصاصی سودو
    if m.from_user.id == SUDO_ID and m.text.strip() == "ربات":
        return bot.reply_to(m, "جانم سودو 👑")

    # ضد لینک
    if locks["links"].get(m.chat.id) and not is_admin(m.chat.id, m.from_user.id):
        if re.search(r"(t\.me|telegram\.me|telegram\.org|https?://)", (m.text or "").lower()):
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass

@bot.message_handler(func=lambda m: getattr(m, "forward_from", None) or getattr(m, "forward_from_chat", None) or getattr(m, "forward_date", None))
def ant_forward(m):
    if locks["forward"].get(m.chat.id) and not is_admin(m.chat.id, m.from_user.id):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

# ====== بن / حذف‌بن / سکوت / حذف‌سکوت ======
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try: bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id); bot.reply_to(m, "🚫 کاربر بن شد.")
    except: bot.reply_to(m, "❗ نتوانستم بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try: bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id, only_if_banned=True); bot.reply_to(m, "✅ کاربر از بن خارج شد.")
    except: bot.reply_to(m, "❗ نتوانستم حذف بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, types.ChatPermissions(can_send_messages=False))
        bot.reply_to(m, "🔕 کاربر سایلنت شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم سکوت کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id,
            types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        bot.reply_to(m, "🔊 کاربر از سکوت خارج شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف سکوت کنم.")

# ====== مدیر / حذف مدیر ======
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "مدیر")
def promote_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status != "administrator" or not getattr(me, "can_promote_members", False):
            return bot.reply_to(m, "❗ ربات مجوز افزودن مدیر ندارد.")
        bot.promote_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True, can_restrict_members=True,
            can_pin_messages=True, can_invite_users=True, can_manage_video_chats=True,
            can_promote_members=False
        )
        bot.reply_to(m, "👑 کاربر مدیر شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم مدیر کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "حذف مدیر")
def demote_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status != "administrator" or not getattr(me, "can_promote_members", False):
            return bot.reply_to(m, "❗ ربات مجوز حذف مدیر ندارد.")
        bot.promote_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False, can_restrict_members=False,
            can_pin_messages=False, can_invite_users=False, can_manage_video_chats=False,
            can_promote_members=False
        )
        bot.reply_to(m, "❌ کاربر از مدیریت حذف شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف مدیر کنم.")

# ====== پین / حذف پین ======
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "پن")
def pin_message(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status != "administrator" or not getattr(me, "can_pin_messages", False):
            return bot.reply_to(m, "❗ ربات مجوز پین کردن پیام ندارد.")
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id, disable_notification=True)
        bot.reply_to(m, "📌 پیام پین شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "حذف پن")
def unpin_message(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status != "administrator" or not getattr(me, "can_pin_messages", False):
            return bot.reply_to(m, "❗ ربات مجوز حذف پین ندارد.")
        bot.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m, "❌ پین پیام برداشته شد.")
    except:
        bot.reply_to(m, "❗ نتوانستم حذف پین کنم.")

# ====== لیست‌ها ======
@bot.message_handler(func=lambda m: m.text == "لیست مدیران گروه")
def list_group_admins(m):
    try:
        admins = bot.get_chat_administrators(m.chat.id)
        lines = []
        for a in admins:
            u = a.user
            name = (u.first_name or "") + ((" " + u.last_name) if u.last_name else "")
            lines.append(f"• {name.strip() or 'بدون‌نام'} — <code>{u.id}</code>")
        bot.reply_to(m, "📋 مدیران گروه:\n" + "\n".join(lines))
    except:
        bot.reply_to(m, "❗ نتوانستم لیست مدیران را بگیرم.")

@bot.message_handler(func=lambda m: m.text == "لیست مدیران ربات")
def list_bot_admins(m):
    bot.reply_to(m, f"📋 مدیران ربات:\n• سودو: <code>{SUDO_ID}</code>")

# ====== اخطار (Warn) ======
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    # ادمین‌ها را اخطار نده
    if is_admin(m.chat.id, uid): 
        return bot.reply_to(m, "این کاربر ادمین است.")
    count = warn_inc(m.chat.id, uid)
    bot.reply_to(m, f"⚠️ به کاربر <code>{uid}</code> اخطار داده شد. تعداد: {count}")

    try:
        if count == WARN_MUTE_THRESHOLD:
            bot.restrict_chat_member(m.chat.id, uid, types.ChatPermissions(can_send_messages=False))
            bot.send_message(m.chat.id, "🔕 به علت اخطارهای متعدد، کاربر سایلنت شد.")
        if count >= WARN_BAN_THRESHOLD:
            bot.ban_chat_member(m.chat.id, uid)
            bot.send_message(m.chat.id, "🚫 به علت ۳ اخطار، کاربر بن شد.")
    except:
        pass

# ====== پاکسازی ======
@bot.message_handler(func=lambda m: m.text == "پاکسازی")
def clear_messages(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    for i in range(m.message_id - 1, m.message_id - 51, -1):
        try: bot.delete_message(m.chat.id, i)
        except: pass
    bot.reply_to(m, "🧹 ۵۰ پیام آخر پاک شد.")

# ====== ارسال همگانی (سودو) ======
waiting_broadcast = {}

@bot.message_handler(func=lambda m: m.from_user.id == SUDO_ID and m.text == "ارسال")
def ask_broadcast(m):
    waiting_broadcast[m.from_user.id] = True
    bot.reply_to(m, "📢 متن یا عکس بعدی‌ات را بفرست تا به همهٔ گروه‌ها ارسال شود.")

@bot.message_handler(func=lambda m: m.from_user.id == SUDO_ID and waiting_broadcast.get(m.from_user.id))
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
    bot.reply_to(m, f"✅ پیام به {sent} گروه ارسال شد.")

# ====== اجرا ======
print("🤖 Bot is running...")
bot.infinity_polling()
