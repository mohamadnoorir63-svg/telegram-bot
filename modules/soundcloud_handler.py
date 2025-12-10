# modules/youtube_handler.py
import os
import shutil
import subprocess
import yt_dlp
from concurrent.futures import ThreadPoolExecutor

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"  # ← کوکی یوتیوب از این فایل

executor = ThreadPoolExecutor(max_workers=5)

# ================================
# تبدیل به MP3 (Thread)
# ================================
def convert_to_mp3_sync(filepath):
    mp3_path = filepath.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None

    subprocess.run([
        "ffmpeg", "-y", "-i", filepath,
        "-vn", "-ab", "192k", "-ar", "44100",
        mp3_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return mp3_path

# ================================
# دانلود از یوتیوب بر اساس Query
# ================================
def youtube_fallback_sync(query):
    """
    جستجو در یوتیوب و دانلود بهترین فایل صوتی به فرمت MP3
    """
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info:
            info = info["entries"][0]

        filename = ydl.prepare_filename(info)
        mp3_file = filename.rsplit(".", 1)[0] + ".mp3"

    return info, mp3_file
