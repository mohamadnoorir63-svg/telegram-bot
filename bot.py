# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re
import os

# ================== تنظیمات ==================
TOKEN   = os.getenv("BOT_TOKEN")   # گرفتن توکن از Config Vars
SUDO_ID = int(os.getenv("SUDO_ID"))  # گرفتن آیدی سودو از Config Vars
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

# ========= سودو =========
sudo_ids = {SUDO_ID}
def is_sudo(uid): return uid in sudo_ids

# ========= کمک‌تابع =========
def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except: return False

def cmd_text(m): return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ——— ذخیره گروه‌ها برای ارسال همگانی ———
joined_groups = set()
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group","supergroup"):
            joined_groups.add(chat.id)
    except: pass

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما") 
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: cmd_text(m)=="تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def stats(m):
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name=(u.first_name or "")
        txt=welcome_texts.get(m.chat.id,"خوش آمدی 🌹").replace("{name}",name)
        if m.chat.id in welcome_photos: bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else: bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def w_on(m): 
    if is_admin(m.chat.id,m.from_user.id): welcome_enabled[m.chat.id]=True; bot.reply_to(m,"✅ خوشامد روشن شد.")

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m): 
    if is_admin(m.chat.id,m.from_user.id): welcome_enabled[m.chat.id]=False; bot.reply_to(m,"❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن"))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن","",1).strip()
        bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_photo(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")

# ========= قفل‌ها =========
locks={k:{} for k in ["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={"لینک":"links","استیکر":"stickers","ربات":"bots","تبچی":"tabchi","گروه":"group","عکس":"photo","ویدیو":"video","گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("باز کردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    t=cmd_text(m); enable=t.startswith("قفل ")
    name=t.replace("قفل ","",1).replace("باز کردن ","",1).strip()
    key=LOCK_MAP.get(name); 
    if not key: return
    if key=="group":
        try: bot.set_chat_permissions(m.chat.id,types.ChatPermissions(can_send_messages=not enable))
        except: return bot.reply_to(m,"❗ نیاز به دسترسی محدودسازی")
    locks[key][m.chat.id]=enable
    bot.reply_to(m,f"{'🔒' if enable else '🔓'} {name} {'فعال شد' if enable else 'آزاد شد'}")

# ========= بن / سکوت =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id); bot.reply_to(m,"🚫 بن شد.")
        except: bot.reply_to(m,"❗ نتوانستم بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id); bot.reply_to(m,"✅ بن حذف شد.")
        except: bot.reply_to(m,"❗ نتوانستم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False); bot.reply_to(m,"🔕 سکوت شد.")
        except: bot.reply_to(m,"❗ خطا")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=True,can_send_media_messages=True,can_send_other_messages=True,can_add_web_page_previews=True)
            bot.reply_to(m,"🔊 سکوت برداشته شد.")
        except: bot.reply_to(m,"❗ خطا")

# ========= اخطار =========
warnings={}; MAX_WARNINGS=3
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{}); warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    c=warnings[m.chat.id][uid]
    if c>=MAX_WARNINGS:
        try: bot.ban_chat_member(m.chat.id,uid); bot.reply_to(m,"🚫 با ۳ اخطار بن شد."); warnings[m.chat.id][uid]=0
        except: bot.reply_to(m,"❗ خطا در بن")
    else: bot.reply_to(m,f"⚠️ اخطار {c}/{MAX_WARNINGS}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid=m.reply_to_message.from_user.id
        if uid in warnings.get(m.chat.id,{}): warnings[m.chat.id][uid]=0; bot.reply_to(m,"✅ اخطارها حذف شد.")
        else: bot.reply_to(m,"ℹ️ اخطاری نیست.")

# ========= مدیر / حذف مدیر =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="مدیر")
def promote(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.promote_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_manage_chat=True,can_delete_messages=True,can_restrict_members=True,can_pin_messages=True,can_invite_users=True,can_manage_video_chats=True)
        bot.reply_to(m,"👑 مدیر شد.")
        except: bot.reply_to(m,"❗ خطا")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف مدیر")
def demote(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.promote_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_manage_chat=False,can_delete_messages=False,can_restrict_members=False,can_pin_messages=False,can_invite_users=False,can_manage_video_chats=False)
        bot.reply_to(m,"❌ مدیر حذف شد.")
        except: bot.reply_to(m,"❗ خطا")

# ========= پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="پن")
def pin(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.pin_chat_message(m.chat.id,m.reply_to_message.message_id,disable_notification=True); bot.reply_to(m,"📌 پین شد.")
        except: bot.reply_to(m,"❗ خطا")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف پن")
def unpin(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.unpin_chat_message(m.chat.id,m.reply_to_message.message_id); bot.reply_to(m,"❌ پین حذف شد.")
        except: bot.reply_to(m,"❗ خطا")

# ========= لیست =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران گروه")
def list_group_admins(m):
    try:
        admins=bot.get_chat_administrators(m.chat.id)
        lines=[f"• {(a.user.first_name or '')} — <code>{a.user.id}</code>" for a in admins]
        bot.reply_to(m,"📋 مدیران گروه:\n"+"\n".join(lines))
    except: bot.reply_to(m,"❗ خطا")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران ربات")
def list_sudos(m): bot.reply_to(m,"📋 سودوها:\n"+"\n".join([f"<code>{i}</code>" for i in sudo_ids]))

# ========= پاکسازی =========
def bulk_delete(m,n):
    if not is_admin(m.chat.id,m.from_user.id): return
    d=0
    for i in range(m.message_id-1,m.message_id-n-1,-1):
        try: bot.delete_message(m.chat.id,i); d+=1
        except: pass
    bot.reply_to(m,f"🧹 {d} پیام پاک شد.")

@bot.message_handler(func=lambda m: cmd_text(m)=="پاکسازی") 
def c50(m): bulk_delete(m,50)

# ========= ارسال همگانی =========
waiting_broadcast={}
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ارسال")
def ask_bc(m): waiting_broadcast[m.from_user.id]=True; bot.reply_to(m,"📢 پیام بعدی را بفرست.")
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and waiting_broadcast.get(m.from_user.id),content_types=['text','photo'])
def do_bc(m):
    waiting_broadcast[m.from_user.id]=False; s=0
    for gid in list(joined_groups):
        try:
            if m.content_type=="text": bot.send_message(gid,m.text)
            elif m.content_type=="photo": bot.send_photo(gid,m.photo[-1].file_id,caption=(m.caption or ""))
            s+=1
        except: pass
    bot.reply_to(m,f"✅ به {s} گروه ارسال شد.")

# ========= مدیریت سودو =========
@bot.message_handler(func=lambda m: cmd_text(m).startswith("افزودن سودو "))
def add_sudo(m):
    if not is_sudo(m.from_user.id): return
    try: uid=int(cmd_text(m).split()[-1])
    except: return bot.reply_to(m,"❗ آیدی نامعتبر")
    sudo_ids.add(uid); bot.reply_to(m,f"✅ <code>{uid}</code> به سودوها اضافه شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف سودو "))
def del_sudo(m):
    if not is_sudo(m.from_user.id): return
    try: uid=int(cmd_text(m).split()[-1])
    except: return bot.reply_to(m,"❗ آیدی نامعتبر")
    if uid==SUDO_ID: return bot.reply_to(m,"❗ سودوی اصلی حذف نمیشود.")
    if uid in sudo_ids: sudo_ids.remove(uid); bot.reply_to(m,f"✅ <code>{uid}</code> حذف شد.")
    else: bot.reply_to(m,"ℹ️ این آیدی در سودوها نیست.")

# ========= لفت بده =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لفت بده")
def leave_cmd(m):
    if is_sudo(m.from_user.id):
        bot.send_message(m.chat.id,"به دستور سودو خارج می‌شوم 👋")
        try: bot.leave_chat(m.chat.id)
        except: pass

# ========= جواب سودو =========
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def sudo_reply(m): bot.reply_to(m,"جانم سودو 👑")

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
