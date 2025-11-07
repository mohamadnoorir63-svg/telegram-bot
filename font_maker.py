import asyncio
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1  # مرحله‌ی پرسیدن اسم

# 🎨 تابع اصلی تولید فونت
async def font_maker(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

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

    if text.strip() == "فونت":
        await update.message.reply_text("🌸 چه اسمی رو برات فونت کنم؟")
        return ASK_NAME

    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END

async def receive_font_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❗ لطفاً یه اسم بنویس تا فونت بسازم.")
        return ASK_NAME
    return await send_fonts(update, context, name)

async def send_fonts(update, context, name):
    is_english = bool(re.search(r"[a-zA-Z]", name))
    fonts = generate_english_fonts(name) if is_english else generate_persian_fonts(name)

    await update.message.reply_text(
        fonts[0]["text"],
        parse_mode="HTML",
        reply_markup=fonts[0]["keyboard"]
    )

    context.user_data["font_pages"] = fonts
    context.user_data["font_index"] = 0
    return ConversationHandler.END

# ======================= 🎭 فونت فارسی مرتب و جذاب =======================
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
    return all_fonts

# ---------- مثال استفاده ----------
name = "محمد"  # یا اسم انگلیسی مثل "Mohammad"
all_fonts = generate_all_fancy_fonts(name)

# چاپ 50 فونت اول
for i, f in enumerate(all_fonts[:50], 1):
    print(f"{i}. {f}") 
