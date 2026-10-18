import asyncio
import logging
import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask
from threading import Thread

BOT_TOKEN = "8546161737:AAGD5lxNL8cmt7nIkfBY-dlQyShscbgyqsw"

# --- ЗАГЛУШКА ДЛЯ RENDER (чтобы не было ошибки порта) ---
app = Flask(__name__)
@app.route('/')
def index():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
# -----------------------------------------------------

# --- ПРОКСИ (если найдете рабочий, вставьте сюда) ---
PROXY_URL = None  # Например: "http://45.132.193.226:8080"
# ---------------------------------------------------

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
        
        # Если прокси указан, используем его
        proxies = None
        if PROXY_URL:
            proxies = {"http": PROXY_URL, "https": PROXY_URL}
        
        response = requests.get(url, headers=headers, timeout=15, proxies=proxies)
        
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
    # Запускаем веб-сервер в фоне, чтобы Render был доволен
    Thread(target=run_web_server).start()
    print("Бот запущен и веб-сервер работает!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
