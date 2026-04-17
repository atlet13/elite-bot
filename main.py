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

# Логування для відстеження помилок у Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = "8703162686:AAHmab2F_7W54X0g30wv5MAbgtRYdlpynAg"
ADMIN_ID = 8561782680 
SUPPORT_USERNAME = "elitegirls_support"
WEB_APP_URL = "https://atlet13.github.io/elite-app/"
CARD_NUMBER = "4400005552741933"

# ПІДКЛЮЧЕННЯ ДО MONGODB (Змініть пароль EliteApp2026 на свій!)
MONGO_URL = "mongodb+srv://admin:Artyr2625@cluster0.tp0nxdu.mongodb.net/?retryWrites=true&w=majority"

try:
    cluster = AsyncIOMotorClient(MONGO_URL)
    db = cluster["elite_db"]
    users_col = db["users"]
    logger.info("Спроба підключення до бази даних...")
except Exception as e:
    logger.error(f"Критична помилка бази: {e}")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# СТАННИ ДЛЯ АНКЕТИ ТА ОПЛАТИ
class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    bio = State()
    photo = State()

class Payment(StatesGroup):
    waiting_for_receipt = State()

# --- ВЕБ-СЕРВЕР (ЩОБ RENDER НЕ ВИМИКАВ БОТА) ---
async def handle(request):
    return web.Response(text="EliteGirls Bot is running smoothly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ГОЛОВНЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "💎 **ELITEGIRLS PREMIUM** 💎\n\n"
        "Вітаємо! Оберіть вашу роль для входу на платформу:"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕺 Я — Хлопець (Вхід)", callback_data="role_guy")],
        [InlineKeyboardButton(text="💃 Я — Дівчина (Реєстрація)", callback_data="reg_girl")],
        [InlineKeyboardButton(text="🆘 Тех. Підтримка", callback_data="support_info")]
    ])
    await message.answer(text, reply_markup=markup, parse_mode="Markdown")

# --- ЛОГІКА ХЛОПЦЯ ТА ОПЛАТА З MINI APP ---
@dp.callback_query(F.data == "role_guy")
async def role_guy(callback: CallbackQuery):
    text = (
        "🕺 **Вітаємо в додатку!**\n\n"
        "Ви можете переглядати анкети безкоштовно. "
        "Для оплати за функціонал використовуйте кнопку поповнення всередині Mini App."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ВІДКРИТИ ELITE APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

# Це спрацює, коли користувач натисне "Поповнити" у вашому вікні Mini App
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message, state: FSMContext):
    if message.web_app_data.data == "payment_requested":
        text = (
            "💳 **ЗАПИТ НА ОПЛАТУ**\n\n"
            f"Реквізити нашої карти:\n`{CARD_NUMBER}`\n\n"
            "Будь ласка, перекажіть суму та **надішліть скріншот чека** нижче 👇"
        )
        await message.answer(text, parse_mode="Markdown")
        await state.set_state(Payment.waiting_for_receipt)

@dp.message(Payment.waiting_for_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    await message.answer("✅ Чек отримано! Модератор перевірить оплату та оновить баланс у додатку.")
    await bot.send_photo(
        ADMIN_ID, 
        photo=message.photo[-1].file_id, 
        caption=f"💰 **НОВИЙ ЧЕК**\nКористувач: @{message.from_user.username}\nID: `{message.from_user.id}`",
        parse_mode="Markdown"
    )
    await state.clear()

# --- РЕЄСТРАЦІЯ ДІВЧИНИ ---
@dp.callback_query(F.data == "reg_girl")
async def start_reg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.name)
    await callback.message.answer("💃 Як тебе звати?")
    await callback.answer()

@dp.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text); await state.set_state(Registration.age)
    await message.answer("Твій вік?")

@dp.message(Registration.age)
async def reg_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text); await state.set_state(Registration.city)
    await message.answer("З якого ти міста?")

@dp.message(Registration.city)
async def reg_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text); await state.set_state(Registration.bio)
    await message.answer("✨ Напиши опис про себе (параметри, інтереси):")

@dp.message(Registration.bio)
async def reg_bio(message: types.Message, state: FSMContext):
    await state.update_data(bio=message.text); await state.set_state(Registration.photo)
    await message.answer("Надішли своє фото 📸")

@dp.message(Registration.photo, F.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    
    try:
        # ЗАПИС У БАЗУ (Виправляє "зависання")
        await users_col.update_one(
            {"user_id": user_id},
            {"$set": {"name": data['name'], "age": data['age'], "city": data['city'], "bio": data['bio'], "status": "pending"}},
            upsert=True
        )
        
        await message.answer("✅ Анкета надіслана! Очікуйте схвалення від адміністратора.")
        
        admin_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"approve_{user_id}")],
            [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"decline_{user_id}")]
        ])
        
        caption = f"👑 **НОВА МОДЕЛЬ**\n\n👤 {data['name']}, {data['age']}\n📍 {data['city']}\n📝 {data['bio']}\n🔗 @{message.from_user.username}"
        await bot.send_photo(ADMIN_ID, photo=photo_id, caption=caption, reply_markup=admin_markup)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        await message.answer(f"❌ Помилка бази даних: {e}. Перевірте Network Access та пароль у MongoDB!")

# --- АДМІНКА ---
@dp.callback_query(F.data.startswith("approve_"))
async def admin_approve(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await users_col.update_one({"user_id": user_id}, {"$set": {"status": "approved"}})
    await bot.send_message(user_id, "🌟 Вітаємо! Твою анкету схвалено. Робочий кабінет у Mini App активовано.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **СХВАЛЕНО**")

# --- ДОПОМІЖНІ КОМАНДИ ---
@dp.callback_query(F.data == "support_info")
async def support(callback: CallbackQuery):
    await callback.message.answer(f"🆘 З усіх питань пишіть: @{SUPPORT_USERNAME}")

@dp.callback_query(F.data == "back_to_main")
async def back(callback: CallbackQuery):
    await cmd_start(callback.message); await callback.message.delete()

async def main():
    await asyncio.gather(start_web_server(), dp.start_polling(bot, skip_updates=True))

if __name__ == '__main__':
    asyncio.run(main())
