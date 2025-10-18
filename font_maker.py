# ======================= 💎 Khenqol FontMaster 30.0 — Persian & English Pro Edition =======================
import random
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# 🎨 تابع اصلی تولید فونت
async def font_maker(update, context):
    text = update.message.text.strip()
    if not text.startswith("فونت "):
        return False

    name = text.replace("فونت", "").strip()
    if not name:
        return await update.message.reply_text("🖋 بعد از «فونت»، نام خودت رو بنویس تا فونت‌هات ساخته بشن.")

    # تشخیص فارسی یا انگلیسی
    is_english = bool(re.search(r"[a-zA-Z]", name))
    fonts = generate_english_fonts(name) if is_english else generate_persian_fonts(name)

    # اولین دسته فونت‌ها
    await update.message.reply_text(fonts[0]["text"], parse_mode="HTML", reply_markup=fonts[0]["keyboard"])
    context.user_data["font_pages"] = fonts  # ذخیره برای صفحه‌های بعدی
    context.user_data["font_index"] = 0
    return True


# ======================= 🎭 تولید فونت فارسی =======================
def generate_persian_fonts(name):
    styles = [
        f"─═〘 {name} 〙═─",
        f"⋆⁺₊⋆ {name} ⋆₊⁺⋆",
        f"•—– {name} –—•",
        f"╭━━━ {name} ━━━╮",
        f"═━═ {name} ═━═",
        f"⋆✦ {name} ✦⋆",
        f"⋆═══ {name} ═══⋆",
        f"✦━─━─━ {name} ━─━─━✦",
        f"⋆⸙̩̩͙⊱ {name} ⊰⸙̩̩͙⋆",
        f"✦⋆ {name} ⋆✦",
        f"═━━═ {name} ═━━═",
        f"⋆╭─ {name} ─╮⋆",
        f"⋆╰─ {name} ─╯⋆",
        f"╰═─ {name} ─═╯",
        f"⋆━── {name} ──━⋆",
        f"•⟡•° {name} °•⟡•",
        f"⋆⁺ {name} ⁺⋆",
        f"◈───────◈ {name} ◈───────◈",
        f"╔═══ {name} ═══╗",
        f"⋆━⋆━ {name} ━⋆━⋆",
        f"⋆──═ {name} ═──⋆",
        f"━⋆━━ {name} ━━⋆━",
        f"⋆═──═ {name} ═──═⋆",
        f"┈┈✦ {name} ✦┈┈",
        f"╭─────────────╮\n{name}\n╰─────────────╯",
        f"⋆═───══ {name} ═══───═⋆",
        f"╔═━━═ {name} ═━━═╗",
        f"⋆━╬━ {name} ━╬━⋆",
        f"⋆═══╬═══ {name} ═══╬═══⋆",
        f"═⋆═╬═ {name} ╬═⋆═",
        f"⋆══╬══ {name} ══╬══⋆",
        f"⋆═══⋆═══ {name} ═══⋆═══⋆",
        f"╭───❖───╮\n{name}\n╰───❖───╯",
    ]

    # هر صفحه شامل 30 فونت است
    return make_pages(name, styles)


# ======================= ✨ تولید فونت انگلیسی =======================
def generate_english_fonts(name):
    fancy_trans = [
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘵𝘶𝘷𝘄𝘅𝘆𝘇"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷"),
    ]

    frames = [
        lambda t: f"═── {t} ──═",
        lambda t: f"⋆━── {t} ──━⋆",
        lambda t: f"⋆✦ {t} ✦⋆",
        lambda t: f"⟪ {t} ⟫",
        lambda t: f"═━━═ {t} ═━━═",
        lambda t: f"⋆═══ {t} ═══⋆",
        lambda t: f"⌜ {t} ⌟",
        lambda t: f"• {t} •",
        lambda t: f"╭── {t} ──╮",
        lambda t: f"╰── {t} ──╯",
        lambda t: f"《 {t} 》",
        lambda t: f"〈 {t} 〉",
    ]

    fonts = []
    for tr in fancy_trans:
        for frame in frames:
            fonts.append(frame(name.translate(tr)))

    return make_pages(name, fonts)


# ======================= 📄 تقسیم فونت‌ها به صفحات =======================
def make_pages(name, all_fonts, page_size=30):
    pages = []
    chunks = [all_fonts[i:i + page_size] for i in range(0, len(all_fonts), page_size)]

    for idx, chunk in enumerate(chunks):
        text = f"<b>🎨 فونت‌های خاص برای:</b> <i>{name}</i>\n\n"
        for i, style in enumerate(chunk, start=1):
            text += f"{i}. <code>{style}</code>\n\n"
        text += f"📄 صفحه {idx + 1} از {len(chunks)}"

        buttons = []
        if idx > 0:
            buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"prev_font:{idx - 1}"))
        if idx < len(chunks) - 1:
            buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"next_font:{idx + 1}"))

        nav_buttons = [buttons] if buttons else []
        nav_buttons.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="feature_back")])

        pages.append({
            "text": text,
            "keyboard": InlineKeyboardMarkup(nav_buttons)
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
