import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = "8703162686:AAHmab2F_7W54X0g30wv5MAbgtRYdlpynAg"
ADMIN_ID = 8561782680 
START_PHOTO = "https://i.ibb.co/cS1xSG0w/image.jpg" # ТВОЄ ФОТО
WEB_APP_URL = "https://atlet13.github.io/elite-app/"
CARD_NUMBER = "4400 0055 5274 1933"

# ПІДКЛЮЧЕННЯ ДО БД (Пароль має бути EliteApp2026 в Atlas)
MONGO_URL = "mongodb+srv://admin:EliteApp2026@cluster0.tp0nxdu.mongodb.net/?retryWrites=true&w=majority"

try:
    cluster = AsyncIOMotorClient(MONGO_URL)
    db = cluster["elite_db"]
    users_col = db["users"]
    logger.info("БД готова")
except Exception as e:
    logger.error(f"DB Error: {e}")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Registration(StatesGroup):
    name, age, city, photo = State(), State(), State(), State()

class Payment(StatesGroup):
    waiting_for_receipt = State()

# --- СЕРВЕР ДЛЯ RENDER ---
async def handle(request): return web.Response(text="Active")
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()

# --- ЛОГІКА БОТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕺 Хлопець (Вхід)", callback_data="role_guy")],
        [InlineKeyboardButton(text="💃 Дівчина (Реєстрація)", callback_data="reg_girl")]
    ])
    await message.answer_photo(
        photo=START_PHOTO,
        caption="💎 **ELITEGIRLS PREMIUM** 💎\n\nВітаємо! Оберіть свою роль:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "role_guy")
async def role_guy(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ВІДКРИТИ ДОДАТОК", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])
    await callback.message.answer("Відкрийте додаток нижче. Баланс поповнюється у вкладці 'Wallet'.", reply_markup=markup)

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message, state: FSMContext):
    if message.web_app_data.data == "payment_requested":
        await message.answer(f"💳 **ОПЛАТА**\n\nКарта: `{CARD_NUMBER}`\n\nНадішліть фото чека сюди 👇")
        await state.set_state(Payment.waiting_for_receipt)

@dp.message(Payment.waiting_for_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    await message.answer("✅ Чек на перевірці!")
    await bot.send_photo(ADMIN_ID, photo=message.photo[-1].file_id, caption=f"💰 ЧЕК: @{message.from_user.username}")
    await state.clear()

# Реєстрація дівчини (спрощено)
@dp.callback_query(F.data == "reg_girl")
async def start_reg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.name)
    await callback.message.answer("💃 Твоє ім'я?")

@dp.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text); await state.set_state(Registration.age)
    await message.answer("Твій вік?")

@dp.message(Registration.age)
async def reg_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text); await state.set_state(Registration.photo)
    await message.answer("Надішли фото 📸")

@dp.message(Registration.photo, F.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await users_col.update_one({"user_id": message.from_user.id}, {"$set": {"status": "pending", **data}}, upsert=True)
    await message.answer("✅ Анкета надіслана!")
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Схвалити", callback_data=f"ok_{message.from_user.id}")]])
    await bot.send_photo(ADMIN_ID, photo=message.photo[-1].file_id, caption=f"👑 Нова модель: {data['name']}\nЮзер: @{message.from_user.username}", reply_markup=admin_markup)
    await state.clear()

@dp.callback_query(F.data.startswith("ok_"))
async def admin_ok(callback: CallbackQuery):
    uid = int(callback.data.split("_")[1])
    await users_col.update_one({"user_id": uid}, {"$set": {"status": "approved"}})
    await bot.send_message(uid, "🌟 Твою анкету схвалено!")
    await callback.message.edit_caption(caption="✅ СХВАЛЕНО")

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery): 
    await cmd_start(callback.message); await callback.message.delete()

async def main():
    # skip_updates=True критично важливо зараз!
    await asyncio.gather(start_web_server(), dp.start_polling(bot, skip_updates=True))

if __name__ == '__main__':
    asyncio.run(main())
