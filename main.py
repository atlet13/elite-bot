import asyncio
import logging
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, WebAppInfo
from aiohttp import web

# --- НАЛАШТУВАННЯ ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://atlet13.github.io/elite-app/")
PORT = int(os.getenv("PORT", 8080))

# Твої ID каналів
MODERATION_CH_ID = -1003732364849
CASH_CH_ID = -1003968761429
LOGS_CH_ID = -1003974489073
SUPPORT_LINK = "https://t.me/elitegirls_support"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Підключення до MongoDB
cluster = AsyncIOMotorClient(MONGO_URL)
db = cluster["EliteDB"]
users_col = db["users"]
models_col = db["models"]

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (ЩОБ НЕ ЗАСИНАВ) ---
async def handle(request):
    return web.Response(text="Elite Girls Bot is Active!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"✅ Web server started on port {PORT}")

# --- СТАТИ (FSM) ---
class Reg(StatesGroup):
    name = State()
    photo = State()

class Chatting(StatesGroup):
    target_model = State()

# --- ЛОГІКА РОЗПОДІЛУ 75/25 ---
async def log_transaction(amount, model_id, client_id):
    model_share = amount * 0.75
    admin_share = amount * 0.25
    
    # Нарахування моделі в БД
    await models_col.update_one({"user_id": int(model_id)}, {"$inc": {"balance": model_share}}, upsert=True)
    
    report = (
        f"💰 **НОВИЙ ПРИБУТОК**\n"
        f"👤 Клієнт ID: {client_id}\n"
        f"💃 Модель ID: {model_id}\n"
        f"💵 Сума: {amount} 💎\n"
        f"------------------\n"
        f"✅ Моделі (75%): +{model_share}\n"
        f"🏦 Адмін (25%): +{admin_share}"
    )
    await bot.send_message(CASH_CH_ID, report)

# --- ГОРОВНЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    u_id = message.from_user.id
    user = await users_col.find_one({"user_id": u_id})
    
    if not user:
        user = {"user_id": u_id, "name": message.from_user.full_name, "balance": 0, "free_msgs": 5}
        await users_col.insert_one(user)
        await bot.send_message(LOGS_CH_ID, f"🆕 Новий юзер: {message.from_user.full_name} (ID: {u_id})")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 КАТАЛОГ ДІВЧАТ", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💃 Стати моделлю", callback_data="reg_model")],
        [InlineKeyboardButton(text="🆘 Підтримка", url=SUPPORT_LINK)]
    ])
    
    await message.answer(
        f"✨ **ELITE GIRLS** ✨\n\nПривіт, {message.from_user.first_name}!\n"
        f"Твій баланс: {user.get('balance', 0)} 💎\n"
        f"Безкоштовно: {user.get('free_msgs', 0)} повідомлень\n\n"
        "Обирай дівчину в каталозі!", reply_markup=kb
    )

# --- РЕЄСТРАЦІЯ МОДЕЛІ ---
@dp.callback_query(F.data == "reg_model")
async def start_reg(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💃 Напиши своє ім'я (псевдонім):")
    await state.set_state(Reg.name)

@dp.message(Reg.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Тепер надішли своє найкраще фото для анкети:")
    await state.set_state(Reg.photo)

@dp.message(Reg.photo, F.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    m_id = message.from_user.id
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"adm_ok_{m_id}")]
    ])
    
    await bot.send_photo(
        MODERATION_CH_ID, 
        message.photo[-1].file_id, 
        caption=f"💎 НОВА АНКЕТА\nІм'я: {data['name']}\nID: {m_id}",
        reply_markup=kb
    )
    await message.answer("⏳ Дякуємо! Анкета на модерації. Очікуй повідомлення про схвалення.")
    await state.clear()

# --- МОДЕРАЦІЯ ---
@dp.callback_query(F.data.startswith("adm_ok_"))
async def approve_model(callback: CallbackQuery):
    m_id = int(callback.data.split("_")[2])
    await models_col.update_one({"user_id": m_id}, {"$set": {"status": "active", "balance": 0}}, upsert=True)
    await bot.send_message(m_id, "🚀 Вітаємо! Твою анкету схвалено. Твій дохід: 75%.\nМожеш починати роботу!")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ СХВАЛЕНО")

# --- ОБРОБКА ВИБОРУ З WEB APP ---
@dp.message(F.web_app_data)
async def web_app_receive(message: types.Message, state: FSMContext):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("action") == "start_chat":
            m_id = data.get("model_id")
            await state.update_data(target_model=m_id)
            await state.set_state(Chatting.target_model)
            await message.answer(f"✅ Чат з моделлю #{m_id} активовано. Напиши їй щось!")
    except Exception as e:
        logging.error(f"WebApp Data Error: {e}")

# --- ОПЛАТА ЧАТУ ---
@dp.message(Chatting.target_model)
async def process_chat(message: types.Message, state: FSMContext):
    u_id = message.from_user.id
    user = await users_col.find_one({"user_id": u_id})
    s_data = await state.get_data()
    m_id = s_data.get("target_model")

    if user["free_msgs"] > 0:
        await users_col.update_one({"user_id": u_id}, {"$inc": {"free_msgs": -1}})
        await message.answer(f"📩 Надіслано! (Залишилось free: {user['free_msgs'] - 1})")
    else:
        if user.get("balance", 0) >= 10:
            await users_col.update_one({"user_id": u_id}, {"$inc": {"balance": -10}})
            await log_transaction(10, m_id, u_id)
            await message.answer("💎 Знято 10 діамантів за повідомлення.")
        else:
            await message.answer("❌ На балансі недостатньо 💎. Поповни рахунок у підтримки.")

# --- ЗАПУСК ---
async def main():
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
