import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1


# ======================= 🎨 شروع کار =======================
async def font_maker(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    # جلوگیری از استفاده داخل گروه
    if chat_type in ["group", "supergroup"]:
        msg = await update.message.reply_text("✨ لطفاً برای ساخت فونت، به پیوی ربات مراجعه کنید 🙏")
        return ConversationHandler.END

    if text == "فونت":
        await update.message.reply_text("🌸 چه اسمی رو برات فونت کنم؟")
        return ASK_NAME

    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END


# ======================= 🌸 دریافت اسم =======================
async def receive_font_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    return await send_fonts(update, context, name)


# ======================= 💎 ساخت و ارسال فونت =======================
async def send_fonts(update, context, name):
    fonts = generate_fonts(name)

    # متن معرفی
    intro = f"🌺 فونت‌های ساخته‌شده برای «{name}»:\n\n"
    await update.message.reply_text(intro)

    keyboard = []

    # فقط 20 فونت ارسال می‌کنیم (قابل تغییر)
    for style in fonts[:20]:
        # دکمه‌ای که متنش همان فونت است
        keyboard.append([InlineKeyboardButton(text=style, callback_data="copy_font")])

    await update.message.reply_text(
        "روی هر فونت بزنید تا قابل کپی شود 🌸",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ConversationHandler.END


# ======================= 🎭 تولید فونت =======================
def generate_fonts(name):
    pre_groups = [
        ["𓄂", "𓆃", "𓃬", "𓋥", "𓄼", "𓂀", "𓅓"],
        ["ꪰ", "ꪴ", "𝄠", "𝅔", "꧁", "꧂", "ꕥ"],
        ["⚝", "☬", "☾", "☽", "★", "✦", "✧"]
    ]

    post_groups = [
        ["✿", "♡", "❖", "░", "❋", "☯", "❂"],
        ["✧", "✦", "❂", "★", "✺", "✶", "✸"],
        ["⋆", "⟡", "❋", "•", "✾", "✢", "✤"]
    ]

    unicode_styles = [
        (
            "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"
            "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        ),
        (
            "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉"
            "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )
    ]

    fonts = []

    for _ in range(30):
        pre = "".join(random.choice(g) for g in pre_groups)
        post = "".join(random.choice(g) for g in post_groups)

        style = random.choice(unicode_styles)
        uname = name.translate(str.maketrans(style[1], style[0]))

        fonts.append(f"{pre}{uname}{post}")

    return fonts
