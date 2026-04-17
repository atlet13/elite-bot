import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

# --- НАЛАШТУВАННЯ ---
# Встав сюди свіжий токен від @BotFather
API_TOKEN = "8703162686:AAHmab2F_7W54X0g30wv5MAbgtRYdlpynAg" 
ADMIN_ID = 8561782680
WEB_APP_URL = "https://atlet13.github.io/elite-app/"

# Логування
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
db_models = {}

class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_photo = State()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (щоб не було помилки Port Scan) ---
async def handle(request):
    return web.Response(text="EliteGirls Bot is Live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- ЛОГІКА БОТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🙋‍♂️ Я хлопець", callback_data="gender_male")],
        [InlineKeyboardButton(text="🙋‍♀️ Я дівчина", callback_data="gender_female")]
    ])
    await message.answer("Вітаємо в **ELITEGIRLS** 💎\nОберіть вашу роль для входу в систему:", reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "gender_male")
async def process_male(callback: CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 УВІЙТИ В ДОДАТОК", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await callback.message.edit_text("Твій доступ активовано! ✅", reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "gender_female")
async def process_female(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_name)
    await callback.message.edit_text("Починаємо реєстрацію.\n\nЯк тебе звати та скільки років?")

@dp.message(Form.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.waiting_for_photo)
    await message.answer("Надішли своє найкраще фото для анкети:")

@dp.message(Form.waiting_for_photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    girl_id = message.from_user.id
    db_models[girl_id] = {"name": data['name']}
    
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написати", url=f"tg://user?id={girl_id}")],
        [InlineKeyboardButton(text="✅ Схвалити", callback_data=f"approve_{girl_id}")]
    ])
    
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"⚡️ **НОВА ЗАЯВКА**\n\nІм'я: {data['name']}\nID: `{girl_id}`", 
                         reply_markup=admin_markup, parse_mode="Markdown")
    await state.clear()
    await message.answer("Заявку надіслано! Очікуйте повідомлення про схвалення.")

@dp.callback_query(F.data.startswith("approve_"))
async def approve_girl(callback: CallbackQuery):
    girl_id = int(callback.data.split("_")[1])
    rules = (
        "**ВІТАЄМО В ELITEGIRLS!** 💎\n\n"
        "Вас схвалено! Ваша ставка: **75%**.\n\n"
        "Для повної активації профілю надішліть фото з папірцем:\n"
        f"`ELITEGIRLS | ID: {girl_id}`"
    )
    await bot.send_message(girl_id, rules, parse_mode="Markdown")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ СХВАЛЕНО")

# --- ГОЛОВНИЙ ЗАПУСК ---
async def main():
    # Обов'язкове видалення вебхука для уникнення ConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск бота та веб-сервера одночасно
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Error: {e}")
