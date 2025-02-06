from decouple import config

TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = config('TELEGRAM_CHAT_ID')
WEBHOOK_HOST = 'https://263e-94-43-154-7.ngrok-free.app'
# WEBHOOK_HOST = "https://mgroup-vvlxvt.amvera.io"
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

TG_SERVER_HOST = "127.0.0.1"
TG_SERVER_PORT = 8001