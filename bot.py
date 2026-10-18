import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = "8546161737:AAGD5lxNL8cmt7nIkfBY-dlQyShscbgyqsw"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправь мне ссылку на аукцион с mos.ru (например: https://zakupki.mos.ru/auction/10321376)")

@dp.message()
async def handle_url(message: types.Message):
    url = message.text.strip()
    if "zakupki.mos.ru/auction/" not in url:
        await message.answer("Пожалуйста, отправь правильную ссылку на аукцион.")
        return
    
    # Вытаскиваем номер аукциона из ссылки
    try:
        auction_id = url.split('/auction/')[1].split('?')[0]
    except:
        await message.answer("Не удалось понять номер аукциона из ссылки.")
        return

    msg = await message.answer("⏳ Запрашиваю данные с сервера госзакупок...")
    
    try:
        # Используем официальный API портала mos.ru (он реже блокирует)
        api_url = f"https://zakupki.mos.ru/newapi/api/Auction/GetAuction?id={auction_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Пытаемся достать цену и название
            name = data.get('name', 'Неизвестный товар')
            price = data.get('startPrice', 'Неизвестно')
            
            answer = f"✅ **Данные найдены!**\n\n"
            answer += f"📦 Товар: {name}\n"
            answer += f"💰 Начальная цена: {price} ₽\n"
            await msg.edit_text(answer, parse_mode="Markdown")
        else:
            await msg.edit_text(f"❌ Ошибка API. Сайт ответил кодом: {response.status_code}")
            
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при чтении: {str(e)}")

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
