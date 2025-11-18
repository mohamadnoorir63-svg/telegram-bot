from telegram.ext import CommandHandler
from bot import mute_speaker, unmute_speaker  # یا مسیر دقیق تو

def register_speaker_commands(application):
    """ثبت دستورات سخنگوی فارسی"""
    application.add_handler(CommandHandler("سخنگو_روشن", unmute_speaker))
    application.add_handler(CommandHandler("سخنگو_خاموش", mute_speaker))
