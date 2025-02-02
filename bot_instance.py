from aiogram import Bot
from decouple import config

chat_id = config('TELEGRAM_CHAT_ID')
TOKEN = config('TELEGRAM_BOT_TOKEN')
bot = Bot(token=TOKEN)
