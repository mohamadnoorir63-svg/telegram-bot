import asyncio
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1  # مرحله‌ی پرسیدن اسم

# 🎨 تابع اصلی تولید فونت
async def font_maker(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    # ✅ جلوگیری از فونت در گروه‌ها
    if chat_type in ["group", "supergroup"]:
        msg = await update.message.reply_text("✨ برای ساخت فونت، لطفاً به پیوی ربات مراجعه کنید 🙏")
        await asyncio.sleep(6)
        try:
            await msg.delete()
            await update.message.delete()
        except Exception as e:
            if "message to be replied not found" not in str(e).lower():
                print(f"⚠️ خطا در حذف پیام: {e}")
        return ConversationHandler.END

    # اگر فقط نوشته "فونت" → سوال بپرس
    if text.strip() == "فونت":
        await update.message.reply_text("🌸 چه اسمی رو برات فونت کنم؟")
        return ASK_NAME

    # اگر نوشت "فونت <اسم>"
    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END

# 🌸 مرحله‌ی بعد: کاربر اسم رو وارد کرد
async def receive_font_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❗ لطفاً یه اسم بنویس تا فونت بسازم.")
        return ASK_NAME
    return await send_fonts(update, context, name)

# 💎 تابع ارسال فونت‌ها
async def send_fonts(update, context, name):
    is_english = bool(re.search(r"[a-zA-Z]", name))
    fonts = generate_all_fancy_fonts(name)  # نسخه کامل fancy که هم فارسی هم انگلیسی رو پشتیبانی می‌کنه

    await update.message.reply_text(
        fonts[0]["text"],
        parse_mode="HTML",
        reply_markup=fonts[0]["keyboard"]
    )
    context.user_data["font_pages"] = fonts
    context.user_data["font_index"] = 0
    return ConversationHandler.END

# ======================= 🎭 تولید فونت فارسی و انگلیسی Fancy =======================
def generate_all_fancy_fonts(name):
    """
    تولید فونت‌های تزئینی برای اسم فارسی یا انگلیسی
    شامل فونت‌های فارسی و انگلیسی Unicode با نمادها
    """
    # ---------------- فونت‌های فارسی ----------------
    fancy_farsi_styles = [
        "{}َِــَِ{}َِ",
        "ۘۘ{}ـ ۘۘ{}ـ ۘۘ{}",
        "{}ـــ{}ـــ{}ّ",
        "{}ـ﹏ـ{}ـ﹏ـ{}",
        "{}ـ෴ِْ{}ـ෴ِْ{}",
        "{}ـًٍʘًٍʘـ{}ـًٍʘًٍʘـ{}ََ",
        "{}ـ•̛{}•̛ـ{}",
        "{}⋆✧{}✧⋆{}",
        "✿{}✿{}✿{}",
        "♡{}♡{}♡{}",
        "⟡{}⟡{}⟡{}",
        "{}༺{}༻{}",
        "{}ღ{}ღ{}",
        "{}❖{}❖{}",
        "⚡{}⚡{}⚡{}",
        "🔥{}🔥{}🔥{}",
        "🌸{}🌸{}🌸{}",
        "✦{}✦{}✦{}",
        "{}⋆{}⋆{}",
        "{}✿{}✿{}",
        "{}•{}•{}",
        "✧{}✧{}✧",
        "{}⸙{}⸙{}",
        "✪{}✪{}✪",
        "{}✺{}✺{}",
        "{}✰{}✰{}",
        "{}❀{}❀{}",
        "❣️{}❣️{}",
        "{}❋{}❋{}",
        "{}⸼{}⸼{}",
        "{}☾{}☽{}",
        "{}☆{}☆{}",
    ]

    farsi_fonts = []
    for style in fancy_farsi_styles:
        count = style.count("{}")
        farsi_fonts.append(style.format(*([name]*count)))

    # ---------------- فونت‌های انگلیسی ----------------
    english_translations = [
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙abcdefghijklmnopqrstuvwxyz"
        ),
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃"
        ),
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁𝒂𝒃𝒄𝒅𝒆𝒇𝒈𝒉𝒊𝒋𝒌𝒍𝒎𝒏𝒐𝒑𝒒𝒓𝒔𝒕𝒖𝒗𝒘𝒙𝒚𝒛"
        ),
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷"
        ),
    ]

    symbols = ["•", "✦", "⋆", "✿", "♡", "☾", "❖", "⟡", "❋", "⊰", "✧", "⚡", "🔥", "💫", "✨", "☆", "✪", "✰", "❀", "❣️"]

    english_fonts = []
    for trans in english_translations:
        translated = name.translate(trans)
        for sym in symbols:
            english_fonts.append(f"{sym} {translated} {sym}")
            english_fonts.append(f"{translated} {sym}")
            english_fonts.append(f"{sym}{translated}{sym}")
            english_fonts.append(f"{translated}")

    # ---------------- ترکیب همه فونت‌ها ----------------
    all_fonts = farsi_fonts + english_fonts

    # ---------------- تقسیم فونت‌ها به صفحات ----------------
    return make_pages(name, all_fonts)

# ======================= 📄 تقسیم فونت‌ها به صفحات =======================
def make_pages(name, all_fonts, page_size=10):
    pages = []
    chunks = [all_fonts[i:i + page_size] for i in range(0, len(all_fonts), page_size)]

    for idx, chunk in enumerate(chunks):
        text = f"<b>🎨 فونت‌های خاص و تزئینی برای:</b> <i>{name}</i>\n\n"
        for i, style in enumerate(chunk, start=1):
            text += f"{i}. <code>{style}</code>\n"
        text += f"\n📄 صفحه {idx + 1} از {len(chunks)}"

        nav_buttons = []
        if idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"prev_font:{idx - 1}"))
        if idx < len(chunks) - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"next_font:{idx + 1}"))

        pages.append({
            "text": text,
            "keyboard": InlineKeyboardMarkup([
                nav_buttons,
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="feature_back")]
            ])
        })
    return pages

# ======================= 🔁 کنترل صفحات فونت =======================
async def next_font(update, context):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":")[1])
    fonts = context.user_data.get("font_pages", [])
    if 0 <= index < len(fonts):
        await query.edit_message_text(
            fonts[index]["text"],
            parse_mode="HTML",
            reply_markup=fonts[index]["keyboard"]
        )

async def prev_font(update, context):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":")[1])
    fonts = context.user_data.get("font_pages", [])
    if 0 <= index < len(fonts):
        await query.edit_message_text(
            fonts[index]["text"],
            parse_mode="HTML",
            reply_markup=fonts[index]["keyboard"]
        )
