import logging
import os
import sys
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)

# -------------------------------------------------------------------
# Django setup
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mgrupsite.settings")

import django  # noqa: E402

django.setup()

# -------------------------------------------------------------------
# Local imports (after Django setup)
# -------------------------------------------------------------------

from bot_instance import bot  # noqa: E402
from mgrupsite.settings import WEBHOOK_URL, WEBHOOK_PATH, TG_SERVER_HOST, TG_SERVER_PORT  # noqa: E402
from tgbot.scripts.handlers import router  # noqa: E402

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
HOST = TG_SERVER_HOST
PORT = TG_SERVER_PORT


# -------------------------------------------------------------------
# Lifespan hooks
# -------------------------------------------------------------------


async def on_startup(app: web.Application) -> None:
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(app: web.Application) -> None:
    await bot.delete_webhook()


# -------------------------------------------------------------------
# App factory
# -------------------------------------------------------------------


def create_app() -> web.Application:
    dp = Dispatcher()
    dp.include_router(router)

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)
    return app


# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------


def main() -> None:
    app = create_app()
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    main()
