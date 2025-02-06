import logging
import os

import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from bot_instance import bot

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mgrupsite.settings')
import django
django.setup()
from tgbot.scripts import vars, handlers

TOKEN = vars.TELEGRAM_BOT_TOKEN
WEBHOOK_URL = vars.WEBHOOK_URL
WEBHOOK_PATH = vars.WEBHOOK_PATH
HOST = vars.TG_SERVER_HOST
PORT = vars.TG_SERVER_PORT


async def on_startup(bot:Bot)->None:
    await bot.set_webhook(WEBHOOK_URL)
async def on_shutdown(bot:Bot)->None:
    await bot.delete_webhook()

def main() -> None:
    dp = Dispatcher()
    dp.include_router(handlers.router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()


