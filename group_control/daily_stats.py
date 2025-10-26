# ======================= 📊 نمایش آمار و آیدی =======================
async def show_daily_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = str(update.effective_chat.id)
        user = update.effective_user
        today = datetime.now().strftime("%Y-%m-%d")

        text_input = update.message.text.strip().lower()

        # 📌 اگر دستور "آیدی" بود
        if text_input in ["آیدی", "id"]:
            jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")
            time_str = datetime.now().strftime("%H:%M:%S")
            user_link = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            text = (
                f"🧿 <b>اطلاعات شما:</b>\n\n"
                f"👤 {user_link}\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
                f"💬 <b>گروه:</b> {update.effective_chat.title}\n"
                f"🏷 <b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"📆 <b>تاریخ:</b> {jalali_date}\n"
                f"🕒 <b>ساعت:</b> {time_str}"
            )
            # 👇 فقط ارسال کن، حذف نکن
            await update.message.reply_text(text, parse_mode="HTML")
            return

        # 📊 آمار روزانه
        if chat_id not in stats or today not in stats[chat_id]:
            return await update.message.reply_text("ℹ️ هنوز فعالیتی برای امروز ثبت نشده است.")

        data = stats[chat_id][today]
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")

        if data["messages"]:
            top_user_id = max(data["messages"], key=lambda x: data["messages"][x])
            top_user_count = data["messages"][top_user_id]
            try:
                member = await context.bot.get_chat_member(chat_id, top_user_id)
                top_name = member.user.first_name
            except:
                top_name = "کاربر ناشناس"
        else:
            top_user_id, top_user_count, top_name = None, 0, "❌ هیچ فعالیتی نیست"

        text = (
            f"♡ <b>فعالیت‌های امروز تا این لحظه :</b>\n"
            f"➲ <b>تاریخ :</b> {jalali_date}\n"
            f"➲ <b>ساعت :</b> {time_str}\n\n"
            f"✛ <b>کل پیام‌ها :</b> {sum(data['messages'].values())}\n"
            f"✛ <b>فیلم :</b> {data['videos']}\n"
            f"✛ <b>عکس :</b> {data['photos']}\n"
            f"✛ <b>گیف :</b> {data['animations']}\n"
            f"✛ <b>ویس :</b> {data['voices']}\n"
            f"✛ <b>آهنگ :</b> {data['audios']}\n"
            f"✛ <b>استیکر :</b> {data['stickers']}\n"
            f"✛ <b>استیکر متحرک :</b> {data['animated_stickers']}\n\n"
        )

        if top_user_id:
            text += (
                f"🥇 <b>فعال‌ترین عضو:</b>\n"
                f"👤 <a href='tg://user?id={top_user_id}'>{top_name}</a>\n"
                f"📩 ({top_user_count} پیام)\n\n"
            )

        text += (
            f"✧ <b>اعضای وارد شده با لینک :</b> {data['joins_link']}\n"
            f"✧ <b>اعضای اد شده :</b> {data['joins_added']}\n"
            f"✧ <b>اعضای لفت داده :</b> {data['lefts']}\n"
        )

        # 👇 فقط ارسال کن، هیچ پیام پاک نشه
        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        print(f"⚠️ خطا در show_daily_stats: {e}")
