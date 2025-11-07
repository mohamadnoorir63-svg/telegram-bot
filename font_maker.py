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
    fonts = generate_english_fonts(name) if is_english else generate_persian_fonts(name)

    await update.message.reply_text(
        fonts[0]["text"],
        parse_mode="HTML",
        reply_markup=fonts[0]["keyboard"]
    )

    context.user_data["font_pages"] = fonts
    context.user_data["font_index"] = 0
    return ConversationHandler.END

# ======================= 🎭 تولید فونت فارسی (جدید، زیبا و عشقی) =======================
def generate_persian_fonts(name):
    styles = [
        f"• {name} •", f"✦ {name} ✦", f"⋆ {name} ⋆", f"✿ {name} ✿",
        f"☾ {name} ☽", f"♡ {name} ♡", f"❖ {name} ❖", f"⟡ {name} ⟡",
        f"⋆❀ {name} ❀⋆", f"ღ {name} ღ", f"❋ {name} ❋", f"✧ {name} ✧",
        f"⋆⸙ {name} ⸙⋆", f"⊰ {name} ⊱", f"❦ {name} ❦", f"⋆✦ {name} ✦⋆",
        f"⚜ {name} ⚜", f"⋆✶ {name} ✶⋆", f"˗ˏˋ {name} ˎˊ˗", f"⟡✧ {name} ✧⟡",
        f"∘₊✧ {name} ✧₊∘", f"⋆｡°✩ {name} ✩°｡⋆", f"𓆩♡𓆪 {name} 𓆩♡𓆪",
        f"༺ {name} ༻", f"꧁༒☬ {name} ☬༒꧂", f"♡﹏﹏﹏ {name} ﹏﹏﹏♡",
        f"╭──❀──╮ {name} ╰──❀──╯", f"♡•́‿•̀♡ {name} ♡•́‿•̀♡",
        f"💞 {name} 💞", f"❣️ {name} ❣️", f"꧁༺♥༻꧂ {name} ꧁༺♥༻꧂",
        f"💋 {name} 💋", f"✿♡✿ {name} ✿♡✿", f"🌸 {name} 🌸",
        f"⋆˙⟡♡⟡˙⋆ {name} ⋆˙⟡♡⟡˙⋆", f"╭────────╮\n{name}\n╰────────╯",
        f"✧˚༺ {name} ༻˚✧", f"♡₊˚ {name} ˚₊♡", f"❀❀ {name} ❀❀",
        f"⟡♡ {name} ♡⟡", f"✿•₊˚ {name} ˚₊•✿", f"⊹✿⊹ {name} ⊹✿⊹"
    ]
    return make_pages(name, styles)

# ======================= ✨ تولید فونت انگلیسی چندصفحه‌ای و جذاب =======================
def generate_english_fonts(name):
    frames = [
        lambda t: f"• {t} •", lambda t: f"✦ {t} ✦", lambda t: f"⋆ {t} ⋆", lambda t: f"✿ {t} ✿",
        lambda t: f"♡ {t} ♡", lambda t: f"☾ {t} ☽", lambda t: f"❖ {t} ❖", lambda t: f"⟡ {t} ⟡",
        lambda t: f"❋ {t} ❋", lambda t: f"⊰ {t} ⊱", lambda t: f"˗ˏˋ {t} ˎˊ˗", lambda t: f"✧ {t} ✧",
        lambda t: f"⋆｡° {t} °｡⋆", lambda t: f"⋆✦ {t} ✦⋆", lambda t: f"꧁༺ {t} ༻꧂",
        lambda t: f"♡﹏﹏﹏ {t} ﹏﹏﹏♡", lambda t: f"✿♡✿ {t} ✿♡✿", lambda t: f"꧁༒☬ {t} ☬༒꧂",
        lambda t: f"✧˚༺ {t} ༻˚✧", lambda t: f"💫 {t} 💫", lambda t: f"⋆˙⟡♡⟡˙⋆ {t} ⋆˙⟡♡⟡˙⋆", lambda t: f"⟡✧ {t} ✧⟡",
        lambda t: f"⚡ {t} ⚡", lambda t: f"🔥 {t} 🔥", lambda t: f"🌟 {t} 🌟", lambda t: f"💥 {t} 💥",
        lambda t: f"✨ {t} ✨", lambda t: f"🎯 {t} 🎯", lambda t: f"🌀 {t} 🌀", lambda t: f"♛ {t} ♛",
        lambda t: f"♚ {t} ♚", lambda t: f"❂ {t} ❂", lambda t: f"❃ {t} ❃", lambda t: f"✪ {t} ✪"
    ]
    fonts = [frame(name) for frame in frames]
    return make_pages(name, fonts)

# ======================= 📄 تقسیم فونت‌ها به صفحات =======================
def make_pages(name, all_fonts, page_size=25):
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

# ======================= 💎 فونت‌های لاکچری پرمیوم (انگلیسی و فارسی) =======================
def generate_premium_fonts(name):
    """فونت‌های ترکیبی خاص و لاکچری برای حالت ویژه"""
    return make_pages(name, get_luxury_styles(name))

def get_luxury_styles(name):
    # فونت انگلیسی خاص با چند نوع تبدیل حروف
    fancy_sets = [
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃"
        ),
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷"
        ),
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"
        ),
    ]

    luxury = []

    # نسخه‌های انگلیسی لاکچری
    for trans in fancy_sets:
        styled = name.translate(trans)
        luxury.extend([
            f"꧁༺ {styled} ༻꧂",
            f"✦ {styled} ✦",
            f"⋆⟡ {styled} ⟡⋆",
            f"♡ {styled} ♡",
            f"❀ {styled} ❀",
            f"╭──✿──╮\n{styled}\n╰──✿──╯",
            f"⟡✧ {styled} ✧⟡",
            f"𓆩♡𓆪 {styled} 𓆩♡𓆪",
            f"꧁💎 {styled} 💎꧂",
            f"✧･ﾟ: *✧･ﾟ:* {styled} *:･ﾟ✧*:･ﾟ✧"
        ])

    # نسخه‌های فارسی لاکچری
    persian_styles = [
        f"꧁༺💖༻꧂ {name} ꧁༺💖༻꧂",
        f"╭❀╮ {name} ╭❀╮",
        f"🌸 {name} 🌸", f"❁ {name} ❁", f"💞 {name} 💞",
        f"♡ꕥ♡ {name} ♡ꕥ♡",
        f"꧁༒☬ {name} ☬༒꧂",
        f"ღ꧁ {name} ꧂ღ",
        f"✿✿✿ {name} ✿✿✿",
        f"༺♡༻ {name} ༺♡༻",
        f"❀⟡ {name} ⟡❀",
        f"⋆༺❀༻⋆ {name} ⋆༺❀༻⋆"
    ]

    luxury.extend(persian_styles)
    return make_pages(name, luxury)
