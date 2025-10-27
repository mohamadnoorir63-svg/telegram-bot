import os, json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatInviteLink
from telegram.ext import ContextTypes

# 📂 مسیر فایل داده گروه‌ها
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


# ===================== 🧭 پنل اصلی =====================
async def link_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("⚠️ فقط در گروه قابل استفاده است.")

    keyboard = [
        [InlineKeyboardButton("📄 نمایش لینک", callback_data="link_show")],
        [InlineKeyboardButton("🔁 ساخت لینک جدید", callback_data="link_create_confirm")],
        [InlineKeyboardButton("🧾 ساخت لینک محدود", callback_data="link_temp_ask")],
        [InlineKeyboardButton("✉️ ارسال به پیوی", callback_data="link_send")],
        [InlineKeyboardButton("📚 راهنما", callback_data="link_help")],
        [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
    ]
    text = (
        "🔗 <b>پنل مدیریت لینک گروه</b>\n\n"
        "از گزینه‌های زیر برای مشاهده، ساخت یا ارسال لینک استفاده کن."
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


# ===================== ⚙️ کنترل دکمه‌ها =====================
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
        group["invite"] = {"link": link, "created": datetime.now().isoformat(), "meta": meta}
        gdata[str(chat_id)] = group
        save_group_data(gdata)

    # ========= نمایش لینک =========
    if data == "link_show":
        inv = group.get("invite")
        if inv and inv.get("link"):
            text = f"🔗 <b>لینک فعلی گروه:</b>\n\n{inv['link']}"
        else:
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                store_link(link, {"type": "default"})
                text = f"✅ لینک جدید ساخته شد:\n{link}"
            except Exception as e:
                text = f"⚠️ ربات باید ادمین باشد تا لینک را بگیرد.\n\n<code>{e}</code>"

        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]]
        return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    # ========= تایید ساخت لینک دائمی =========
    if data == "link_create_confirm":
        kb = [
            [InlineKeyboardButton("✅ بله، بساز", callback_data="link_create_yes")],
            [InlineKeyboardButton("❌ خیر، انصراف", callback_data="link_main")]
        ]
        return await query.edit_message_text(
            "آیا مطمئنی می‌خوای یک لینک جدید (دائمی) بسازی؟\n\nلینک قبلی همچنان فعال می‌مونه.",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    if data == "link_create_yes":
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(chat_id)
            store_link(link_obj.invite_link, {"type": "permanent"})
            text = f"✅ لینک جدید ساخته شد:\n{link_obj.invite_link}"
        except Exception:
            link = await context.bot.export_chat_invite_link(chat_id)
            store_link(link, {"type": "fallback"})
            text = f"✅ لینک جدید ساخته شد:\n{link}"

        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]]
        return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    # ========= ساخت لینک محدود (پرسش تعداد) =========
    if data == "link_temp_ask":
        kb = [
            [
                InlineKeyboardButton("👥 1 نفر", callback_data="link_temp_1"),
                InlineKeyboardButton("👥 5 نفر", callback_data="link_temp_5"),
                InlineKeyboardButton("👥 10 نفر", callback_data="link_temp_10")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]
        ]
        text = "چند نفر مجاز به استفاده از لینک باشند؟"
        return await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    # ========= ساخت لینک محدود بر اساس انتخاب =========
    if data.startswith("link_temp_"):
        limit = int(data.split("_")[-1])
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(
                chat_id,
                expire_date=datetime.utcnow() + timedelta(hours=24),
                member_limit=limit
            )
            store_link(link_obj.invite_link, {"type": "temp", "limit": limit, "expire": "24h"})
            text = f"🕒 لینک موقت ساخته شد:\n{link_obj.invite_link}\n\n⏳ اعتبار: ۲۴ ساعت\n👥 محدودیت: {limit} نفر"
        except Exception as e:
            text = f"⚠️ خطا در ساخت لینک موقت:\n<code>{e}</code>"

        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]]
        return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    # ========= ارسال به پیوی =========
    if data == "link_send":
        inv = group.get("invite")
        if not inv or not inv.get("link"):
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                store_link(link, {"type": "default"})
            except Exception as e:
                return await query.edit_message_text(
                    f"⚠️ ربات باید ادمین باشد تا لینک را بگیرد.\n\n<code>{e}</code>",
                    parse_mode="HTML"
                )
        else:
            link = inv["link"]

        try:
            await context.bot.send_message(user.id, f"🔗 لینک گروه:\n{link}")
            text = "✅ لینک به پیوی شما ارسال شد."
        except:
            text = "⚠️ ابتدا به ربات پیام بده تا بتواند برایت بفرستد."

        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]]
        return await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    # ========= راهنما =========
    if data == "link_help":
        text = (
            "📘 <b>راهنمای لینک‌ها</b>\n\n"
            "• ساخت لینک جدید فقط برای مدیران مجاز است.\n"
            "• لینک موقت پس از ۲۴ ساعت یا تعداد مشخص منقضی می‌شود.\n"
            "• برای ارسال به پیوی، ابتدا باید به ربات پیام دهید."
        )
        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]]
        return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    # ========= بازگشت به منوی اصلی =========
    if data == "link_main":
        kb = [
            [InlineKeyboardButton("📄 نمایش لینک", callback_data="link_show")],
            [InlineKeyboardButton("🔁 ساخت لینک جدید", callback_data="link_create_confirm")],
            [InlineKeyboardButton("🧾 ساخت لینک محدود", callback_data="link_temp_ask")],
            [InlineKeyboardButton("✉️ ارسال به پیوی", callback_data="link_send")],
            [InlineKeyboardButton("📚 راهنما", callback_data="link_help")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        text = "🔗 <b>پنل مدیریت لینک گروه</b>\n\nاز گزینه‌های زیر استفاده کن 👇"
        return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    # ========= بستن =========
    if data == "link_close":
        return await query.edit_message_text("❌ پنل بسته شد.")
