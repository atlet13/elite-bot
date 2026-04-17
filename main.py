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
WEB_APP_URL = "https://atlet13.github.io/elite-app/"
START_PHOTO_URL = "https://i.imgur.com/8P5n5p8.jpeg" 

# ПЛАТІЖНІ ДАНІ
UAH_BANK_URL = "https://pay.a-bank.com.ua/collection/V68yZ6q8B69Nm4A0"
CRYPTO_TOKEN = "568872:AAmFd8yJDVg0fd5QQMzJdIQhs8O4aNE5bqT"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
crypto_client = None  # Буде створено всередині main()

class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    photo = State()

# --- ВЕБ-СЕРВЕР ДЛЯ ОБХОДУ ОБМЕЖЕНЬ RENDER ---
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
        "Оберіть потрібний розділ нижче:"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ВІДКРИТИ ELITE APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💎 Поповнити баланс", callback_data="top_up_menu")],
        [InlineKeyboardButton(text="💃 Реєстрація (для дівчат)", callback_data="reg_girl")]
    ])
    try:
        await message.answer_photo(photo=START_PHOTO_URL, caption=text, reply_markup=markup, parse_mode="Markdown")
    except:
        await message.answer(text, reply_markup=markup, parse_mode="Markdown")

# --- МЕНЮ ОПЛАТИ ---
@dp.callback_query(F.data == "top_up_menu")
async def top_up_menu(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 UAH Card", callback_data="region_uah")],
        [InlineKeyboardButton(text="🌍 Crypto (USDT)", callback_data="region_crypto")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_caption(caption="💳 Оберіть зручний спосіб поповнення:", reply_markup=markup)

@dp.callback_query(F.data == "region_crypto")
async def crypto_menu(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 100 — 3 USDT", callback_data="buy_crypto_3")],
        [InlineKeyboardButton(text="💎 500 — 12 USDT", callback_data="buy_crypto_12")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up_menu")]
    ])
    await callback.message.edit_caption(caption="🌍 **Crypto Payment:**", reply_markup=markup)

@dp.callback_query(F.data.startswith("buy_crypto_"))
async def process_crypto(callback: CallbackQuery):
    usd_val = int(callback.data.split("_")[2])
    invoice = await crypto_client.create_invoice(asset='USDT', amount=usd_val)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Сплатити в CryptoBot", url=invoice.pay_url)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="region_crypto")]
    ])
    await callback.message.answer(f"💎 Рахунок на {usd_val} USDT створено!", reply_markup=markup)

# --- РЕЄСТРАЦІЯ ДІВЧАТ ---
@dp.callback_query(F.data == "reg_girl")
async def start_reg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.name)
    await callback.message.answer("💃 **Починаємо реєстрацію!**\nЯк тебе звати?")
    await callback.answer()

@dp.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.age)
    await message.answer("Скільки тобі років?")

@dp.message(Registration.age)
async def reg_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Registration.city)
    await message.answer("З якого ти міста?")

@dp.message(Registration.city)
async def reg_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Registration.photo)
    await message.answer("Надішли своє найкраще фото для анкети 📸")

@dp.message(Registration.photo, F.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    await message.answer("✅ **Анкету відправлено!**\nАдміністратор перевірить дані найближчим часом.")
    
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"adm_girl_ok_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"adm_girl_no_{message.from_user.id}")]
    ])
    await bot.send_photo(
        ADMIN_ID, 
        photo=photo_id, 
        caption=f"👑 **НОВА АНКЕТА**\n\n👤 Ім'я: {data['name']}\n🔞 Вік: {data['age']}\n📍 Місто: {data['city']}\n🔗 Юзер: @{message.from_user.username}",
        reply_markup=admin_markup
    )
    await state.clear()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await cmd_start(callback.message)
    await callback.message.delete()

# --- ЗАПУСК ---
async def main():
    global crypto_client
    # Важливо: ініціалізація CryptoPay ТУТ
    crypto_client = CryptoPay(token=CRYPTO_TOKEN)
    
    # Запускаємо веб-сервер та бота паралельно
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot, skip_updates=True)
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
