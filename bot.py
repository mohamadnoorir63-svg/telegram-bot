# ================== لیست مدیران ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران گروه")
def admins_list(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        admins=bot.get_chat_administrators(m.chat.id)
        txt="👑 مدیران گروه:\n"+"\n".join([f"▪️ {a.user.first_name} — <code>{a.user.id}</code>" for a in admins])
    except: txt="❗ خطا"
    bot.reply_to(m,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران ربات")
def bot_admins_list(m):
    if not is_sudo(m.from_user.id): return
    txt="👑 مدیران ربات:\n"+"\n".join([str(x) for x in bot_admins])
    bot.reply_to(m,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست سودو")
def sudo_list(m):
    if not is_sudo(m.from_user.id): return
    txt="⚡ سودوها:\n"+"\n".join([str(x) for x in sudo_ids])
    bot.reply_to(m,txt)

# ================== راهنما ==================
HELP_TEXT="""
📖 دستورات اصلی:

⏰ ساعت | 🆔 ایدی | 📊 آمار | 📎 لینک
🎉 خوشامد روشن/خاموش | ✍️ خوشامد متن | 🖼 ثبت عکس
🔒 قفل‌ها (لینک، عکس، ویدیو، ...)
🚫 بن | ✅ حذف بن | 🔕 سکوت | 🔊 حذف سکوت
⚠️ اخطار | حذف اخطار
👑 مدیر | ❌ حذف مدیر
📌 پن | ❌ حذف پن
🧾 اصل / اصل من / ثبت اصل
😂 جوک | 🔮 فال
🧹 پاکسازی / حذف [عدد]
📋 لیست مدیران گروه / ربات / سودو
"""
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if m.chat.type!="private" and not is_admin(m.chat.id,m.from_user.id): return
    bot.reply_to(m,HELP_TEXT)

# ================== استارت ==================
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type!="private": return
    kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("➕ افزودن ربات به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new"))
    kb.add(types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}"))
    txt=("👋 سلام!\n\nمن ربات مدیریت گروه هستم 🤖\n\n"
         "📌 امکانات:\n"
         "• قفل‌ها\n• خوشامد\n• اخطار/بن/سکوت\n• اصل\n• جوک و فال\n• ابزار مدیریتی\n\n➕ منو به گروهت اضافه کن.")
    bot.send_message(m.chat.id,txt,reply_markup=kb)

# ================== اجرا ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True,timeout=30)
