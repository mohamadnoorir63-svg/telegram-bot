from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


# 🌐 تابع نمایش پنل لینک‌ها
async def link_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("• نمایش لینک بصورت متن", callback_data="link_show_text")],
        [InlineKeyboardButton("• نمایش لینک بصورت عکس", callback_data="link_show_photo")],
        [InlineKeyboardButton("• ساخت لینک یکبار مصرف", callback_data="link_create_once")],
        [InlineKeyboardButton("• ساخت لینک درخواست عضویت", callback_data="link_invite_request")],
        [InlineKeyboardButton("• ارسال لینک به پیوی", callback_data="link_send_private")],
        [InlineKeyboardButton("• بازگشت به منوی اصلی", callback_data="link_back_main")],
        [InlineKeyboardButton("• بستن", callback_data="link_close")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # اگر پیام از CallbackQuery بوده
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            "─━─━─━ ✦ ━─━─━─\n🔗 <b>شیوه دریافت لینک</b>\n─━─━─━ ✦ ━─━─━─",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "─━─━─━ ✦ ━─━─━─\n🔗 <b>شیوه دریافت لینک</b>\n─━─━─━ ✦ ━─━─━─",
            parse_mode="HTML",
            reply_markup=reply_markup
        )


# ⚙️ مدیریت دکمه‌ها
async def link_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat = update.effective_chat
    user = update.effective_user

    await query.answer()

    # 🔹 نمایش لینک به صورت متن
    if data == "link_show_text":
        invite = await context.bot.export_chat_invite_link(chat.id)
        keyboard = [[InlineKeyboardButton("◀ بازگشت", callback_data="link_back")]]
        await query.edit_message_text(
            f"📎 <b>لینک گروه:</b>\n{invite}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 🔹 نمایش لینک بصورت عکس
    elif data == "link_show_photo":
        invite = await context.bot.export_chat_invite_link(chat.id)
        keyboard = [[InlineKeyboardButton("◀ بازگشت", callback_data="link_back")]]
        await query.edit_message_text(
            f"🖼 <b>نمایش لینک بصورت عکس</b>\n\n📎 {invite}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 🔹 ساخت لینک یکبار مصرف
    elif data == "link_create_once":
        link = await context.bot.create_chat_invite_link(
            chat.id, member_limit=1
        )
        keyboard = [[InlineKeyboardButton("◀ بازگشت", callback_data="link_back")]]
        await query.edit_message_text(
            f"🕐 <b>لینک یکبار مصرف ساخته شد:</b>\n{link.invite_link}\n\n"
            f"👥 <b>تعداد مجاز عضویت:</b> ۱ نفر",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 🔹 ساخت لینک درخواست عضویت
    elif data == "link_invite_request":
        link = await context.bot.create_chat_invite_link(
            chat.id, creates_join_request=True
        )
        keyboard = [[InlineKeyboardButton("◀ بازگشت", callback_data="link_back")]]
        await query.edit_message_text(
            f"📨 <b>لینک درخواست عضویت ساخته شد:</b>\n{link.invite_link}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 🔹 ارسال لینک به پیوی
    elif data == "link_send_private":
        invite = await context.bot.export_chat_invite_link(chat.id)
        try:
            await context.bot.send_message(user.id, f"📎 لینک گروه شما:\n{invite}")
            await query.edit_message_text("📩 لینک با موفقیت به پیوی شما ارسال شد ✅")
        except:
            await query.edit_message_text("⚠️ نمی‌تونم لینک رو به پیوی‌ات بفرستم (احتمالاً استارت نزدی).")

    # 🔙 بازگشت به منوی لینک‌ها
    elif data == "link_back":
        await link_panel(update, context)

    # 🔙 بازگشت به منوی اصلی ربات
    elif data == "link_back_main":
        from panels.panel_menu import panel_menu
        await panel_menu(update, context)

    # ❌ بستن
    elif data == "link_close":
        await query.edit_message_text("❌ منو بسته شد.")
