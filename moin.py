import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Змінні (Render попросить їх ввести в налаштуваннях)
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Кнопка для входу в Mini App
    webapp_btn = InlineKeyboardButton(
        text="💎 УВІЙТИ В ELITEGIRLS 💎", 
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    markup.add(webapp_btn)

    welcome_text = (
        "✨ Ласкаво просимо до EliteGirls ✨\n\n"
        "Твій ексклюзивний простір для спілкування з найкращими моделями.\n\n"
        "💎 Для гостей: Тільки перевірені профілі та приватні чати.\n"
        "💸 Для моделей: Отримуй 75% прибутку. Вивід від $50.\n\n"
        "Натисни кнопку нижче, щоб відкрити каталог."
    )
    
    await message.answer(welcome_text, reply_markup=markup, parse_mode="Markdown")

if name == '__main__':
    executor.start_polling(dp, skip_updates=True)
