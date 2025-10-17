# ======================= ☁️ NOORI Secure Backup v12.1 (Cloud+ Heroku Edition) =======================
import io, shutil, base64, qrcode, os, zipfile, asyncio, math, time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import ContextTypes

# 📁 مسیر ذخیره بک‌آپ‌ها
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# 📄 فایل‌های مهم برای بازیابی
IMPORTANT_FILES = [
    "memory.json", "group_data.json", "jokes.json",
    "fortunes.json", "warnings.json", "aliases.json"
]

# 🎯 انتخاب فایل‌هایی که در بک‌آپ ذخیره می‌شوند
def _should_include_in_backup(path: str) -> bool:
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", "backups"]
    lowered = path.lower()
    if any(sd in lowered for sd in skip_dirs): return False
    if lowered.endswith(".zip"): return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

# 🧩 ساخت فایل ZIP
def create_zip_backup():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    zip_path = os.path.join(BACKUP_DIR, filename)
    start = time.time()
    count = 0

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                full_path = os.path.join(root, file)
                if _should_include_in_backup(full_path):
                    arcname = os.path.relpath(full_path, ".")
                    zipf.write(full_path, arcname=arcname)
                    count += 1

    duration = round(time.time() - start, 2)
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"[ZIP] Created backup with {count} files in {duration}s ({size_mb:.2f} MB)")
    return zip_path, now, count, size_mb, duration

# ✂️ تقسیم فایل ZIP به پارت‌های کوچکتر
def split_file(filepath, part_size_mb=45):
    parts = []
    part_size = part_size_mb * 1024 * 1024
    filesize = os.path.getsize(filepath)
    total_parts = math.ceil(filesize / part_size)

    with open(filepath, "rb") as f:
        for i in range(total_parts):
            part_name = f"{filepath}.part{i+1:02d}"
            with open(part_name, "wb") as part:
                chunk = f.read(part_size)
                if not chunk:
                    break
                part.write(chunk)
            parts.append(part_name)
    return parts

# 🧠 QR برای امضای بک‌آپ
def generate_qr_image(signature_text, timestamp):
    short_text = signature_text[:400]
    qr = qrcode.QRCode(
        version=5, error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10, border=2
    )
    qr.add_data(short_text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0044cc", back_color="white").convert("RGB")

    # لوگوی نوری
    shield = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shield)
    draw.ellipse((0, 0, 120, 120), fill="#0044cc")
    draw.polygon([(60, 25), (95, 50), (85, 95), (35, 95), (25, 50)], fill="white")

    qr_w, qr_h = qr_img.size
    shield = shield.resize((qr_w // 4, qr_h // 4))
    qr_img.paste(shield, ((qr_w - shield.size[0]) // 2, (qr_h - shield.size[1]) // 2), mask=shield)

    # عنوان پایین
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

# 💾 بک‌آپ دستی کامل
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    msg = await update.message.reply_text("⏳ در حال ساخت بک‌آپ حجیم... لطفاً صبر کنید...")

    zip_path, timestamp, count, size_mb, duration = create_zip_backup()
    parts = split_file(zip_path)
    total_parts = len(parts)

    with open(zip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    qr_img = generate_qr_image(encoded, timestamp)

    await msg.edit_text(f"☁️ بک‌آپ ساخته شد ✅\n"
                        f"📦 فایل‌ها: {count}\n"
                        f"💾 حجم: {size_mb:.2f} MB\n"
                        f"🕓 زمان فشرده‌سازی: {duration}s\n"
                        f"📂 پارت‌ها: {total_parts}")

    await update.message.reply_photo(photo=qr_img, caption=f"🔹 NOORI Backup {timestamp}")

    # ارسال پارت‌ها
    for i, part in enumerate(parts, start=1):
        size = os.path.getsize(part) / (1024 * 1024)
        await update.message.reply_document(InputFile(part),
            caption=f"📦 پارت {i}/{total_parts} — {size:.2f} MB")
        print(f"[UPLOAD] Sent part {i}/{total_parts} ({size:.2f} MB)")
        os.remove(part)

    os.remove(zip_path)
    await update.message.reply_text("✅ بک‌آپ کامل ارسال شد!\n📤 آماده برای بازیابی در هر زمان.")

# ☁️ بک‌آپ ابری (ارسال مستقیم به ادمین)
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    zip_path, timestamp, count, size_mb, duration = create_zip_backup()
    parts = split_file(zip_path)
    total_parts = len(parts)

    with open(zip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    qr_img = generate_qr_image(encoded, timestamp)

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=qr_img,
        caption=f"☁️ Cloud Backup — {timestamp}\n📦 فایل‌ها: {count}\n💾 {size_mb:.2f} MB در {total_parts} پارت")

    for i, part in enumerate(parts, start=1):
        size = os.path.getsize(part) / (1024 * 1024)
        await context.bot.send_document(chat_id=ADMIN_ID,
            document=InputFile(part),
            caption=f"📦 پارت {i}/{total_parts} — {size:.2f} MB — {timestamp}")
        print(f"[CLOUD] Sent part {i}/{total_parts} ({size:.2f} MB)")
        os.remove(part)

    os.remove(zip_path)
    print(f"[CLOUD BACKUP] Done {timestamp}")

# ♻️ بازیابی از بک‌آپ ZIP تکی
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("📎 فایل ZIP بک‌آپ را ریپلای کن و سپس /restore بزن.")

    msg = await update.message.reply_text("♻️ در حال بازیابی از بک‌آپ...")

    file = await update.message.reply_to_message.document.get_file()
    path = os.path.join(BACKUP_DIR, "restore_temp.zip")
    await file.download_to_drive(path)

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
            bars = "█" * (percent // 5) + "▒" * (20 - percent // 5)
            await msg.edit_text(f"♻️ بازیابی {percent}% [{bars}]")
            await asyncio.sleep(0.1)

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
            zip_path, timestamp, count, size_mb, duration = create_zip_backup()
            parts = split_file(zip_path)
            total_parts = len(parts)

            with open(zip_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            qr_img = generate_qr_image(encoded, timestamp)

            await bot.send_photo(chat_id=ADMIN_ID, photo=qr_img,
                caption=f"🤖 Auto Backup — {timestamp}\n📦 {count} فایل\n💾 {size_mb:.2f} MB\n📂 {total_parts} پارت")

            for i, part in enumerate(parts, start=1):
                size = os.path.getsize(part) / (1024 * 1024)
                await bot.send_document(chat_id=ADMIN_ID,
                    document=InputFile(part),
                    caption=f"📦 Auto پارت {i}/{total_parts} — {size:.2f} MB — {timestamp}")
                os.remove(part)

            os.remove(zip_path)
            print(f"[AUTO BACKUP] {timestamp} complete ✅")
        except Exception as e:
            print(f"[AUTO BACKUP ERROR] {e}")
        await asyncio.sleep(21600)  # هر 6 ساعت
