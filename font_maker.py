import asyncio
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1

# ======================= 🎨 تابع اصلی تولید فونت =======================
async def font_maker(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:
        msg = await update.message.reply_text("✨ لطفاً برای ساخت فونت، به پیوی ربات مراجعه کنید 🙏")
        await asyncio.sleep(6)
        try:
            await msg.delete()
            await update.message.delete()
        except Exception as e:
            if "message to be replied not found" not in str(e).lower():
                print(f"⚠️ خطا در حذف پیام: {e}")
        return ConversationHandler.END

    if text.strip() == "فونت":
        await update.message.reply_text("🌸 چه اسمی رو برات فونت کنم؟")
        return ASK_NAME

    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END

# ======================= 🌸 دریافت اسم کاربر =======================
async def receive_font_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❗ لطفاً یه اسم بنویس تا فونت بسازم.")
        return ASK_NAME
    return await send_fonts(update, context, name)

# ======================= 💎 ارسال فونت‌ها =======================
async def send_fonts(update, context, name):
    fonts = generate_rainbow_fonts(name)

    await update.message.reply_text(
        fonts[0]["text"],
        parse_mode="HTML",
        reply_markup=fonts[0]["keyboard"]
    )
    context.user_data["font_pages"] = fonts
    context.user_data["font_index"] = 0
    return ConversationHandler.END

# ======================= 🎭 تولید فونت رنگین‌کمانی و زیبا =======================
def generate_rainbow_fonts(name):
    colors = ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "⬛", "⬜"]  # می‌توان شکل‌های رنگی اضافه کرد

    def rainbow_text(text):
        return "".join(f"{random.choice(colors)}{c}" for c in text)

    # ---------------- فونت‌های فارسی زیبا ----------------
    farsi_styles = [
        "{}َِــَِ{}", "{}ۘـ{}ۘـ{}", "{}ـــ{}ـــ{}", "{}ـ﹏ـ{}ـ﹏ـ{}", "{}ـ෴ِْ{}ـ෴ِْ{}",
        "{}ـًٍʘًٍʘـ{}ـًٍʘًٍʘـ{}", "{}⋆✧{}✧⋆{}", "✿{}✿{}", "♡{}♡{}", "{}༺{}༻{}",
        "نَِ{}و", "نـ{}مـ{}", "نـ{}وـ{}", "نـ{}هـ", "نُ{}وٌ", "نِ{}وِ", "نْ{}وْ"
    ]
    farsi_fonts = [style.format(*([name]*style.count("{}"))) for style in farsi_styles]
    farsi_fonts = [rainbow_text(f) for f in farsi_fonts]

    # ---------------- فونت انگلیسی با نماد ----------------
    english_translations = [
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝑾𝑿𝒀𝒁abcdefghijklmnopqrstuvwxyz"
        ),
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃"
        ),
    ]
    symbols = ["•", "✦", "⋆", "✿", "♡", "☾", "❖", "⟡", "❋"]

    english_fonts = []
    for trans in english_translations:
        translated = name.translate(trans)
        for sym in symbols:
            english_fonts.append(rainbow_text(f"{sym}{translated}{sym}"))
            english_fonts.append(rainbow_text(f"{translated}{sym}"))
        english_fonts.append(rainbow_text(translated))

    # ---------------- فونت‌های Unicode خاص ----------------
    spaced_flag = " ".join(c for c in name.upper() if c.isalpha())
    english_fonts.append(rainbow_text(spaced_flag))  # 🇹 🇪 🇸 🇹 شبیه سازی با حروف کاربر

    en_circle = "".join({
        "A":"Ⓐ","B":"Ⓑ","C":"Ⓒ","D":"Ⓓ","E":"Ⓔ","F":"Ⓕ","G":"Ⓖ","H":"Ⓗ","I":"Ⓘ","J":"Ⓙ",
        "K":"Ⓚ","L":"Ⓛ","M":"Ⓜ","N":"Ⓝ","O":"Ⓞ","P":"Ⓟ","Q":"Ⓠ","R":"Ⓡ","S":"Ⓢ","T":"Ⓣ",
        "U":"Ⓤ","V":"Ⓥ","W":"Ⓦ","X":"Ⓧ","Y":"Ⓨ","Z":"Ⓩ"
    }.get(c,c) for c in name.upper())
    english_fonts.append(rainbow_text(en_circle))

    en_square = "".join({
        "A":"🄰","B":"🄱","C":"🄲","D":"🄳","E":"🄴","F":"🄵","G":"🄶","H":"🄷","I":"🄸","J":"🄹",
        "K":"🄺","L":"🄻","M":"🄼","N":"🄽","O":"🄾","P":"🄿","Q":"🅀","R":"🅁","S":"🅂","T":"🅃",
        "U":"🅄","V":"🅅","W":"🅆","X":"🅇","Y":"🅈","Z":"🅉"
    }.get(c,c) for c in name.upper())
    english_fonts.append(rainbow_text(en_square))

    all_fonts = farsi_fonts + english_fonts

    return make_pages(name, all_fonts, page_size=10, max_pages=10)

# ======================= 📄 تقسیم فونت‌ها به صفحات =======================
def make_pages(name, all_fonts, page_size=10, max_pages=10):
    pages = []
    chunks = [all_fonts[i:i + page_size] for i in range(0, len(all_fonts), page_size)]
    if len(chunks) > max_pages:
        chunks = chunks[:max_pages]

    for idx, chunk in enumerate(chunks):
        text = f"<b>↻ {name} ⇦</b>\n:• لیست فونت های پیشنهادی :\n"
        for i, style in enumerate(chunk, start=1):
            text += f"{i}- {style}\n"

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
