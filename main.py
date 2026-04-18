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
WEB_APP_URL = os.getenv("WEB_APP_URL")
PORT = int(os.getenv("PORT", 8080))

# ID КАНАЛІВ
MODERATION_CH_ID = -1003732364849
CASH_CH_ID = -1003968761429
LOGS_CH_ID = -1003974489073
SUPPORT_LINK = "https://t.me/elitegirls_support"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# БАЗА ДАНИХ
cluster = AsyncIOMotorClient(MONGO_URL)
db = cluster["EliteDB"]
users_col = db["users"]
models_col = db["models"]

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Elite Girls Bot is Active!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

# --- СТАТИ (FSM) ---
class Reg(StatesGroup):
    name = State()
    age = State()
    photo = State()

class Chatting(StatesGroup):
    target_model = State()

# --- ЛОГІКА ПРИБУТКУ 75/25 ---
async def log_transaction(amount, model_id, client_id):
    m_share = amount * 0.75
    a_share = amount * 0.25
    await models_col.update_one({"user_id": int(model_id)}, {"$inc": {"balance": m_share}}, upsert=True)
    
    report = (f"💰 КАСА | +{amount} 💎\nМодель (75%): +{m_share}\nАдмін (25%): +{a_share}\nКлієнт ID: {client_id}")
    await bot.send_message(CASH_CH_ID, report)

# --- ГОЛОВНЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    u_id = message.from_user.id
    user = await users_col.find_one({"user_id": u_id})
    if not user:
        await users_col.insert_one({"user_id": u_id, "balance": 0, "free_msgs": 5})
        await bot.send_message(LOGS_CH_ID, f"🆕 Новий юзер: {message.from_user.full_name}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕺 Хлопець (Вхід)", callback_data="client_menu")],
        [InlineKeyboardButton(text="💃 Дівчина (Реєстрація)", callback_data="reg_start")]
    ])
    await message.answer("✨ **ELITE GIRLS PREMIUM** ✨\n\nВітаємо! Обери свою роль:", reply_markup=kb)

# --- МЕНЮ ХЛОПЦЯ ---
@dp.callback_query(F.data == "client_menu")
async def client_menu(callback: CallbackQuery):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 КАТАЛОГ ДІВЧАТ", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💎 Поповнити баланс", url=SUPPORT_LINK)]
    ])
    await callback.message.edit_text(
        f"💎 Твій баланс: {user.get('balance', 0)} діамантів\n"
        f"📩 Безкоштовних повідомлень: {user.get('free_msgs', 0)}\n\n"
        "Обирай дівчину та починай чат!", reply_markup=kb
    )

# --- РЕЄСТРАЦІЯ ДІВЧИНИ ---
@dp.callback_query(F.data == "reg_start")
async def reg_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💃 Твоє ім'я (псевдонім)?")
    await state.set_state(Reg.name)

@dp.message(Reg.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Твій вік?")
    await state.set_state(Reg.age)

@dp.message(Reg.age)
async def reg_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Надішли своє найкраще фото 📸")
    await state.set_state(Reg.photo)

@dp.message(Reg.photo, F.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    m_id = message.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Схвалити", callback_data=f"adm_ok_{m_id}")]])
    
    await bot.send_photo(MODERATION_CH_ID, message.photo[-1].file_id, 
                         caption=f"💎 НОВА АНКЕТА\nІм'я: {data['name']}\nВік: {data['age']}\nID: {m_id}", 
                         reply_markup=kb)
    await message.answer("✅ Анкета надіслана! Очікуй схвалення.")
    await state.clear()

@dp.callback_query(F.data.startswith("adm_ok_"))
async def approve(callback: CallbackQuery):
    m_id = int(callback.data.split("_")[2])
    await models_col.update_one({"user_id": m_id}, {"$set": {"status": "active", "balance": 0}}, upsert=True)
    await bot.send_message(m_id, "🌟 Твою анкету схвалено! Тепер ти в каталозі.")
    await callback.message.edit_caption(caption="✅ СХВАЛЕНО")

# --- ОБРОБКА ДАНИХ З MINI APP ---
@dp.message(F.web_app_data)
async def web_app_receive(message: types.Message, state: FSMContext):
    data = json.loads(message.web_app_data.data)
    if data.get("action") == "start_chat":
        m_id = data.get("model_id")
        await state.update_data(target_model=m_id)
        await state.set_state(Chatting.target_model)
        await message.answer(f"✅ Чат з дівчиною #{m_id} активовано! Пиши повідомлення 👇")

# --- ПЛАТНИЙ ЧАТ ---
@dp.message(Chatting.target_model)
async def process_chat(message: types.Message, state: FSMContext):
    u_id = message.from_user.id
    user = await users_col.find_one({"user_id": u_id})
    s_data = await state.get_data()
    m_id = s_data.get("target_model")

    if user["free_msgs"] > 0:
        await users_col.update_one({"user_id": u_id}, {"$inc": {"free_msgs": -1}})
        await message.answer(f"📩 Надіслано! (Залишилось free: {user['free_msgs'] - 1})")
    elif user.get("balance", 0) >= 10:
        await users_col.update_one({"user_id": u_id}, {"$inc": {"balance": -10}})
        await log_transaction(10, m_id, u_id)
        await message.answer("💎 Знято 10 діамантів за повідомлення.")
    else:
        await message.answer("❌ Недостатньо 💎. Поповни баланс через підтримку.")

# --- ЗАПУСК ---
async def main():
    await asyncio.gather(start_web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
