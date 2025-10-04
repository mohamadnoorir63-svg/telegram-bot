# -*- coding: utf-8 -*-
import telebot

# 🚨 این فقط برای تست ـه، توکن رو مستقیم گذاشتم
TOKEN = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام 🌹 ربات روشن شد و کار می‌کنه!")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, f"شما گفتی: {message.text}")

print("🤖 Bot is running...")
bot.infinity_polling()
