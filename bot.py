# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

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
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (روی عکس ریپلای کن و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر)
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ——— ذخیره‌ی گروه‌هایی که ربات داخل‌شان است (برای «ارسال») ———
joined_groups = set()

@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group", "supergroup"):
            joined_groups.add(chat.id)
    except:
        pass

# ——— کمک‌تابع: آیا اجراکننده ادمین (یا سودو) است؟ ———
def is_admin(chat_id, user_id):
    if user_id == SUDO_ID:
        return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: m.text == "راهنما")
def help_cmd(m):
    bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text == "ساعت")
def time_cmd(m):
    bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text == "تاریخ")
def date_cmd(m):
    bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text == "ایدی")
def id_cmd(m):
    bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text == "آمار")
def stats(m):
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ========= وضعیت ربات =========
@bot.message_handler(func=lambda m: m.text == "وضعیت ربات")
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
        if not welcome_enabled.get(m.chat.id): continue
        txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", u.first_name or "")
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text == "خوشامد روشن")
def welcome_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id]=True
    bot.reply_to(m,"✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: m.text == "خوشامد خاموش")
def welcome_off(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id]=False
    bot.reply_to(m,"❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    txt = m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id]=txt
    bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="ثبت عکس")
def save_photo(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
    bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")

# ========= قفل‌ها =========
lock_links, lock_stickers, lock_bots, lock_tabcchi, lock_group = {},{},{},{},{}

@bot.message_handler(func=lambda m: m.text=="قفل گروه")
def lock_group_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=False))
    bot.reply_to(m,"🔐 گروه قفل شد.")

@bot.message_handler(func=lambda m: m.text=="باز کردن گروه")
def unlock_group_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=True))
    bot.reply_to(m,"✅ گروه باز شد.")

@bot.message_handler(func=lambda m: m.text=="قفل لینک")
def lock_links_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_links[m.chat.id]=True; bot.reply_to(m,"🔒 لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن لینک")
def unlock_links_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_links[m.chat.id]=False; bot.reply_to(m,"🔓 لینک‌ها آزاد شدند.")

@bot.message_handler(content_types=['sticker'])
def block_sticker(m):
    if lock_stickers.get(m.chat.id) and m.from_user.id!=SUDO_ID:
        try: bot.delete_message(m.chat.id,m.message_id)
        except: pass

# ========= بن و سکوت =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try: bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id); bot.reply_to(m,"🚫 کاربر بن شد.")
    except: bot.reply_to(m,"❗ نتوانستم بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try: bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id); bot.reply_to(m,"✅ کاربر آزاد شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try: bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False); bot.reply_to(m,"🔕 کاربر سایلنت شد.")
    except: bot.reply_to(m,"❗ نتوانستم سکوت کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try: bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,
        can_send_messages=True,can_send_media_messages=True,can_send_other_messages=True,can_add_web_page_previews=True)
    except: pass
    bot.reply_to(m,"🔊 سکوت برداشته شد.")

# ========= اخطار =========
warnings = {}
MAX_WARNINGS=3

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="اخطار")
def warn_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{}); warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    count=warnings[m.chat.id][uid]
    if count>=MAX_WARNINGS:
        try: bot.ban_chat_member(m.chat.id,uid); bot.reply_to(m,f"⚠️ کاربر {uid} سومین اخطار را گرفت و بن شد 🚫")
        except: bot.reply_to(m,"❗ نتوانستم بن کنم.")
        warnings[m.chat.id][uid]=0
    else:
        bot.reply_to(m,f"⚠️ اخطار {count}/{MAX_WARNINGS} برای کاربر {uid}")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف اخطار")
def reset_warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    if m.chat.id in warnings and uid in warnings[m.chat.id]:
        warnings[m.chat.id][uid]=0; bot.reply_to(m,f"✅ اخطارهای {uid} حذف شد.")
    else:
        bot.reply_to(m,"ℹ️ اخطاری برای این کاربر ثبت نشده.")

