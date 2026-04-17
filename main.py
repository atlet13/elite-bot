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

# Налаштування логування для відстеження помилок на Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = "8703162686:AAHmab2F_7W54X0g30wv5MAbgtRYdlpynAg"
ADMIN_ID = 8561782680 
START_PHOTO = "https://i.ibb.co/cS1xSG0w/image.jpg" # Ваше лого
WEB_APP_URL = "https://atlet13.github.io/elite-app/"
CARD_NUMBER = "4400 0055 5274 1933"

# ПІДКЛЮЧЕННЯ ДО MONGODB
# ВАЖЛИВО: Переконайтеся, що пароль в MongoDB Atlas змінено на EliteApp2026
MONGO_URL = "mongodb+srv://admin:EliteApp2026@cluster0.tp0nxdu.mongodb.net/?retryWrites=true&w=majority"

try:
    cluster = AsyncIOMotorClient(MONGO_URL)
    db = cluster["elite_db"]
    users_col = db["users"]
    logger.info("✅ MongoDB підключено успішно")
except Exception as e:
    logger.error(f"❌ Помилка підключення до БД: {e}")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# СТАНИ (FSM)
class Registration(StatesGroup):
    name, age, city, bio, photo = State(), State(), State(), State(), State()

class Payment(StatesGroup):
    waiting_for_receipt = State()

# --- ВЕБ-СЕРВЕР ДЛЯ ПІДТРИМКИ RENDER ---
async def handle(request):
    return web.Response(text="EliteGirls Bot is Active")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()

# --- ПРИВІТАННЯ З ФОТО ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕺 Я — Хлопець (Вхід)", callback_data="role_guy")],
        [InlineKeyboardButton(text="💃 Я — Дівчина (Реєстрація)", callback_data="reg_girl")]
    ])
    await message.answer_photo(
        photo=START_PHOTO,
        caption="💎 **ELITEGIRLS PREMIUM** 💎\n\nЛаскаво просимо! Тут ви знайдете найкращий сервіс та ексклюзивні знайомства.\n\nОберіть свою роль для початку роботи:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# --- ЛОГІКА ДЛЯ ХЛОПЦЯ ---
@dp.callback_query(F.data == "role_guy")
async def role_guy(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ВІДКРИТИ ELITE APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])
    await callback.message.answer("Ви можете переглянути анкети в нашому Mini App. Щоб написати моделі, поповніть баланс у вкладці 'Гаманець'.", reply_markup=markup)
    await callback.answer()

# ПРИЙОМ СИГНАЛУ "Я ОПЛАТИВ" З MINI APP
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message, state: FSMContext):
    if message.web_app_data.data == "payment_requested":
        await message.answer(
            f"💳 **ЗАПИТ НА ПОПОВНЕННЯ**\n\nПерекажіть суму на карту:\n`{CARD_NUMBER}`\n\nПісля оплати **надішліть фото чека** одним повідомленням 👇",
            parse_mode="Markdown"
        )
        await state.set_state(Payment.waiting_for_receipt)

@dp.message(Payment.waiting_for_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    await message.answer("✅ Дякуємо! Чек надіслано адміністратору. Баланс буде оновлено після перевірки.")
    await bot.send_photo(
        ADMIN_ID, 
        photo=message.photo[-1].file_id, 
        caption=f"💰 **НОВИЙ ЧЕК**\nВід: @{message.from_user.username}\nID: `{message.from_user.id}`"
    )
    await state.clear()

# --- РЕЄСТРАЦІЯ ДІВЧИНИ ---
@dp.callback_query(F.data == "reg_girl")
async def start_reg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.name)
    await callback.message.answer("💃 Як тебе звати?")

@dp.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text); await state.set_state(Registration.age)
    await message.answer("Скільки тобі років?")

@dp.message(Registration.age)
async def reg_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text); await state.set_state(Registration.city)
    await message.answer("З якого ти міста?")

@dp.message(Registration.city)
async def reg_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text); await state.set_state(Registration.photo)
    await message.answer("Надішли своє найкраще фото 📸")

@dp.message(Registration.photo, F.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    try:
        await users_col.update_one({"user_id": user_id}, {"$set": {"status": "pending", **data}}, upsert=True)
        await message.answer("✅ Твоя анкета надіслана на модерацію!")
        
        admin_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"ok_{user_id}")],
            [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"no_{user_id}")]
        ])
        await bot.send_photo(
            ADMIN_ID, photo=message.photo[-1].file_id, 
            caption=f"👑 **НОВА МОДЕЛЬ**\n{data['name']}, {data['age']}\n📍 {data['city']}\nЮзер: @{message.from_user.username}",
            reply_markup=admin_markup
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Save error: {e}")
        await message.answer("❌ Помилка бази. Перевірте з'єднання!")

# --- АДМІН ДІЇ ---
@dp.callback_query(F.data.startswith("ok_"))
async def admin_ok(callback: CallbackQuery):
    uid = int(callback.data.split("_")[1])
    await users_col.update_one({"user_id": uid}, {"$set": {"status": "approved"}})
    await bot.send_message(uid, "🌟 Твою анкету схвалено! Тепер ти у списку моделей.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **СХВАЛЕНО**")

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery): 
    await cmd_start(callback.message); await callback.message.delete()

# --- ЗАПУСК ---
async def main():
    # skip_updates=True допомагає уникнути ConflictError при перезапуску
    await asyncio.gather(start_web_server(), dp.start_polling(bot, skip_updates=True))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинений")
