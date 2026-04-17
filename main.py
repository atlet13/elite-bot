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
crypto = CryptoPay(token=CRYPTO_TOKEN)

class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    photo = State()

# --- ФЕЙКОВИЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render автоматично надає порт через змінну оточення PORT
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ЛОГІКА БОТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "💎 **ELITEGIRLS PREMIUM SERVICE** 💎\n\n"
        "Вітаємо у найексклюзивнішій спільноті! Ми поєднали преміальний сервіс, "
        "конфіденційність та найкращий контент.\n\n"
        "📍 **Що ви можете зробити зараз:**\n"
        "• Переглянути анкетну базу в нашому додатку\n"
        "• Поповнити баланс Diamonds для доступу до VIP-функцій\n"
        "• Зареєструватися як модель та стати частиною команди\n\n"
        "✨ *Обирайте потрібний розділ нижче:* "
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

@dp.callback_query(F.data == "top_up_menu")
async def top_up_menu(callback: CallbackQuery):
    text = "💳 **Оберіть зручний спосіб поповнення:**"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Україна (UAH Card)", callback_data="region_uah")],
        [InlineKeyboardButton(text="🌍 International (Crypto)", callback_data="region_crypto")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_caption(caption=text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "region_uah")
async def uah_menu(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 100 💎 — 100 грн", callback_data="buy_uah_100")],
        [InlineKeyboardButton(text="💎 500 💎 — 450 грн", callback_data="buy_uah_450")],
        [InlineKeyboardButton(text="💎 1000 💎 — 800 грн", callback_data="buy_uah_800")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up_menu")]
    ])
    await callback.message.edit_caption(caption="🇺🇦 **Оберіть пакет поповнення (UAH):**", reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_uah_"))
async def process_uah(callback: CallbackQuery):
    amount = callback.data.split("_")[2]
    pay_url = f"{UAH_BANK_URL}?amount={amount}"
    text = f"📍 **Пакет: {amount} грн**\n\n1. Сплатіть за кнопкою.\n2. Надішліть чек сюди."
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Сплатити {amount} грн", url=pay_url)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="region_uah")]
    ])
    await callback.message.edit_caption(caption=text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "region_crypto")
async def crypto_menu(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 100 💎 — 3 USDT", callback_data="buy_crypto_3")],
        [InlineKeyboardButton(text="💎 500 💎 — 12 USDT", callback_data="buy_crypto_12")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up_menu")]
    ])
    await callback.message.edit_caption(caption="🌍 **Select Crypto Package (USDT):**", reply_markup=markup)

@dp.callback_query(F.data.startswith("buy_crypto_"))
async def process_crypto(callback: CallbackQuery):
    usd_val = int(callback.data.split("_")[2])
    invoice = await crypto.create_invoice(asset='USDT', amount=usd_val)
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Pay with CryptoBot", url=invoice.pay_url)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="region_crypto")]
    ])
    await callback.message.answer(f"💎 **Рахунок на {usd_val} USDT створено!**", reply_markup=markup)

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
    await message.answer("✅ **Анкету відправлено!**\nАдміністратор перевірить дані.")
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"adm_girl_ok_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"adm_girl_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, photo=photo_id, caption=f"👑 **НОВА АНКЕТА**\n👤: {data['name']}, {data['age']}\n📍: {data['city']}\n🔗: @{message.from_user.username}", reply_markup=admin_markup)
    await state.clear()

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if message.from_user.id == ADMIN_ID: return
    await message.answer("✅ Чек отримано! Очікуйте підтвердження.")
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"pay_ok_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"pay_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, photo=message.photo[-1].file_id, caption=f"💰 Чек від @{message.from_user.username}", reply_markup=admin_markup)

@dp.callback_query(F.data.startswith(("pay_ok_", "pay_no_", "adm_girl_ok_", "adm_girl_no_")))
async def admin_decision(callback: CallbackQuery):
    action = callback.data
    user_id = action.split("_")[-1]
    if "pay_ok" in action: await bot.send_message(user_id, "🎉 Оплата підтверджена!")
    elif "pay_no" in action: await bot.send_message(user_id, "❌ Оплату відхилено.")
    elif "girl_ok" in action: await bot.send_message(user_id, "🌟 Анкету схвалено!")
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await cmd_start(callback.message)
    await callback.message.delete()

# --- ЗАПУСК ---
async def main():
    # Запускаємо фейковий сервер і бота одночасно
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot, skip_updates=True)
    )

if __name__ == '__main__':
    asyncio.run(main())
