from decouple import config

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")
WEBHOOK_HOST = "https://ae05-94-43-154-7.ngrok-free.app"
# WEBHOOK_HOST = "https://mgroup-vvlxvt.amvera.io"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

TG_SERVER_HOST = "127.0.0.1"
TG_SERVER_PORT = 8001


import hmac
import hashlib


def hmac_sha256_hex(data_check_string, secret_key):
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


# Пример использования
bot_token = TELEGRAM_BOT_TOKEN
secret_key = hashlib.sha256(bot_token.encode()).digest()

data_check_string = "auth_date=1743418682\nfirst_name=Vit\nid=541172529\nphoto_url=https://t.me/i/userpic/320/mtFfh0UnMxuQqpTq9iDJ8f5kEzOVvsp9pzCniWSMRzQ.jpg\nusername=vvlxvt"

calculated_hash = hmac_sha256_hex(data_check_string, secret_key)
print(calculated_hash)
