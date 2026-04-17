import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiocryptopay import CryptoPay

# --- КОНФІГУРАЦІЯ ---
API_TOKEN = "8703162686:AAG_uYV01qHTsm4EhB1m5MDEgeRfUyesgac"
ADMIN_ID = 8561782680
WEB_APP_URL = "https://atlet13.github.io/elite-app/"

# ПЛАТІЖНІ ДАНІ
UAH_BANK_URL = "https://pay.a-bank.com.ua/collection/V68yZ6q8B69Nm4A0"
CRYPTO_TOKEN = "568872:AAmFd8yJDVg0fd5QQMzJdIQhs8O4aNE5bqT"

# ІНІЦІАЛІЗАЦІЯ
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
crypto = CryptoPay(token=CRYPTO_TOKEN)

# --- СТАНИ ДЛЯ РЕЄСТРАЦІЇ ДІВЧАТ ---
class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    photo = State()

# --- ГОЛОВНЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "✨ **Вітаємо в ELITEGIRLS**\n\n"
        "Платформа ексклюзивного контенту та преміальних знайомств.\n"
        "Оберіть потрібний розділ нижче:"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ВІДКРИТИ ELITE APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💎 Поповнити баланс", callback_data="top_up_menu")],
        [InlineKeyboardButton(text="💃 Реєстрація (для дівчат)", callback_data="reg_girl")]
    ])
    await message.answer(text, reply_markup=markup, parse_mode="Markdown")

# --- МЕНЮ ПОПОВНЕННЯ (ВИБІР РЕГІОНУ) ---
@dp.callback_query(F.data == "top_up_menu")
async def top_up_menu(callback: CallbackQuery):
    text = "💳 **Оберіть спосіб оплати:**"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇦 Україна (UAH Card)", callback_data="region_uah")],
        [InlineKeyboardButton(text="🌍 International (Crypto)", callback_data="region_crypto")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

# --- УКРАЇНА (А-БАНК) ---
@dp.callback_query(F.data == "region_uah")
async def uah_menu(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 100 💎 — 100 грн", callback_data="buy_uah_100")],
        [InlineKeyboardButton(text="💎 500 💎 — 450 грн", callback_data="buy_uah_450")],
        [InlineKeyboardButton(text="💎 1000 💎 — 800 грн", callback_data="buy_uah_800")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up_menu")]
    ])
    await callback.message.edit_text("🇺🇦 **Оберіть пакет (UAH):**", reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_uah_"))
async def process_uah(callback: CallbackQuery):
    amount = callback.data.split("_")[2]
    pay_url = f"{UAH_BANK_URL}?amount={amount}"
    
    text = (
        f"📍 **Оплата пакету: {amount} грн**\n\n"
        "1. Натисніть кнопку оплати.\n"
        "2. Зробіть переказ у додатку банку.\n"
        "3. **Надішліть скріншот чека** у цей чат.\n\n"
        "💎 Зарахування після перевірки адміном."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Сплатити {amount} грн", url=pay_url)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="region_uah")]
    ])
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

# --- КРИПТО (CRYPTO BOT) ---
@dp.callback_query(F.data == "region_crypto")
async def crypto_menu(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 100 💎 — 3 USDT", callback_data="buy_crypto_3")],
        [InlineKeyboardButton(text="💎 500 💎 — 12 USDT", callback_data="buy_crypto_12")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="top_up_menu")]
    ])
    await callback.message.edit_text("🌍 **Select Crypto Package:**", reply_markup=markup)

@dp.callback_query(F.data.startswith("buy_crypto_"))
async def process_crypto(callback: CallbackQuery):
    usd_val = int(callback.data.split("_")[2])
    invoice = await crypto.create_invoice(asset='USDT', amount=usd_val)
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Pay in Crypto Bot", url=invoice.pay_url)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="region_crypto")]
    ])
    await callback.message.answer(f"💎 **Рахунок на {usd_val} USDT створено!**", reply_markup=markup)

# --- РЕЄСТРАЦІЯ ДІВЧАТ (АНКЕТА) ---
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
    
    await message.answer("✅ **Анкету відправлено на модерацію!**\nМи перевіримо твій профіль найближчим часом.")
    
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

# --- ОБРОБКА ЧЕКІВ ТА АДМІН-ДІЇ ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if message.from_user.id == ADMIN_ID: return
    
    await message.answer("✅ Чек отримано! Очікуйте нарахування 💎")
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"pay_ok_{message.from_user.id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"pay_no_{message.from_user.id}")]
    ])
    await bot.send_photo(ADMIN_ID, photo=message.photo[-1].file_id, 
                         caption=f"💰 Чек від @{message.from_user.username}", reply_markup=admin_markup)

@dp.callback_query(F.data.startswith(("pay_ok_", "pay_no_", "adm_girl_ok_", "adm_girl_no_")))
async def admin_decision(callback: CallbackQuery):
    action = callback.data
    user_id = action.split("_")[-1]
    
    if "pay_ok" in action:
        await bot.send_message(user_id, "🎉 **Оплата підтверджена!** Діаманти додано.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ ОПЛАЧЕНО")
    elif "pay_no" in action:
        await bot.send_message(user_id, "❌ **Оплата відхилена.** Перевірте дані.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ ВІДХИЛЕНО")
    elif "girl_ok" in action:
        await bot.send_message(user_id, "🌟 **Твою анкету схвалено!** Тепер ти в EliteGirls.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ АНКЕТА СХВАЛЕНА")
    
    await callback.answer()

# --- ПОВЕРНЕННЯ ДО ГОЛОВНОГО ---
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await cmd_start(callback.message)
    await callback.message.delete()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
