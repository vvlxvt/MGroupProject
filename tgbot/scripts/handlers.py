import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def start_handler(message: Message):
    logger.info(
        "Telegram start command received",
        extra={"has_start_argument": " " in (message.text or "")},
    )

    text = message.text or ""
    args = text.split(" ", 1)[1] if " " in text else None
    if args:
        await message.answer(f"Вы перешли по ссылке с аргументом: {args}")
    else:
        await message.answer("Вы нажали /start вручную, аргументов нет.")
