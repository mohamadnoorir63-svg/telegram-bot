
    if not target_user:
        return

    # رمزگذاری متن
    encrypted_text = fernet.encrypt(text.encode()).decode()

    # ذخیره نجوا
    whispers = load_whispers()
    whisper_id = f"{chat_id}_{sender.id}_{target_user.id}_{len(whispers)+1}"
    whispers[whisper_id] = {
        "from_id": sender.id,
        "from_name": sender.first_name,
        "to_id": target_user.id,
        "to_name": target_user.first_name,
        "text": encrypted_text,
        "chat": chat_id
    }
    save_whispers(whispers)

    # ارسال اعلان عمومی با دکمه در گروه
    button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(f"📩 مشاهده نجوا برای {target_user.first_name}", callback_data=f"whisper:{whisper_id}")
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🤫 {target_user.first_name} شما یک نجوا از طرف {sender.first_name} دارید!",
        reply_markup=button
    )

    # حذف خودکار بعد از مدت مشخص شده
    async def auto_delete():
        await asyncio.sleep(auto_delete_seconds)
        data = load_whispers()
        if whisper_id in data:
            del data[whisper_id]
            save_whispers(data)

    asyncio.create_task(auto_delete())

async def open_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش popup فقط برای گیرنده"""
    query = update.callback_query
    whisper_id = query.data.split(":")[1]
    whispers = load_whispers()
    whisper = whispers.get(whisper_id)

    if not whisper:
        await query.answer("⚠️ این نجوا منقضی شده یا حذف شده.", show_alert=True)
        return

    if query.from_user.id != whisper["to_id"]:
        await query.answer("🚫 این نجوا برای شما نیست!", show_alert=True)
        return

    decrypted_text = fernet.decrypt(whisper["text"].encode()).decode()

    # نمایش popup فقط برای گیرنده
    await query.answer(
        text=f"💌 نجوا از طرف {whisper['from_name']}:\n\n{decrypted_text}",
        show_alert=True
    )

def register_whisper_handler(application, auto_delete_seconds: int = 300):
    """ثبت تمام handlerهای نجوا روی Application اصلی"""
    # پیام‌هایی که با "Najwa " شروع می‌شوند
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        lambda update, context: whisper_message(update, context, auto_delete_seconds)
    ))
    # دکمه باز کردن نجوا
    application.add_handler(CallbackQueryHandler(open_whisper, pattern=r"^whisper:"))
