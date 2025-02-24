import asyncio
import logging

import redis
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import config

API_TOKEN = config.API_TOKEN

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("project_logs.log"),
        logging.StreamHandler()
    ]    
)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
redis_client = redis.Redis("redis")


# Змінні зберігають основні ключові слова та додаткові тексти
global_keywords = set(["cat", "dog"])  # Приклад початкових слів
global_additional_text = ""

# Глобальна змінна для керування вашим парсером
crawler = None


# ---- Оголошення станів ----
class AddKeywordState(StatesGroup):
    waiting_for_keyword = State()

class RemoveKeywordState(StatesGroup):
    waiting_for_keyword = State()

class AddAdditionalTextState(StatesGroup):
    waiting_for_text = State()


# ---- Клавіатури ----
kb_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Keywords"), KeyboardButton(text="Additional text")],
        [KeyboardButton(text="Start Search"), KeyboardButton(text="Stop Search")],
    ],
    resize_keyboard=True,
)

# Інлайн-клавіатура для керування списком keywords
inline_kb_keywords = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Add", callback_data="add_keyword"),
            InlineKeyboardButton(text="Remove", callback_data="remove_keyword"),
        ]
    ]
)

# Інлайн-клавіатура для керування списком додаткового тексту
inline_kb_additional_text = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Add", callback_data="add_text"),
            InlineKeyboardButton(text="Remove", callback_data="remove_text"),
        ]
    ]
)


# ---- Хендлери на запуск і завершення бота ----
@dp.startup()
async def on_startup():
    logger.info("Bot is starting up...")

@dp.shutdown()
async def on_shutdown():
    logger.info("Bot is shutting down...")


