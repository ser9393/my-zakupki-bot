import asyncio
import logging
import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

BOT_TOKEN = "8546161737:AAGD5lxNL8cmt7nIkfBY-dlQyShscbgyqsw"
DAMIA_KEY = "1174ab6b3317737c801bed5996269efd852417d9"

# URL вашего сервиса на Render (я вижу его на скриншоте)
WEBHOOK_HOST = "https://zakupki-bot-ai.onrender.com" 
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот для поиска закупок через DaMIA. Отправь команду:\n/search <товар> (например: /search медбол)")

@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажи товар. Пример: /search медбол")
        return
    
    query = parts[1]
    msg = await message.answer(f"⏳ Ищу закупки по запросу: {query}...")
    
    try:
        url = f"https://api.damia.ru/zakupki/zsearch?q={query}&key={DAMIA_KEY}"
        response = requests.get(url, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if "44" in data and data["44"]:
                answer = f"✅ **Найдены закупки по запросу '{query}':**\n\n"
                count = 0
                for reg_number, info in data["44"].items():
                    if count >= 5: break
                    
                    product = info.get("Продукт", "Без названия")
                    price = info.get("Сумма", 0)
                    date = info.get("ДатаПубл", "—")
                    status = info.get("Статус", "Неизвестно")
                    
                    answer += f"📦 **{product}**\n"
                    answer += f"💰 Сумма: {price:,.2f} ₽\n"
                    answer += f"📅 Дата: {date} | Статус: {status}\n"
                    answer += f"🔗 [Открыть в ЕИС](https://zakupki.gov.ru/epz/order/notice/notice44/common-info.html?regNumber={reg_number})\n\n"
                    count += 1
                
                await msg.edit_text(answer, parse_mode=ParseMode.MARKDOWN)
            else:
                await msg.edit_text(f"По запросу '{query}' ничего не найдено.")
        else:
            await msg.edit_text(f"❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")

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
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
