import asyncio
import logging
import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask

BOT_TOKEN = "8546161737:AAGD5lxNL8cmt7nIkfBY-dlQyShscbgyqsw"

# --- Веб-сервер для Render ---
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
    await message.answer("Привет! Отправь мне ссылку на аукцион с mos.ru, и я попробую проверить данные.")

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
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
            answer = f"✅ Страница открыта!\n\n"
            if "Текущая цена" in text_content:
                answer += "💰 Нашел блок с ценой.\n"
            else:
                answer += "💰 Блок с ценой не найден.\n"
            if "Ставок:" in text_content:
                answer += "📊 Нашел информацию о ставках.\n"
            await msg.edit_text(answer)
        else:
            await msg.edit_text(f"❌ Сайт ответил с ошибкой. Код: {response.status_code}")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при чтении: {str(e)}")

async def main():
    # Запускаем бота в фоновой задаче
    bot_task = asyncio.create_task(dp.start_polling(bot))
    
    # Запускаем Flask в основном потоке (Render это увидит)
    port = int(os.environ.get("PORT", 10000))
    print(f"Веб-сервер запущен на порту {port}, бот работает в фоне.")
    app.run(host="0.0.0.0", port=port)
    
    await bot_task

if __name__ == "__main__":
    asyncio.run(main())
