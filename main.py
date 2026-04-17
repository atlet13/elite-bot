import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from motor.motor_asyncio import AsyncIOMotorClient

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = "8703162686:AAHmab2F_7W54X0g30wv5MAbgtRYdlpynAg"
ADMIN_ID = 8561782680 
SUPPORT_USERNAME = "elitegirls_support"
WEB_APP_URL = "https://atlet13.github.io/elite-app/"
START_PHOTO_URL = "https://i.ibb.co/cS1xSG0w/image.jpg" 
CARD_NUMBER = "4400005552741933"

# ПІДКЛЮЧЕННЯ ДО MONGODB
MONGO_URL = "mongodb+srv://admin:Artyr2626@cluster0.tp0nxdu.mongodb.net/?retryWrites=true&w=majority"
cluster = AsyncIOMotorClient(MONGO_URL)
db = cluster["elite_db"]
users_col = db["users"] # Колекція для збереження анкет та статусів

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# СТАННИ ДЛЯ РЕЄСТРАЦІЇ ТА ОПЛАТИ
class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    bio = State()
    photo = State()

class Payment(StatesGroup):
    waiting_for_receipt = State()

# --- ВЕБ-СЕРВЕР ДЛЯ ПІДТРИМКИ ЖИТТЄДІЯЛЬНОСТІ (RENDER) ---
async def handle(request):
    return web.Response(text="EliteGirls Bot is Active and Connected to Database!")

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
        "Вітаємо на платформі ексклюзивного контенту!\n"
        "Будь ласка, оберіть вашу роль для входу:"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕺 Я — Хлопець (Вхід)", callback_data="role_guy")],
        [InlineKeyboardButton(text="💃 Я — Дівчина (Реєстрація)", callback_data="reg_girl")],
        [InlineKeyboardButton(text="🆘 Тех. Підтримка", callback_data="support_info")]
    ])
    try:
        await message.answer_photo(photo=START_PHOTO_URL, caption=text, reply_markup=markup, parse_mode="Markdown")
    except:
        await message.answer(text, reply_markup=markup, parse_mode="Markdown")

# --- ЛОГІКА ДЛЯ ХЛОПЦЯ (ВХІД ТА ОПЛАТА) ---
@dp.callback_query(F.data == "role_guy")
async def role_guy(callback: CallbackQuery):
    text = (
        "🕺 **Вітаємо в Elite App!**\n\n"
        "Для перегляду контенту та спілкування відкрийте додаток.\n"
        "Щоб отримати преміум-доступ, поповніть баланс."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ВІДКРИТИ ELITE APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💳 Поповнити баланс (Карта)", callback_data="pay_card")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_caption(caption=text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "pay_card")
async def pay_card(callback: CallbackQuery, state: FSMContext):
    text = (
        "💳 **Оплата на карту**\n\n"
        f"Переведіть бажану суму на карту:\n`{CARD_NUMBER}`\n\n"
        "⚠️ **Обов'язково:** Після оплати надішліть сюди **скріншот чека**."
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await state.set_state(Payment.waiting_for_receipt)
    await callback.answer()

@dp.message(Payment.waiting_for_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    await message.answer("✅ Чек отримано! Модератор перевірить оплату протягом 15 хвилин.")
    
    # Повідомлення адміну з чеком
    await bot.send_photo(
        ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"💰 **НОВИЙ ЧЕК**\nВід: @{message.from_user.username}\nID: `{message.from_user.id}`",
        parse_mode="Markdown"
    )
    await state.clear()

# --- ЛОГІКА ДЛЯ ДІВЧИНИ (РЕЄСТРАЦІЯ) ---
@dp.callback_query(F.data == "reg_girl")
async def start_reg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.name)
    await callback.message.answer("💃 **Починаємо реєстрацію!**\nЯк тебе звати?")
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
    
    # Зберігаємо в базу зі статусом "pending"
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "name": data['name'], 
            "age": data['age'], 
            "city": data['city'], 
            "bio": data['bio'], 
            "status": "pending"
        }},
        upsert=True
    )
    
    await message.answer("✅ **Анкету відправлено!**\nОчікуйте на рішення адміністратора.")
    
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"decline_{user_id}")]
    ])
    
    caption = (
        f"👑 **НОВА МОДЕЛЬ**\n\n"
        f"👤 {data['name']}, {data['age']} р.\n"
        f"📍 Місто: {data['city']}\n"
        f"📝 Опис: {data['bio']}\n"
        f"🔗 Юзер: @{message.from_user.username}"
    )
    await bot.send_photo(ADMIN_ID, photo=photo_id, caption=caption, reply_markup=admin_markup)
    await state.clear()

# --- ЛОГІКА АДМІНА: ПІДТВЕРДЖЕННЯ ТА ІНСТРУКЦІЇ ---
@dp.callback_query(F.data.startswith("approve_"))
async def admin_approve(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    # Оновлюємо статус в MongoDB
    await users_col.update_one({"user_id": user_id}, {"$set": {"status": "approved"}})
    
    instruction = (
        "🌟 **ВІТАЄМО! ВАС ПРИЙНЯТО ДО ELITEGIRLS**\n\n"
        "Тепер ваш профіль доступний для користувачів.\n\n"
        "📍 **Умови роботи:**\n"
        "• Ви отримуєте 70% від усіх подарунків та платних чатів.\n"
        "• Виплати на карту щотижня.\n"
        "• Менеджер: @elitegirls_support\n\n"
        "Напишіть менеджеру, щоб отримати доступ до робочого чату."
    )
    
    await bot.send_message(user_id, instruction, parse_mode="Markdown")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **СТАТУС: СХВАЛЕНО (База оновлена)**")
    await callback.answer()

@dp.callback_query(F.data.startswith("decline_"))
async def admin_decline(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await users_col.update_one({"user_id": user_id}, {"$set": {"status": "declined"}})
    await bot.send_message(user_id, "❌ На жаль, вашу анкету було відхилено модератором.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **СТАТУС: ВІДХИЛЕНО**")
    await callback.answer()

# --- ДОПОМІЖНІ КНОПКИ ---
@dp.callback_query(F.data == "support_info")
async def support_info(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Написати менеджеру", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_caption(caption="🆘 **Підтримка**\nЗ усіх питань пишіть менеджеру.", reply_markup=markup)

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await cmd_start(callback.message); await callback.message.delete()

# --- ЗАПУСК ---
async def main():
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot, skip_updates=True)
    )

if __name__ == '__main__':
    asyncio.run(main())
