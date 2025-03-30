from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    print(f"Received message: {message.text}")  # Логируем входящее сообщение

    args = message.text.split(" ", 1)[1] if " " in message.text else None
    if args:
        await message.answer(f"Вы перешли по ссылке с аргументом: {args}")
    else:
        await message.answer("Вы нажали /start вручную, аргументов нет.")




