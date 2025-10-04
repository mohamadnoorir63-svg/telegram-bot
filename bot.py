# -*- coding: utf-8 -*-
# Persian Group Manager Bot – pyTelegramBotAPI==4.14.0
import os, json, re, time
from datetime import datetime, timedelta, timezone
import telebot
from telebot import types

# ====== CONFIG ======
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"  # آخرین توکن
SUDO_ID = 7089376754                                         # آیدی سودو
IR_TZ   = timezone(timedelta(hours=3, minutes=30))
bot     = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ====== HELP TEXTS ======
HELP_GROUP = (
"📌 دستورات گروه:\n"
"• ساعت | تاریخ | آمار | ایدی | لینک | راهنما\n"
"• قفل لینک / باز کردن لینک\n"
"• قفل استیکر / باز کردن استیکر\n"
"• قفل گروه / باز کردن گروه\n"
"• پاکسازی (حذف ۵۰ پیام اخیر)\n"
"• بن / حذف بن (ریپلای) — سکوت / حذف سکوت (ریپلای)\n"
"• مدیر / حذف مدیر (ریپلای)\n"
"• خوشامد روشن / خوشامد خاموش\n"
"• خوشامد متن <متن>\n"
"• ثبت عکس (روی عکس ریپلای کن و بفرست ثبت عکس)\n"
"• لفت بده (فقط سودو)\n"
)

# ====== WELCOME ======
@bot.message_handler(content_types=['new_chat_members'])
def welcome_members(m):
    group_name = m.chat.title or ""
    for u in m.new_chat_members:
        name = (u.first_name or "") + (" " + u.last_name if u.last_name else "")
        text = f"🌹 خوش آمدی {name} به گروه {group_name}"
        bot.send_message(m.chat.id, text)

# ====== BASIC GROUP COMMANDS ======
def ir_time(): return datetime.now(IR_TZ)

@bot.message_handler(func=lambda m: m.text in ("راهنما","/help","help"))
def help_cmd(m): bot.reply_to(m, HELP_GROUP)

@bot.message_handler(func=lambda m: m.text in ("ساعت","/time","time"))
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: <b>{ir_time().strftime('%H:%M:%S')}</b>")

@bot.message_handler(func=lambda m: m.text in ("تاریخ","/date","date"))
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: <b>{ir_time().strftime('%Y-%m-%d')}</b>")

@bot.message_handler(func=lambda m: m.text in ("آمار","/stats","stats"))
def stats_group(m):
    try: cnt = bot.get_chat_member_count(m.chat.id)
    except: cnt = "نامشخص"
    bot.reply_to(m, f"👥 اعضا: <b>{cnt}</b>")

@bot.message_handler(func=lambda m: m.text in ("ایدی","/id","id"))
def id_cmd(m):
    bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text in ("لینک","/link","بهشت"))
def link_cmd(m):
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 {link}")
    except: bot.reply_to(m, "⚠️ نتونستم لینک بسازم، باید ادمین با اجازه Invite باشم.")

# ====== LEAVE (SUDO ONLY) ======
@bot.message_handler(func=lambda m: m.text in ("لفت بده","/leave"))
def leave_here(m):
    if m.from_user.id != SUDO_ID: return
    bot.reply_to(m, "خداحافظ 👋")
    try: bot.leave_chat(m.chat.id)
    except: pass

# ====== RUN ======
print("🤖 Bot is running...")
bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
