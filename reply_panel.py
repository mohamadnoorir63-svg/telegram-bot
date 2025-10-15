# ---------------------- 🎯 افزودن پاسخ (نسخه پیشرفته) ----------------------
async def add_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن پاسخ جدید — پشتیبانی از ریپلای و فرمت ="""
    message = update.message
    text = message.text.strip().replace("افزودن پاسخ", "").strip()
    data = load_replies()
    replies = data.get("replies", {})

    # حالت ۱: فرمت مستقیم => افزودن پاسخ <کلید>=<پاسخ>
    if "=" in text:
        try:
            key, reply_text = text.split("=", 1)
            key, reply_text = key.strip(), reply_text.strip()
            if not key or not reply_text:
                raise ValueError
        except:
            return await message.reply_text("❗ استفاده صحیح: افزودن پاسخ <نام>=<پاسخ>")

        if key not in replies:
            replies[key] = []
        if reply_text not in replies[key]:
            replies[key].append(reply_text)
            save_replies(data)
            return await message.reply_text(f"✅ پاسخ برای '{key}' ذخیره شد!\n💬 {reply_text}")
        else:
            return await message.reply_text("⚠️ این پاسخ از قبل وجود دارد!")

    # حالت ۲: وقتی روی پیام ریپلای زدی
    if message.reply_to_message and text:
        key = text
        reply_text = message.reply_to_message.text.strip() if message.reply_to_message.text else ""
        if not reply_text:
            return await message.reply_text("❗ باید روی یک پیام متنی ریپلای بزنی!")

        if key not in replies:
            replies[key] = []
        if reply_text not in replies[key]:
            replies[key].append(reply_text)
            save_replies(data)
            return await message.reply_text(f"✅ پاسخ برای '{key}' ذخیره شد!\n💬 {reply_text}")
        else:
            return await message.reply_text("⚠️ این پاسخ از قبل وجود دارد!")

    # حالت ۳: بدون پارامتر معتبر
    return await message.reply_text(
        "❗ استفاده صحیح:\n"
        "1️⃣ افزودن پاسخ <نام>=<پاسخ>\n"
        "2️⃣ یا روی پیام ریپلای بزن و بنویس:\n"
        "افزودن پاسخ <نام>"
    )
