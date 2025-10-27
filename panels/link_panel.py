# panels/link_panel.py
import os, json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatInviteLink
from telegram.ext import ContextTypes

# مسیر فایل اطلاعات گروه
GROUP_CTRL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "group_control.json")

def load_group_data():
    if os.path.exists(GROUP_CTRL_FILE):
        try:
            with open(GROUP_CTRL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_group_data(data):
    with open(GROUP_CTRL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ========================== پنل اصلی لینک ==========================
async def link_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("⚠️ این دستور فقط در گروه قابل استفاده است.")

    keyboard = [
        [InlineKeyboardButton("📄 نمایش لینک", callback_data="link_show")],
        [InlineKeyboardButton("🔁 ساخت لینک جدید", callback_data="link_create")],
        [InlineKeyboardButton("🧾 لینک موقت / محدود", callback_data="link_temp")],
        [InlineKeyboardButton("✉️ ارسال به پیوی", callback_data="link_send")],
        [InlineKeyboardButton("📚 راهنما", callback_data="link_help")],
        [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
    ]
    text = (
        "🔗 <b>مدیریت لینک گروه</b>\n\n"
        "از گزینه‌های زیر برای مشاهده یا ساخت لینک استفاده کنید.\n"
        "ربات باید در گروه ادمین باشد و اجازه ساخت لینک داشته باشد."
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


# ========================== دکمه‌های پنل ==========================
async def link_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat = query.message.chat
    chat_id = chat.id
    user = query.from_user

    gdata = load_group_data()
    group = gdata.setdefault(str(chat_id), {})

    def store_link(link, meta):
        group["invite"] = {
            "link": link,
            "created": datetime.now().isoformat(),
            "meta": meta
        }
        gdata[str(chat_id)] = group
        save_group_data(gdata)

    # ========= نمایش لینک =========
    if data == "link_show":
        inv = group.get("invite")
        if inv and inv.get("link"):
            text = (
                f"🔗 <b>لینک فعلی گروه:</b>\n\n{inv['link']}\n\n"
                f"📆 ساخته‌شده در: {inv.get('created')[:19].replace('T',' ')}"
            )
        else:
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                meta = {"type": "default"}
                store_link(link, meta)
                text = f"✅ لینک جدید ایجاد شد:\n\n{link}"
            except Exception as e:
                text = f"⚠️ ربات باید ادمین باشد تا لینک را بگیرد.\n\n<code>{e}</code>"

        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= ساخت لینک جدید =========
    if data == "link_create":
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(chat_id)
            store_link(link_obj.invite_link, {"type": "permanent"})
            text = f"✅ لینک جدید ساخته شد:\n\n{link_obj.invite_link}"
        except Exception as e:
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                store_link(link, {"type": "fallback"})
                text = f"✅ لینک جدید ساخته شد:\n\n{link}"
            except Exception as err:
                text = f"⚠️ خطا در ساخت لینک:\n<code>{err}</code>"

        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= لینک موقت =========
    if data == "link_temp":
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(
                chat_id,
                expire_date=datetime.utcnow() + timedelta(hours=24),
                member_limit=5
            )
            store_link(link_obj.invite_link, {"type": "temp", "expire": "24h", "limit": 5})
            text = (
                f"🕒 لینک موقت ساخته شد:\n\n{link_obj.invite_link}\n\n"
                "⏳ اعتبار: ۲۴ ساعت\n👥 محدودیت: ۵ نفر"
            )
        except Exception as e:
            text = f"⚠️ خطا در ساخت لینک موقت:\n<code>{e}</code>"

        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= ارسال به پیوی =========
    if data == "link_send":
        inv = group.get("invite")
        if not inv or not inv.get("link"):
            text = "ℹ️ هنوز هیچ لینکی ثبت نشده. ابتدا لینک بساز."
        else:
            try:
                await context.bot.send_message(user.id, f"🔗 لینک گروه:\n{inv['link']}")
                text = "✅ لینک به پیوی شما ارسال شد."
            except:
                text = "⚠️ نمی‌توان لینک را به پیوی فرستاد. ابتدا به ربات پیام بده."

        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= راهنما =========
    if data == "link_help":
        text = (
            "📚 <b>راهنمای لینک</b>\n\n"
            "• ربات باید ادمین باشد تا لینک واقعی بسازد.\n"
            "• لینک موقت پس از ۲۴ ساعت یا ۵ عضو باطل می‌شود.\n"
            "• برای ارسال به پیوی، ابتدا به ربات پیام بده.\n"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= بازگشت به صفحه اصلی =========
    if data == "link_main":
        keyboard = [
            [InlineKeyboardButton("📄 نمایش لینک", callback_data="link_show")],
            [InlineKeyboardButton("🔁 ساخت لینک جدید", callback_data="link_create")],
            [InlineKeyboardButton("🧾 لینک موقت / محدود", callback_data="link_temp")],
            [InlineKeyboardButton("✉️ ارسال به پیوی", callback_data="link_send")],
            [InlineKeyboardButton("📚 راهنما", callback_data="link_help")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        text = (
            "🔗 <b>مدیریت لینک گروه</b>\n\n"
            "از گزینه‌های زیر برای مشاهده یا ساخت لینک استفاده کنید."
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= بستن =========
    if data == "link_close":
        try:
            await query.edit_message_text("❌ پنل لینک بسته شد.")
        except:
            pass
