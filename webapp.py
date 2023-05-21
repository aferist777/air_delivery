import asyncio
import os

from aiogram.utils.executor import start_webhook

from app import on_startup_app
from core import dp, bot, logger

WEBHOOK_HOST = f'https://{os.environ["WEBHOOK_HOST"]}'
WEBHOOK_PATH = f'/{os.environ["BOT_TOKEN"]}/'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = '127.0.0.1'
WEBAPP_PORT = os.environ["WEBAPP_PORT"]

SSL_PEM = '/home/airbot/PUBLIC.pem'


# noinspection PyUnusedLocal
async def on_startup_webapp(dispatcher=dp):
    await on_startup_app()
    asyncio.create_task(bot.set_webhook(WEBHOOK_URL, certificate=open(SSL_PEM, 'rb')))
    logger.info('webhook created')


# noinspection PyUnusedLocal
async def on_shutdown_webapp(dispatcher=dp):
    await dp.storage.close()
    await dp.storage.wait_closed()
    await asyncio.sleep(1)
    await bot.delete_webhook()
    logger.warning('webhook deleted')


if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup_webapp,
        on_shutdown=on_shutdown_webapp,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT)
