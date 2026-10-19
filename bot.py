import asyncio
import logging
import os
import requests
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from openai import AsyncOpenAI
from flask import Flask

# ==========================================
# КЛЮЧИ БЕРУТСЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ RENDER
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
DAMIA_API_KEY = os.getenv("DAMIA_API_KEY")
# ==========================================

# Создаем Flask-приложение для Render (заглушка)
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

client = AsyncOpenAI(
    api_key=YANDEX_API_KEY,
    base_url="https://llm.api.cloud.yandex.net/v1",
)

SYSTEM_PROMPT = "Ты — строгий и профессиональный финансовый аналитик по госзакупкам."

CITIES = {
    "москва": "77", "питер": "78", "санкт-петербург": "78", "новосибирск": "54",
    "екатеринбург": "66", "казань": "16", "набережные челны": "16", "менделеевск": "16",
    "нижний новгород": "52", "челябинск": "74", "самара": "63", "омск": "55",
    "ростов-на-дону": "61", "уфа": "02", "красноярск": "24", "воронеж": "36",
    "пермь": "59", "волгоград": "34", "краснодар": "23", "сочи": "23",
    "саратов": "64", "тюмень": "72", "тольятти": "63"
}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я твой ИИ-ассистент.\n\n"
        "🔹 Напиши **«закупка [слово] [город]»** — найду свежие закупки.\n"
        "🔹 /calc [цена] [себестоимость] — посчитать маржу\n"
        "Или просто задай любой вопрос!"
    )

@dp.message(Command("calc"))
async def cmd_calc(message: types.Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Формат: /calc 9751.50 6000")
        return
    try:
        price = float(parts[1])
        cost = float(parts[2])
        margin = price - cost
        margin_pct = (margin / price) * 100 if price > 0 else 0
        
        if margin < 0: status = "🔴 УБЫТОК! Не ставь."
        elif margin_pct < 10: status = "🟡 КРАЙНЕ РИСКОВАННО."
        elif margin_pct < 20: status = "🟢 Нормально."
        else: status = "🟢 ВЫГОДНО."
            
        await message.answer(
            f"💰 Выручка: <code>{price:,.2f} ₽</code>\n"
            f"📦 Себестоимость: <code>{cost:,.2f} ₽</code>\n"
            f"📈 Маржа: <code>{margin:,.2f} ₽</code> ({margin_pct:.1f}%)\n\n"
            f"{status}", parse_mode=ParseMode.HTML
        )
    except ValueError:
        await message.answer("❌ Ошибка. Введи числа.")

@dp.message()
async def handle_ai(message: types.Message):
    text = message.text.strip()
    text_lower = text.lower()
    
    if text_lower.startswith("закупка"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("❌ Напиши: закупка [слово] [город]")
            return
        
        query_and_city = parts[1].split()
        region_code = None
        query = query_and_city[0]
        
        if len(query_and_city) > 1:
            city_name = " ".join(query_and_city[1:]).lower()
            if city_name in CITIES:
                region_code = CITIES[city_name]
                query = query_and_city[0]
            else:
                query = " ".join(query_and_city) 
        
        msg = await message.answer(f"⏳ Ищу закупки по слову '{query}'...")
        
        try:
            url = "https://api.damia.ru/zakupki/zsearch"
            today = datetime.now()
            month_ago = today - timedelta(days=30)
            
            params = {
                "q": query, "fz": "44", "key": DAMIA_API_KEY,
                "from_date": month_ago.strftime("%Y-%m-%d"),
                "to_date": today.strftime("%Y-%m-%d")
            }
            if region_code: params["region"] = region_code
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                if "44" in data:
                    for reg_num, tender in data["44"].items():
                        results.append({
                            "regNumber": reg_num,
                            "name": tender.get("Продукт", "Без названия"),
                            "maxPrice": tender.get("Сумма", "?"),
                            "date": tender.get("ДатаПубл", "?")
                        })
                
                if not results:
                    await msg.edit_text(f"По запросу '{query}' ничего не найдено.")
                    return
                
                answer = f"🔎 Найдено: {len(results)}\n\n"
                for t in results[:5]:
                    answer += f"📦 <b>{t['name']}</b>\n💰 НМЦ: {t['maxPrice']} ₽\n📅 {t['date']}\n🔗 <a href='https://zakupki.gov.ru/epz/order/notice/notice223/common-info.html?regNumber={t['regNumber']}'>Ссылка</a>\n\n"
                
                await msg.edit_text(answer, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            else:
                await msg.edit_text(f"❌ Ошибка DaMIA: {response.status_code}")
        except Exception as e:
            await msg.edit_text(f"❌ Ошибка: {e}")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        response = await client.chat.completions.create(
            model=f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        await message.answer(f"Ошибка ИИ: {e}")

def run_bot():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    import threading
    # Запускаем бота в отдельном потоке
    threading.Thread(target=run_bot, daemon=True).start()
    # Запускаем Flask в основном потоке для Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
