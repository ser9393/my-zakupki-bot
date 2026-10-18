import asyncio
import logging
import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

BOT_TOKEN = "8546161737:AAGD5lxNL8cmt7nIkfBY-dlQyShscbgyqsw"
# Ваш URL на Render
WEBHOOK_HOST = "https://zakupki-bot-78oq.onrender.com" 
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправь мне ссылку на аукцион с mos.ru.")

@dp.message()
async def handle_url(message: types.Message):
    url = message.text.strip()
    if "zakupki.mos.ru" not in url:
        await message.answer("Пожалуйста, отправь ссылку с сайта zakupki.mos.ru")
        return
    msg = await message.answer("⏳ Пробую открыть страницу...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            await msg.edit_text("✅ Страница открыта! (Данные могут не отобразиться из-за блокировки IP)")
        else:
            await msg.edit_text(f"❌ Ошибка доступа. Код: {response.status_code}")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при чтении: {str(e)}")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен на {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"Запуск сервера на порту {port}")
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
