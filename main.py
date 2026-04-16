import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Змінні
API_TOKEN = "8703162686:AAG_uYVO1qHTsm4EhB1m5MDEgeRfUyesgac"
WEB_APP_URL = "https://atlet13.github.io/elite-app/"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 УВІЙТИ В ELITEGIRLS 💎", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    welcome_text = (
        "✨ Ласкаво просимо до EliteGirls ✨\n\n"
        "Твій ексклюзивний простір для спілкування.\n\n"
        "💎 Для гостей: Тільки перевірені профілі.\n"
        "💸 Для моделей: Вивід від $50.\n\n"
        "Натисни кнопку нижче, щоб відкрити каталог."
    )
    
    await message.answer(welcome_text, reply_markup=markup, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
