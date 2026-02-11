import asyncio
import os  # noqa: INP001
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

HELLO_IMG_PATH = BASE_DIR / "valentine_day/static/valentine_day/img/main.png"
API_KEY = os.environ["VALENTINE_BOT_API_KEY"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _ = context
    """Обработчик команды /start."""
    if update.message is None:
        return
    # URL вашего Mini App (замените на реальный)
    web_app_url: str = "https://atl-asana.vim-store.ru/valentine-day/"
    welcome_text_1 = """
У тебя тоже что-то внезапно закололо в области груди сегодня? Отмена паники! Это все шалости Святого Валентина, ведь сегодня он традиционно расчехлил свой колчан и пронзил твое сердечко!💘

<tg-spoiler>Запись к кардиологу рекомендуем не отменять, чекап - тоже важно</tg-spoiler>

Джоэл считал, что 14 февраля - это праздник, который придумали компании, производящие поздравительные открытки, чтобы заставить людей чувствовать себя паршиво.

Мы же с ним не согласны категорически, и подготовили для тебя самые лучшие открытки для твоего друллеги, а ещё - этот бот, который поможет тебе признаться в твоей любви совершенно анонимно, без подписок, и смс 🥹

✨Анонимно.
✨ Без объяснений.
✨ Без «это я, если что», <tg-spoiler>но можно и с ним!</tg-spoiler>

С нас - картинка, с тебя - текст, дальше всю магию любви берет на себя бот 💌

Кто отправил? Один Валентин знает 😉
Кто получит? Вопросы тоже к тому парню с нимбом и стрелами!
Что дальше? Покажет ✨любовь✨

Заряжаем стрелу?

""".strip()

    instruction_text = """
<b>Как это сделать?</b>

❤️ Запусти приложение (кнопка Open или 'Отправить валентинку')

❤️ Выбери получателя

❤️ Подбери картинку и напиши текст

❤️Нажми «Сохранить»

Иногда любовь бывает переменчива…. Ты можешь отозвать свою валентинку - просто удалив ее 💔 

Или удалить сообщение и отправить новое - ты  сегодня Валентин и все в твоих руках 🙌🏻
""".strip()

    # Создание кнопки Mini App
    keyboard = [[InlineKeyboardButton(text="💌 Отправить валентинку", web_app=WebAppInfo(url=web_app_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    async with aiofiles.open(HELLO_IMG_PATH, "rb") as photo_file:
        photo_bytes: bytes = await photo_file.read()
        await update.message.reply_photo(
            photo=photo_bytes,
            caption=welcome_text_1,
            parse_mode="HTML",
        )
        await update.message.reply_text(
            text=instruction_text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _ = context
    if update.message and update.message.text:
        user_text: str = update.message.text
        if user_text == "ping":
            await update.message.reply_text(user_text)


async def test_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _ = context
    if update.message is None:
        return
    web_app_url: str = "https://atl-asana.vim-store.ru/"
    keyboard = [[InlineKeyboardButton(text="💌 Отправить валентинку", web_app=WebAppInfo(url=web_app_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="Test",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


def main() -> None:
    application = ApplicationBuilder().token(API_KEY).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test_link", test_link))
    application.add_handler(MessageHandler(filters.TEXT, echo))
    print("Бот запускает сервер вебхуков...")
    # application.run_polling()

    application.run_webhook(
        listen="0.0.0.0",
        port=8000,
        webhook_url="https://atl-valentine.vim-store.ru/",
    )


if __name__ == "__main__":
    main()
    print("Бот запущен...")
