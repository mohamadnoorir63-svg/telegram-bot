import re
import os
import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]  # آیدی شما

# ================================
# کوکی اینستاگرام (فرمت Netscape)
# ================================
COOKIE_FILE = "insta_cookie.txt"
INSTAGRAM_COOKIES = r"""
.instagram.com	TRUE	/	TRUE	1799701606	csrftoken	--d8oLwWArIVOTuxrKibqa
.instagram.com	TRUE	/	TRUE	1799687399	datr	47Q1aZceuWl7nLkf_Uzh_kVW
.instagram.com	TRUE	/	TRUE	1796663399	ig_did	615B02DC-3966-40ED-864D-5EDD6E7C4EA3
.instagram.com	TRUE	/	TRUE	1799687399	mid	aTW04wABAAHoKpxsaAJbAfLsgVU3
.instagram.com	TRUE	/	TRUE	1765732343	dpr	2
.instagram.com	TRUE	/	TRUE	1772917606	ds_user_id	79160628834
.instagram.com	TRUE	/	TRUE	1796663585	sessionid	79160628834%3AtMYF1zDBj9tXx3%3A7%3AAYhX_MD6k4rrVPUaIBvVhJLqxdAzNqJ0SkLDHb-ymQ
.instagram.com	TRUE	/	TRUE	1765746400	wd	360x683
.instagram.com	TRUE	/	TRUE	0	rur	"FRC\05479160628834\0541796677606:01feeadcb720f15c682519c2475d06626b55e5e1646ce3648355ab004152c377c46ba081"
"""

os.makedirs("downloads", exist_ok=True)
with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(INSTAGRAM_COOKIES.strip())

# ================================
# regex گرفتن لینک
# ================================
URL_RE = re.compile(r"(https?://[^\s]+)")

# ================================
# تابع چک مدیر بودن
# ================================
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return True
    if user.id in SUDO_USERS:
        return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
    except:
        return False

    return user.id in admin_ids

# ================================
# دکمه افزودن ربات (پیوی)
# ================================
def get_add_btn(chat_type):
    if chat_type == "private":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
        ])
    return None

# ================================
# هندلر اصلی اینستاگرام
# ================================
async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    m = URL_RE.search(text)
    if not m:
        return

    url = m.group(1)
    if "instagram.com" not in url:
        return

    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "noplaylist": True,
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            await msg.edit_text("⬇ در حال ارسال فایل‌ها...")

            files_to_send = []

            # چندتایی یا تک پست
            if "entries" in info:
                files_to_send = [ydl.prepare_filename(entry) for entry in info["entries"]]
            else:
                files_to_send = [ydl.prepare_filename(info)]

            for file in files_to_send:
                ext = file.split(".")[-1].lower()
                if ext in ["mp4", "mov", "webm"]:
                    await update.message.reply_video(video=open(file, "rb"),
                                                     reply_markup=get_add_btn(update.effective_chat.type))
                elif ext in ["jpg", "jpeg", "png", "webp"]:
                    await update.message.reply_photo(photo=open(file, "rb"),
                                                    reply_markup=get_add_btn(update.effective_chat.type))
                else:
                    await update.message.reply_document(document=open(file, "rb"),
                                                       reply_markup=get_add_btn(update.effective_chat.type))

                os.remove(file)  # حذف فایل بعد از ارسال

            await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ نتوانستم دانلود کنم.\n⚠️ خطا: {e}")
