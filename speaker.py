# speaker.py
from telegram.ext import MessageHandler, filters

def register_speaker_commands(application, mute_speaker, unmute_speaker):
    """ثبت دستورات سخنگو فارسی"""
    application.add_handler(
        MessageHandler(filters.Regex(r"^سخنگو_خاموش$"), mute_speaker),
        group=4  # یا هر گروهی که مناسب می‌دونی
    )
    application.add_handler(
        MessageHandler(filters.Regex(r"^سخنگو_روشن$"), unmute_speaker),
        group=4
    )
