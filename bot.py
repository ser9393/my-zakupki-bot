import asyncio
import logging
import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

BOT_TOKEN = "8546161737:AAGD5lxNL8cmt7nIkfBY-dlQyShscbgyqsw"
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
    if "zakupki.mos.ru/auction/" not in url:
        await message.answer("Пожалуйста, отправь правильную ссылку на аукцион.")
        return
    
    try:
        auction_id = url.split('/auction/')[1].split('?')[0]
    except:
        await message.answer("Не удалось понять номер аукциона из ссылки.")
        return

    msg = await message.answer("⏳ Запрашиваю данные с сервера госзакупок...")
    
    try:
        # Официальный API портала mos.ru
        api_url = f"https://zakupki.mos.ru/newapi/api/Auction/GetAuction?id={auction_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Пытаемся достать цену, название и заказчика
            name = data.get('name', 'Неизвестный товар')
            price = data.get('startPrice', 'Неизвестно')
            customer = data.get('customer', {}).get('name', 'Неизвестный заказчик')
            
            answer = f"✅ **Данные найдены!**\n\n"
            answer += f"📦 Товар: {name}\n"
            answer += f"💰 Начальная цена: {price} ₽\n"
            answer += f"🏢 Заказчик: {customer}\n"
            await msg.edit_text(answer, parse_mode="Markdown")
        else:
            await msg.edit_text(f"❌ Ошибка API. Сайт ответил кодом: {response.status_code}")
            
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при чтении: {str(e)}")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен")

async def on_shutdown(app):
    await bot.delete_webhook()

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
