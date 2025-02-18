import os

from dotenv import load_dotenv
import telebot
from telebot.types import InputFile

load_dotenv()

API_TOKEN = os.getenv("BOT_API_TOKEN")

bot = telebot.TeleBot(API_TOKEN)


def send_bot_message(chat_id: int, photo_url: str, message: str):
    photo = InputFile(photo_url)
    bot.send_photo(chat_id, photo, caption=message, parse_mode="html")
    