import asyncio
import logging
import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask

BOT_TOKEN = "8546161737:AAGD5lxNL8cmt7nIkfBY-dlQyShscbgyqsw"

# --- Flask (заглушка для Render) ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

# --- Бот ---
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

# --- Функция запуска бота для Gunicorn ---
def start_bot():
    asyncio.run(dp.start_polling(bot))

# Запускаем бота в фоне при старте Gunicorn
import threading
threading.Thread(target=start_bot, daemon=True).start()