# ========= ارتقا / حذف مدیر =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="مدیر")
def promote_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.promote_chat_member(m.chat.id,m.reply_to_message.from_user.id,
            can_manage_chat=True,can_delete_messages=True,can_restrict_members=True,
            can_pin_messages=True,can_invite_users=True,can_manage_video_chats=True)
        bot.reply_to(m,"👑 کاربر مدیر شد.")
    except: bot.reply_to(m,"❗ نتوانستم مدیر کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف مدیر")
def demote_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.promote_chat_member(m.chat.id,m.reply_to_message.from_user.id,
            can_manage_chat=False,can_delete_messages=False,can_restrict_members=False,
            can_pin_messages=False,can_invite_users=False,can_manage_video_chats=False)
        bot.reply_to(m,"❌ مدیر حذف شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف مدیر کنم.")

# ========= پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="پن")
def pin_message(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: bot.pin_chat_message(m.chat.id,m.reply_to_message.message_id,disable_notification=True); bot.reply_to(m,"📌 پین شد.")
    except: bot.reply_to(m,"❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف پن")
def unpin_message(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: bot.unpin_chat_message(m.chat.id,m.reply_to_message.message_id); bot.reply_to(m,"❌ پین حذف شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف پین کنم.")

# ========= لیست‌ها =========
@bot.message_handler(func=lambda m: m.text=="لیست مدیران گروه")
def list_group_admins(m):
    try:
        admins=bot.get_chat_administrators(m.chat.id)
        lines=[f"• {(a.user.first_name or 'بدون‌نام')} — <code>{a.user.id}</code>" for a in admins]
        bot.reply_to(m,"📋 مدیران گروه:\n"+"\n".join(lines))
    except: bot.reply_to(m,"❗ نتوانستم لیست بگیرم.")

@bot.message_handler(func=lambda m: m.text=="لیست مدیران ربات")
def list_bot_admins(m):
    bot.reply_to(m,f"📋 مدیران ربات:\n• سودو: <code>{SUDO_ID}</code>")

# ========= پاکسازی =========
@bot.message_handler(func=lambda m: m.text=="پاکسازی")
def clear_messages(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    for i in range(m.message_id-1,m.message_id-51,-1):
        try: bot.delete_message(m.chat.id,i)
        except: pass
    bot.reply_to(m,"🧹 ۵۰ پیام پاک شد.")

# ========= ارسال همگانی =========
waiting_broadcast={}
@bot.message_handler(func=lambda m: m.from_user.id==SUDO_ID and m.text=="ارسال")
def ask_broadcast(m):
    waiting_broadcast[m.from_user.id]=True
    bot.reply_to(m,"📢 متن یا عکس بعدی‌ات را بفرست.")

@bot.message_handler(func=lambda m: m.from_user.id==SUDO_ID and waiting_broadcast.get(m.from_user.id))
def do_broadcast(m):
    waiting_broadcast[m.from_user.id]=False; sent=0
    for gid in list(joined_groups):
        try:
            if m.content_type=="text": bot.send_message(gid,m.text)
            elif m.content_type=="photo": bot.send_photo(gid,m.photo[-1].file_id,caption=(m.caption or ""))
            sent+=1
        except: pass
    bot.reply_to(m,f"✅ به {sent} گروه ارسال شد.")

# ========= ضد لینک + جانم سودو =========
@bot.message_handler(content_types=['text'])
def text_handler(m):
    if m.from_user.id==SUDO_ID and m.text.strip()=="ربات":
        return bot.reply_to(m,"جانم سودو 👑")
    if lock_links.get(m.chat.id) and not is_admin(m.chat.id,m.from_user.id):
        if re.search(r"(t\.me|http)",(m.text or "").lower()):
            try: bot.delete_message(m.chat.id,m.message_id)
            except: pass

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
