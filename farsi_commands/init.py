from .speaker import register_speaker_commands

def register_all_farsi(app):
    """ثبت همه دستورات فارسی"""
    register_speaker_commands(app)
