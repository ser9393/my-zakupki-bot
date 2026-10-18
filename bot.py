import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = "8546161737:AAGD5lxNL8cmt7nIkfBY-dlQyShscbgyqsw"

# --- ПРОКСИ (если не сработает, замените на другой IP) ---
PROXY_URL = "http://45.132.193.226:8080" 
# --------------------------------------------------------

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправь мне ссылку с mos.ru, и я проверю данные.")

@dp.message()
async def handle_url(message: types.Message):
    url = message.text.strip()
    if "zakupki.mos.ru" not in url:
        await message.answer("Пожалуйста, отправь ссылку с сайта zakupki.mos.ru")
        return
    
    msg = await message.answer("⏳ Собираю данные (это может занять до 15 секунд)...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        proxies = {
            "http": PROXY_URL,
            "https": PROXY_URL,
        }
        
        # Запрос через прокси
        response = requests.get(url, headers=headers, timeout=15, proxies=proxies)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
            
            answer = f"✅ Страница открыта!\n\n"
            
            # Ищем цену
            if "Текущая цена" in text_content:
                answer += "💰 Нашел блок с ценой на странице.\n"
            else:
                answer += "💰 Блок с ценой не найден.\n"
                
            # Ищем ставки
            if "Ставок:" in text_content:
                answer += "📊 Нашел информацию о ставках.\n"
            
            await msg.edit_text(answer)
        else:
            await msg.edit_text(f"❌ Сайт ответил с ошибкой. Код: {response.status_code}")
            
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при чтении: {str(e)}")

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
