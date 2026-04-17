import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiocryptopay import AioCryptoPay as CryptoPay

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = "8703162686:AAHmab2F_7W54X0g30wv5MAbgtRYdlpynAg"
ADMIN_ID = 8561782680 
SUPPORT_USERNAME = "elitegirls_support"
WEB_APP_URL = "https://atlet13.github.io/elite-app/"
# Посилання на фото, яке ви надали
START_PHOTO_URL = "https://i.ibb.co/cS1xSG0w/image.jpg" 

# ПЛАТІЖНІ ДАНІ
UAH_BANK_URL = "https://pay.a-bank.com.ua/collection/V68yZ6q8B69Nm4A0"
CRYPTO_TOKEN = "568872:AAmFd8yJDVg0fd5QQMzJdIQhs8O4aNE5bqT"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
crypto_client = None 

class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    photo = State()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="EliteGirls Bot is Active!")

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
        "Платформа ексклюзивного контенту та преміальних знайомств.\n\n"
        "Оберіть хто ви, щоб продовжити:"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ВІДКРИТИ ELITE APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🕺 Я — Гість (Пошук)", callback_data="role_guest")],
        [InlineKeyboardButton(text="💃 Я — Модель (Реєстрація)", callback_data="reg_girl")],
        [InlineKeyboardButton(text="🆘 Тех. Підтримка", callback_data="support_info")]
    ])
    try:
        await message.answer_photo(photo=START_PHOTO_URL, caption=text, reply_markup=markup, parse_mode="Markdown")
    except:
        await message.answer(text, reply_markup=markup, parse_mode="Markdown")

# --- ПІДТРИМКА ---
@dp.callback_query(F.data == "support_info")
async def support_info(callback: CallbackQuery):
    text = (
        "🆘 **Служба підтримки ELITEGIRLS**\n\n"
        "Маєте питання щодо роботи сервісу?\n"
        "Натисніть нижче, щоб написати менеджеру."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Написати менеджеру", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_caption(caption=text, reply_markup=markup, parse_mode="Markdown")

# --- РОЗДІЛ ГІСТЬ ТА ОПЛАТА ---
@dp.callback_query(F.data == "role_guest")
async def role_guest(callback: CallbackQuery):
    text = "Вітаємо, Гість! Тут ви можете переглянути контент або поповнити баланс для доступу."
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Перейти до додатку", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💎 Поповнити баланс", callback_data="top_up_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_caption(caption=text, reply_markup=markup)

@dp.callback_query(F.data == "top_up_menu")
async def top_up_menu(callback: CallbackQuery):
    text = "💳 **Оберіть зручний спосіб поповнення:**"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 UAH Card (A-Bank)", url=UAH_BANK_URL)],
        [InlineKeyboardButton(text="🌍 Crypto (USDT)", callback_data="pay_crypto_select")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="role_guest")]
    ])
    await callback.message.edit_caption(caption=text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "pay_crypto_select")
async def pay_crypto_select(callback: CallbackQuery):
    text = "🌍 **Crypto Payment**\nОберіть суму для створення рахунку:"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 100 — 3 USDT", callback_data="buy_crypto_3")],
        [InlineKeyboardButton(text="💎 500 — 12 USDT", callback_data="buy_crypto_12")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up_menu")]
    ])
    await callback.message.edit_caption(caption=text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_crypto_"))
async def process_crypto(callback: CallbackQuery):
    usd_val = int(callback.data.split("_")[2])
    invoice = await crypto_client.create_invoice(asset='USDT', amount=usd_val)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Сплатити", url=invoice.pay_url)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="pay_crypto_select")]
    ])
    await callback.message.answer(f"💎 Рахунок на {usd_val} USDT створено!", reply_markup=markup)

# --- РЕЄСТРАЦІЯ ---
@dp.callback_query(F.data == "reg_girl")
async def start_reg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.name)
    await callback.message.answer("💃 **Починаємо реєстрацію!**\nЯк тебе звати?")
    await callback.answer()

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
    await message.answer("Надішли фото для анкети 📸")

@dp.message(Registration.photo, F.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    
    await message.answer("✅ **Анкету відправлено!** Очікуйте на рішення адміністратора.")
    
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"decline_{user_id}")]
    ])
    
    await bot.send_photo(
        ADMIN_ID, 
        photo=photo_id, 
        caption=f"👑 **НОВА АНКЕТА**\n👤 {data['name']}, {data['age']}\n📍 {data['city']}\n🔗 @{message.from_user.username}",
        reply_markup=admin_markup
    )
    await state.clear()

# --- ЛОГІКА АДМІНІСТРАТОРА ---
@dp.callback_query(F.data.startswith("approve_"))
async def admin_approve(callback: CallbackQuery):
    user_id = callback.data.split("_")[1]
    await bot.send_message(user_id, "🌟 **Вітаємо! Вашу анкету схвалено.**\nВаш профіль тепер доступний у додатку!")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **СТАТУС: СХВАЛЕНО**")
    await callback.answer()

@dp.callback_query(F.data.startswith("decline_"))
async def admin_decline(callback: CallbackQuery):
    user_id = callback.data.split("_")[1]
    await bot.send_message(user_id, "❌ На жаль, вашу анкету було відхилено модератором.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **СТАТУС: ВІДХИЛЕНО**")
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await cmd_start(callback.message); await callback.message.delete()

# --- ЗАПУСК ---
async def main():
    global crypto_client
    # Виправлено помилку event loop: ініціалізація всередині main
    crypto_client = CryptoPay(token=CRYPTO_TOKEN)
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot, skip_updates=True)
    )

if __name__ == '__main__':
    asyncio.run(main())