# ---- Старт / Головне меню ----
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Виводить привітання і головну клавіатуру.
    """
    await message.answer(
        text=(
            "Hello! This is an image search bot.\n\n"
            "Use the menu below:\n"
            "1) Keywords - перегляд та зміна ключових слів\n"
            "2) Additional text - перегляд та зміна додаткових текстів\n"
            "3) Start Search - запуск пошуку\n"
            "4) Stop Search - зупинка пошуку"
        ),
        reply_markup=kb_main,
    )


# ---- Керування Keywords (натискається кнопка "Keywords") ----
@dp.message(F.text.lower() == "keywords")
async def show_keywords(message: Message):
    """
    Показати поточні keywords та інлайн-клавіатуру для додавання/видалення.
    """
    if not global_keywords:
        await message.answer(
            "There are no keywords.",
            reply_markup=inline_kb_keywords
        )
    else:
        text = ", ".join(sorted(global_keywords))
        await message.answer(
            f"Current keywords:\n<b>{text}</b>",
            reply_markup=inline_kb_keywords,
            parse_mode="html"
        )


@dp.callback_query(F.data == "add_keyword")
async def callback_add_keyword(callback: CallbackQuery, state: FSMContext):
    """
    Запитуємо в користувача ключове слово для додавання.
    """
    await callback.message.answer("Enter a keyword to add:")
    await state.set_state(AddKeywordState.waiting_for_keyword)


@dp.callback_query(F.data == "remove_keyword")
async def callback_remove_keyword(callback: CallbackQuery, state: FSMContext):
    """
    Запитуємо в користувача ключове слово для видалення.
    """
    await callback.message.answer("Enter a keyword to remove:")
    await state.set_state(RemoveKeywordState.waiting_for_keyword)


@dp.message(AddKeywordState.waiting_for_keyword)
async def process_add_keyword(message: Message, state: FSMContext):
    """
    Обробка введеного ключового слова для додавання.
    """
    word = message.text.strip().lower()
    if word in global_keywords:
        await message.answer(
            f"Keyword <b>{word}</b> already in the list.",
            parse_mode="html",
            reply_markup=kb_main
        )
    else:
        global_keywords.add(word)
        await message.answer(
            f"Added <b>{word}</b> to the keywords list.",
            parse_mode="html",
            reply_markup=kb_main
        )

    await state.clear()


@dp.message(RemoveKeywordState.waiting_for_keyword)
async def process_remove_keyword(message: Message, state: FSMContext):
    """
    Обробка введеного ключового слова для видалення.
    """
    word = message.text.strip().lower()
    if word in global_keywords:
        global_keywords.remove(word)
        await message.answer(
            f"Removed <b>{word}</b> from the keywords list.",
            parse_mode="html",
            reply_markup=kb_main
        )
    else:
        await message.answer(
            f"Keyword <b>{word}</b> not found in the list.",
            parse_mode="html",
            reply_markup=kb_main
        )

    await state.clear()


@dp.message(F.text.lower() == "additional text")
async def show_additional_text(message: Message):
    """
    Показати поточний додатковий текст та інлайн-клавіатуру для додавання/видалення.
    """
    if not global_additional_text:
        await message.answer(
            "No additional text added.",
            reply_markup=inline_kb_additional_text
        )
    else:
        await message.answer(
            f"Current additional text:\n<b>{global_additional_text}</b>",
            reply_markup=inline_kb_additional_text,
            parse_mode="html"
        )


@dp.callback_query(F.data == "add_text")
async def callback_add_text(callback: CallbackQuery, state: FSMContext):
    """
    Запитуємо у користувача рядок, який треба додати до додаткових текстів.
    """
    await callback.message.answer("Enter an additional text to add:")
    await state.set_state(AddAdditionalTextState.waiting_for_text)


@dp.callback_query(F.data == "remove_text")
async def callback_remove_text(callback: CallbackQuery):
    """
    Видаляємо additional text.
    """
    global global_additional_text
    global_additional_text = ""
    
    await callback.message.answer(
        "Removed additional text.",
        parse_mode="html",
        reply_markup=kb_main
    )


@dp.message(AddAdditionalTextState.waiting_for_text)
async def process_add_text(message: Message, state: FSMContext):
    """
    Обробка введеного рядка для додавання в додаткові тексти.
    """
    global global_additional_text
    
    text_item = message.text.strip().lower()
    if text_item == global_additional_text:
        await message.answer(
            f"Text <b>{text_item}</b> already in the list.",
            parse_mode="html",
            reply_markup=kb_main
        )
    else:
        global_additional_text = text_item
        await message.answer(
            f"Added <b>{text_item}</b> as the additional text.",
            parse_mode="html",
            reply_markup=kb_main
        )

    await state.clear()


# ---- Запуск та зупинка пошуку ----
@dp.message(F.text.lower() == "start search")
async def start_search_button(message: Message):
    """
    Запуск парсера з наявним списком keywords і additional text.
    """
    global crawler

    if not global_keywords:
        await message.answer(
            "There are no keywords. You should add some first.",
            reply_markup=kb_main,
            parse_mode="html",
        )
        return

    # Якщо crawler вже запущений - зупиняємо його перед повторним запуском
    if crawler is not None:
        crawler.stop_parsing()
        crawler = None
    
    keywords_list = list(global_keywords)

    # Запускаємо власний парсер (Crawler), підставте свій імпорт/код
    from crawler import Crawler  # Можна винести вгору, залежно від вашої структури
    crawler = Crawler(keywords_list, global_additional_text)
    crawler.start_parsing()

    await message.answer(
        "Crawling started.\n"
        f"Keywords: {', '.join(keywords_list)}\n"
        f"Additional text: {global_additional_text if global_additional_text else 'No additional text'}\n"
        "To stop crawling press: Stop Search",
        reply_markup=kb_main,
        parse_mode="html",
    )


@dp.message(F.text.lower() == "stop search")
async def stop_search_button(message: Message):
    """
    Зупинка парсера.
    """
    global crawler
    if crawler is not None:
        crawler.stop_parsing()
        crawler = None

    await message.answer("Crawling stopped.", reply_markup=kb_main, parse_mode="html")
    crawled_links_count = redis_client.get("crawled_links_count").decode()
    saved_images_count = redis_client.get("saved_images_count").decode()
    await message.answer(f"Statistics: \nCrawled links count: {crawled_links_count}\nSaved images count: {saved_images_count}")

    # Посилання на архів зображень (приклад формування)
    archive_url = f'<a href="http://{config.SERVER_HOST_HUMANABLE}:{config.SERVER_PORT}/get_images_archive">Download</a>'
    await message.answer(
        f"📁 Archive with parsed images you can get here: {archive_url}",
        reply_markup=kb_main,
        parse_mode="HTML",
    )
    
    # remove unique images hashes
    image_hashes = redis_client.smembers("image_hashes")
    redis_client.srem("image_hashes", *image_hashes)
    redis_client.set("crawled_links_count", 0)
    redis_client.set("saved_images_count", 0)


# ---- Точка входу в бота ----
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
