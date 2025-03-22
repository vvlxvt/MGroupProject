from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import redis
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=1)  # Используем ту же базу, что и в Django

router = Router()
@router.message(Command('start'))
async def start_handler(message: Message):
    args = message.text.split(maxsplit=1)  # Разделяем строку на команду и аргумент
    print(args)
    user = message.from_user
    user_id = user.id
    username = user.username
    print(username)

    if len(args) > 1:
        tg_username = args[1].strip()
        redis_client.hset(tg_username, "user_id", user_id)
        try:
            code = redis_client.hget(tg_username, 'code').decode('utf-8')
            await message.reply(f'Привет, {tg_username} \n Ваш пароль: {code}!')
        except:
            await message.reply(f"К сожалению, я не нашел пароль для пользователя с именем {tg_username}. "
                                f"Пожалуйста, проверьте имя или начните процесс верификации заново.")
            # Можно добавить логирование для отладки
            print(f"[DEBUG] Пользователь {tg_username} отсутствует в ключах")
    else:
        await message.reply("Пожалуйста, укажите ваш Telegram username в форме")
