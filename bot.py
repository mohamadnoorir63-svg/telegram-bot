# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

# ================== تنظیمات ==================
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754  # آیدی عددی سودو
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
⚠️ اخطار (ریپلای) — سه اخطار = بن
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (ریپلای روی عکس و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر یا پاکسازی 9999)
✍️ فونت [متن دلخواه]
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ——— ذخیره گروه‌ها برای «ارسال» ———
joined_groups = set()
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group","supergroup"):
            joined_groups.add(chat.id)
    except: pass

# ——— ادمین‌چک ———
def is_admin(chat_id, user_id):
    if user_id == SUDO_ID: return True
    try:
        st = bot.get_chat_member(chat_id,user_id).status
        return st in ("administrator","creator")
    except: return False

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: m.text=="راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text=="ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text=="تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text=="ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text=="آمار")
def stats(m):
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

# ========= خوشامد =========
welcome_enabled,welcome_texts,welcome_photos={}, {}, {}

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    if not welcome_enabled.get(m.chat.id): return
    for u in m.new_chat_members:
        name=u.first_name or ""
        txt=welcome_texts.get(m.chat.id,"خوش آمدی 🌹").replace("{name}",name)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else: bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m:m.text=="خوشامد روشن")
def w_on(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    welcome_enabled[m.chat.id]=True; bot.reply_to(m,"✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m:m.text=="خوشامد خاموش")
def w_off(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    welcome_enabled[m.chat.id]=False; bot.reply_to(m,"❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m:m.text and m.text.startswith("خوشامد متن"))
def w_txt(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    txt=m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id]=txt; bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m:m.reply_to_message and m.text=="ثبت عکس")
def w_photo(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
    bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")

# ========= قفل‌ها =========
locks={k:{} for k in["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}

def lock_toggle(cid,typ,state): locks[typ][cid]=state

@bot.message_handler(func=lambda m: m.text in [
"قفل لینک","باز کردن لینک","قفل استیکر","باز کردن استیکر",
"قفل ربات","باز کردن ربات","قفل تبچی","باز کردن تبچی",
"قفل گروه","باز کردن گروه","قفل عکس","باز کردن عکس",
"قفل ویدیو","باز کردن ویدیو","قفل گیف","باز کردن گیف",
"قفل فایل","باز کردن فایل","قفل موزیک","باز کردن موزیک",
"قفل ویس","باز کردن ویس","قفل فوروارد","باز کردن فوروارد"])
def toggle(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    t=m.text;cid=m.chat.id
    if   t=="قفل لینک":lock_toggle(cid,"links",True);bot.reply_to(m,"🔒 لینک قفل شد.")
    elif t=="باز کردن لینک":lock_toggle(cid,"links",False);bot.reply_to(m,"🔓 لینک آزاد شد.")
    elif t=="قفل استیکر":lock_toggle(cid,"stickers",True);bot.reply_to(m,"🧷 استیکر قفل شد.")
    elif t=="باز کردن استیکر":lock_toggle(cid,"stickers",False);bot.reply_to(m,"🧷 استیکر آزاد شد.")
    elif t=="قفل ربات":lock_toggle(cid,"bots",True);bot.reply_to(m,"🤖 ربات قفل شد.")
    elif t=="باز کردن ربات":lock_toggle(cid,"bots",False);bot.reply_to(m,"🤖 ربات آزاد شد.")
    elif t=="قفل تبچی":lock_toggle(cid,"tabchi",True);bot.reply_to(m,"🚫 تبچی قفل شد.")
    elif t=="باز کردن تبچی":lock_toggle(cid,"tabchi",False);bot.reply_to(m,"🚫 تبچی آزاد شد.")
    elif t=="قفل گروه":lock_toggle(cid,"group",True);bot.set_chat_permissions(cid,types.ChatPermissions(can_send_messages=False));bot.reply_to(m,"🔐 گروه قفل شد.")
    elif t=="باز کردن گروه":lock_toggle(cid,"group",False);bot.set_chat_permissions(cid,types.ChatPermissions(can_send_messages=True));bot.reply_to(m,"✅ گروه باز شد.")
    elif t=="قفل عکس":lock_toggle(cid,"photo",True);bot.reply_to(m,"🖼 عکس قفل شد.")
    elif t=="باز کردن عکس":lock_toggle(cid,"photo",False);bot.reply_to(m,"🖼 عکس آزاد شد.")
    elif t=="قفل ویدیو":lock_toggle(cid,"video",True);bot.reply_to(m,"🎥 ویدیو قفل شد.")
    elif t=="باز کردن ویدیو":lock_toggle(cid,"video",False);bot.reply_to(m,"🎥 ویدیو آزاد شد.")
    elif t=="قفل گیف":lock_toggle(cid,"gif",True);bot.reply_to(m,"🎭 گیف قفل شد.")
    elif t=="باز کردن گیف":lock_toggle(cid,"gif",False);bot.reply_to(m,"🎭 گیف آزاد شد.")
    elif t=="قفل فایل":lock_toggle(cid,"file",True);bot.reply_to(m,"📎 فایل قفل شد.")
    elif t=="باز کردن فایل":lock_toggle(cid,"file",False);bot.reply_to(m,"📎 فایل آزاد شد.")
    elif t=="قفل موزیک":lock_toggle(cid,"music",True);bot.reply_to(m,"🎶 موزیک قفل شد.")
    elif t=="باز کردن موزیک":lock_toggle(cid,"music",False);bot.reply_to(m,"🎶 موزیک آزاد شد.")
    elif t=="قفل ویس":lock_toggle(cid,"voice",True);bot.reply_to(m,"🎙 ویس قفل شد.")
    elif t=="باز کردن ویس":lock_toggle(cid,"voice",False);bot.reply_to(m,"🎙 ویس آزاد شد.")
    elif t=="قفل فوروارد":lock_toggle(cid,"forward",True);bot.reply_to(m,"🔄 فوروارد قفل شد.")
    elif t=="باز کردن فوروارد":lock_toggle(cid,"forward",False);bot.reply_to(m,"🔄 فوروارد آزاد شد.")

# ========= بن / سکوت =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="بن")
def ban_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m,"🚫 کاربر بن شد.")
    except: bot.reply_to(m,"❗ نتوانستم بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m,"✅ کاربر از بن خارج شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="سکوت")
def mute_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, can_send_messages=False)
        bot.reply_to(m,"🔕 کاربر سکوت شد.")
    except: bot.reply_to(m,"❗ نتوانستم سکوت کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id,
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True)
        bot.reply_to(m,"🔊 کاربر از سکوت خارج شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف سکوت کنم.")

# ========= مدیر / حذف مدیر =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="مدیر")
def promote_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        me=bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status!="administrator" or not getattr(me,"can_promote_members",False):
            return bot.reply_to(m,"❗ ربات مجوز افزودن مدیر ندارد.")
        bot.promote_chat_member(m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True,
            can_restrict_members=True, can_pin_messages=True,
            can_invite_users=True, can_manage_video_chats=True,
            can_promote_members=False)
        bot.reply_to(m,"👑 کاربر مدیر شد.")
    except: bot.reply_to(m,"❗ نتوانستم مدیر کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف مدیر")
def demote_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.promote_chat_member(m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False,
            can_restrict_members=False, can_pin_messages=False,
            can_invite_users=False, can_manage_video_chats=False,
            can_promote_members=False)
        bot.reply_to(m,"❌ کاربر از مدیریت حذف شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف مدیر کنم.")

# ========= پن / حذف پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="پن")
def pin_msg(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id, disable_notification=True)
        bot.reply_to(m,"📌 پیام پین شد.")
    except: bot.reply_to(m,"❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف پن")
def unpin_msg(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m,"❌ پین پیام برداشته شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف پین کنم.")

# ========= لیست مدیران =========
@bot.message_handler(func=lambda m: m.text=="لیست مدیران گروه")
def list_group_admins(m):
    try:
        admins=bot.get_chat_administrators(m.chat.id)
        lines=[f"• {a.user.first_name or 'بدون‌نام'} — <code>{a.user.id}</code>" for a in admins]
        bot.reply_to(m,"📋 مدیران گروه:\n"+"\n".join(lines))
    except: bot.reply_to(m,"❗ نتوانستم لیست مدیران را بگیرم.")

@bot.message_handler(func=lambda m: m.text=="لیست مدیران ربات")
def list_bot_admins(m):
    bot.reply_to(m,f"📋 مدیران ربات:\n• سودو: <code>{SUDO_ID}</code>")

# ========= اخطار =========
warnings={}
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="اخطار")
def warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{})
    warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    count=warnings[m.chat.id][uid]
    if count>=3:
        try:
            bot.ban_chat_member(m.chat.id,uid)
            bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد.")
            warnings[m.chat.id][uid]=0
        except: bot.reply_to(m,"❗ نتوانستم بن کنم.")
    else:
        bot.reply_to(m,f"⚠️ اخطار {count}/3 داده شد.")

# ========= فونت ساده =========
fonts=[lambda t: " ".join(list(t)), lambda t: t.upper(), lambda t: f"★{t}★"]
@bot.message_handler(func=lambda m: m.text and m.text.startswith("فونت"))
def font_cmd(m):
    txt=m.text.replace("فونت","",1).strip()
    if not txt: return bot.reply_to(m,"❗ متنی وارد کن")
    out="\n".join([f"{i+1}- {f(txt)}" for i,f in enumerate(fonts)])
    bot.reply_to(m,"✍️ متن با فونت‌های مختلف:\n"+out)

# ========= پاکسازی =========
@bot.message_handler(func=lambda m: m.text.startswith("پاکسازی"))
def clear_msgs(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    parts=m.text.split()
    n=9999 if len(parts)>1 else 50
    for i in range(m.message_id-1, m.message_id-n-1, -1):
        try: bot.delete_message(m.chat.id,i)
        except: pass
    bot.reply_to(m,f"🧹 {n} پیام پاک شد.")

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
