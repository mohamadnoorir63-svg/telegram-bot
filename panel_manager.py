import json
import os
from telegram import ReplyKeyboardMarkup

PANEL_FILE = os.path.join("data", "panel.json")

# ========== Load Panel ==========
def load_panel():
    with open(PANEL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ========== Build Keyboard ==========
def build_keyboard(buttons):
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# ========== Get Main Menu ==========
def get_main_keyboard():
    panel = load_panel()
    return build_keyboard(panel["main"])


# ========== Get Submenu ==========
def get_submenu(button):
    panel = load_panel()
    submenu = panel["submenu"].get(button)
    if submenu:
        return build_keyboard(submenu)
    return None
