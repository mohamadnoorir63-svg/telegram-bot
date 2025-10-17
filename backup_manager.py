# ======================= ☁️ NOORI Secure QR Backup v11.5 (AutoLimit Edition) =======================
import io, shutil, base64, qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os, zipfile, asyncio
from telegram import Update, InputFile
from telegram.ext import ContextTypes

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

IMPORTANT_FILES = [
    "memory.json", "group_data.json", "jokes.json",
    "fortunes.json", "warnings.json", "aliases.json"
]

def _should_include_in_backup(path: str) -> bool:
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", "backups"]
    lowered = path.lower()
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

def create_zip_backup():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    zip_path = os.path.join(BACKUP_DIR, filename)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                full_path = os.path.join(root, file)
                if _should_include_in_backup(full_path):
                    arcname = os.path.relpath(full_path, ".")
                    zipf.write(full_path, arcname=arcname)
    return zip_path, now

# 🧠 QR هوشمند با محدودکننده خودکار
def generate_qr_image(text, timestamp):
    safe_text = text
    version = 10
    while True:
        try:
            qr = qrcode.QRCode(
                version=version,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2
            )
            qr.add_data(safe_text)
            qr.make(fit=True)
            break
        except Exception as e:
            # اگر طول متن زیاد بود → نصفش می‌کنیم تا در QR جا بشه
            print(f"[QR AUTO-LIMIT] version={version} failed ({len(safe_text)} chars) → reducing")
            safe_text = safe_text[: int(len(safe_text) * 0.8)]
            if version > 1:
                version -= 1
            if len(safe_text) < 100:
                raise Exception("❌ Text too long for QR even after reduction!")

    qr_img = qr.make_image(fill_color="#0044cc", back_color="white").convert("RGB")

    # آیکون مرکزی
    shield = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shield)
    draw.ellipse((0, 0, 120, 120), fill="#0044cc")
    draw.polygon([(60, 25), (95, 50), (85, 95), (35, 95), (25, 50)], fill="white")
    qr_w, qr_h = qr_img.size
    shield = shield.resize((qr_w // 4, qr_h // 4))
    qr_img.paste(shield, ((qr_w - shield.size[0]) // 2, (qr_h - shield.size[1]) // 2), mask=shield)

    canvas = Image.new("RGB", (qr_w, qr_h + 80), "white")
    canvas.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    label = f"Backup — {timestamp}"
    w, h = draw.textsize(label, font=font)
    draw.text(((qr_w - w) // 2, qr_h + 25), label, fill="#0044cc", font=font)

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return output

# 💾 بک‌آپ دستی
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    zip_path, timestamp = create_zip_backup()
    with open(zip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    qr_img = generate_qr_image(encoded, timestamp)

    await update.message.reply_photo(photo=qr_img, caption=f"☁️ بک‌آپ ساخته شد ✅\n🕓 {timestamp}")
    await update.message.reply_document(InputFile(zip_path))
    os.remove(zip_path)

# ☁️ بک‌آپ ابری
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    zip_path, timestamp = create_zip_backup()
    with open(zip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    qr_img = generate_qr_image(encoded, timestamp)

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=qr_img, caption=f"☁️ Cloud Backup — {timestamp}")
    await context.bot.send_document(chat_id=ADMIN_ID, document=InputFile(zip_path))
    os.remove(zip_path)

# ♻️ بازیابی
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه بازیابی کنه!")
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("📎 فایل ZIP بک‌آپ را ریپلای کن و بعد دستور /restore بزن.")

    file = await update.message.reply_to_message.document.get_file()
    path = os.path.join(BACKUP_DIR, "restore_temp.zip")
    await file.download_to_drive(path)

    msg = await update.message.reply_text("♻️ شروع بازیابی...\n0% [▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒]")
    restore_dir = "restore_temp"
    if os.path.exists(restore_dir):
        shutil.rmtree(restore_dir)
    os.makedirs(restore_dir, exist_ok=True)

    with zipfile.ZipFile(path, "r") as zip_ref:
        files = zip_ref.namelist()
        total = len(files)
        done = 0
        for file in files:
            zip_ref.extract(file, restore_dir)
            done += 1
            percent = int(done / total * 100)
            bars = int(percent / 5)
            progress_bar = "█" * bars + "▒" * (20 - bars)
            await msg.edit_text(f"♻️ بازیابی {percent}% [{progress_bar}]")
            await asyncio.sleep(0.2)

    moved = 0
    for f in IMPORTANT_FILES:
        src = os.path.join(restore_dir, f)
        if os.path.exists(src):
            shutil.move(src, f)
            moved += 1

    shutil.rmtree(restore_dir)
    os.remove(path)
    await msg.edit_text(f"✅ بازیابی کامل شد!\n📦 {moved} فایل بازگردانی گردید.\n🤖 سیستم آماده است.")

# 🕓 بک‌آپ خودکار هر ۶ ساعت
async def auto_backup(bot):
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    while True:
        try:
            zip_path, timestamp = create_zip_backup()
            with open(zip_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            qr_img = generate_qr_image(encoded, timestamp)
            await bot.send_photo(chat_id=ADMIN_ID, photo=qr_img, caption=f"🤖 Auto Backup — {timestamp}")
            await bot.send_document(chat_id=ADMIN_ID, document=InputFile(zip_path))
            os.remove(zip_path)
            print(f"[AUTO BACKUP] {timestamp} sent ✅")
        except Exception as e:
            print(f"[AUTO BACKUP ERROR] {e}")
        await asyncio.sleep(21600)
