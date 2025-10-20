# ======================= 🌆 نمایش آب‌وهوا (عمومی و از پنل) =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت آب‌وهوا هم از چت و هم از پنل"""
    message = update.message or update.callback_query.message

    # حالت ۱️⃣: وقتی از پنل (دکمه) زده میشه
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
        context.user_data["awaiting_city"] = True
        return

    # حالت ۲️⃣: اگر در حالت انتظار نام شهر هستیم
    if context.user_data.get("awaiting_city"):
        city = update.message.text.strip()
        context.user_data["awaiting_city"] = False  # بعد از دریافت شهر، حالت انتظار غیرفعال شود
        data = await get_weather(city)
        if not data or data.get("cod") != 200:
            return await update.message.reply_text("⚠️ شهر مورد نظر پیدا نشد یا API خطا داد.")

        name = data["name"]
        country = data["sys"].get("country", "")
        temp = round(data["main"]["temp"])
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        desc = data["weather"][0]["description"]
        icon = data["weather"][0]["icon"]

        dt = datetime.fromtimestamp(data["dt"])
        local_time = dt.strftime("%H:%M")

        emoji = get_weather_emoji(icon)

        text = (
            f"{emoji} <b>وضعیت آب‌وهوا</b>\n\n"
            f"🏙 شهر: {name} {flag_emoji(country)}\n"
            f"🌤 وضعیت: {desc}\n"
            f"🌡 دما: {temp}°C\n"
            f"💧 رطوبت: {humidity}%\n"
            f"💨 باد: {wind} km/h\n"
            f"🕒 آخرین بروزرسانی: {local_time}"
        )
        return await update.message.reply_text(text, parse_mode="HTML")

    # حالت ۳️⃣: وقتی مستقیماً کاربر می‌نویسه مثل «آب و هوا تهران»
    if update.message and update.message.text:
        text = update.message.text.strip()
        if text.startswith("آب و هوا"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                return await update.message.reply_text("🌆 لطفاً بنویس:\nآب و هوا [نام شهر]\nمثلاً: آب و هوا تهران")
            city = parts[-1]
            data = await get_weather(city)
            if not data or data.get("cod") != 200:
                return await update.message.reply_text("⚠️ شهر مورد نظر پیدا نشد یا API خطا داد.")

            name = data["name"]
            country = data["sys"].get("country", "")
            temp = round(data["main"]["temp"])
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            desc = data["weather"][0]["description"]
            icon = data["weather"][0]["icon"]

            dt = datetime.fromtimestamp(data["dt"])
            local_time = dt.strftime("%H:%M")

            emoji = get_weather_emoji(icon)

            text = (
                f"{emoji} <b>وضعیت آب‌وهوا</b>\n\n"
                f"🏙 شهر: {name} {flag_emoji(country)}\n"
                f"🌤 وضعیت: {desc}\n"
                f"🌡 دما: {temp}°C\n"
                f"💧 رطوبت: {humidity}%\n"
                f"💨 باد: {wind} km/h\n"
                f"🕒 آخرین بروزرسانی: {local_time}"
            )
            return await update.message.reply_text(text, parse_mode="HTML")
