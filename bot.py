# ========= پین / حذف پین =========
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

# ========= لیست‌ها =========
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
    # فعلاً فقط سودو تعریف شده
    bot.reply_to(m, f"📋 مدیران ربات:\n• سودو: <code>{SUDO_ID}</code>")

# ========= پاکسازی =========
@bot.message_handler(func=lambda m: m.text == "پاکسازی")
def clear_messages(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    for i in range(m.message_id - 1, m.message_id - 51, -1):
        try: bot.delete_message(m.chat.id, i)
        except: pass
    bot.reply_to(m, "🧹 ۵۰ پیام آخر پاک شد.")

# ========= ارسال پیام همگانی (فقط سودو) =========
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

# ========= ضد لینک + کفِ هندلر متنی =========
@bot.message_handler(content_types=['text'])
def text_handler(m):
    # فقط اگر سودو بگه «ربات»
    if m.from_user.id == SUDO_ID and m.text.strip() == "ربات":
        return bot.reply_to(m, "جانم سودو 👑")

    # حذف لینک برای غیر ادمین‌ها وقتی قفل لینک فعاله
    if lock_links.get(m.chat.id, False) and not is_admin(m.chat.id, m.from_user.id):
        if re.search(r"(t\.me|telegram\.me|telegram\.org|https?://)", (m.text or "").lower()):
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
