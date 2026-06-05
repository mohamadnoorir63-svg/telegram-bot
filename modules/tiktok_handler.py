# modules/tiktok_handler.py
         import os
import requests
import yt_dlp
import asyncio
import uuid

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

video_store = {}


async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return True

    if user.id in SUDO_USERS:       
