import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- НАЛАШТУВАННЯ ---
API_TOKEN = "8703162686:AAG_uYV01qHTsm4EhB1m5MDEgeRfUyesgac"
ADMIN_ID = 8561782680  # Твій ID
WEB_APP_URL = "https://atlet13.github.io/elite-app/"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Тимчасова база (у пам'яті)
db_models = {} 

class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_photo = State()

# --- СТАРТ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🙋‍♂️ Я хлопець", callback_data="gender_male")],
        [InlineKeyboardButton(text="🙋‍♀️ Я дівчина", callback_data="gender_female")]
    ])
    await message.answer("Вітаємо в ELITEGIRLS 💎\nОберіть вашу роль для входу в систему:", reply_markup=markup, parse_mode="Markdown")

# --- АДМІН ПАНЕЛЬ ---
@dp.message(Command("admin"))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    total = len(db_models)
    text = f"📊 **СТАТИСТИКА ELITEGIRLS**\n\nМоделей у базі: {total}\n"
    for m_id, data in db_models.items():
        text += f"• ID: {m_id} | {data['name']} | 0.00 💎\n"
    await message.answer(text, parse_mode="Markdown")

# --- ГІЛКА ХЛОПЦЯ ---
@dp.callback_query(F.data == "gender_male")
async def process_male(callback: types.Callback_query):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 УВІЙТИ В ДОДАТОК", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await callback.message.edit_text("Твій статус: Клієнт ✅\nДоступ до анкети дівчат відкритий.", reply_markup=markup, parse_mode="Markdown")

# --- ГІЛКА ДІВЧИНИ ---
@dp.callback_query(F.data == "gender_female")
async def process_female(callback: types.Callback_query, state: FSMContext):
    await state.set_state(Form.waiting_for_name)
    await callback.message.edit_text("Починаємо реєстрацію моделі.\n\nВведіть ваше ім'я та вік:")

@dp.message(Form.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.waiting_for_photo)
    await message.answer("Надішліть ваше найкраще фото для профілю:")

@dp.message(Form.waiting_for_photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    girl_id = message.from_user.id
    db_models[girl_id] = {"name": data['name']}
    
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написати їй", url=f"tg://user?id={girl_id}")],
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"approve_{girl_id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"decline_{girl_id}")]
    ])
    
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"⚡️ **НОВА ЗАЯВКА**\n\nІм'я: {data['name']}\nID: `{girl_id}`", 
                         reply_markup=admin_markup, parse_mode="Markdown")
    await state.clear()
    await message.answer("Заявка прийнята! Очікуйте повідомлення про схвалення від адміністратора.")

# --- СХВАЛЕННЯ ---
@dp.callback_query(F.data.startswith("approve_"))
async def approve_girl(callback: types.Callback_query):
    girl_id = int(callback.data.split("_")[1])
    rules = (
        "**ВІТАЄМО В ELITEGIRLS!** 💎\n\n"
        "Вас схвалено! Ваші умови:\n"
        "📍 Виплата: 75% від чатів/дзвінків.\n"
        "📍 Виплати щопонеділка на USDT/Карту.\n\n"
        "**ВЕРИФІКАЦІЯ:** Надішліть фото з папірцем:\n"
        f"`ELITEGIRLS | ID: {girl_id} | {callback.message.date.strftime('%d.%m.%Y')}`\n\n"
        "Після цього ваш профіль з'явиться у загальному FEED."
    )
    await bot.send_message(girl_id, rules, parse_mode="Markdown")
    await callback.message.
[17.04.2026 3:35] Lina✨: edit_caption(caption=callback.message.caption + "\n\n✅ СХВАЛЕНО")

async def main():
    await dp.start_polling(bot)

if name == '__main__':
    asyncio.run(main())
