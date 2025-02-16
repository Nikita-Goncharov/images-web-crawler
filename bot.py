import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

from crawler import CryptoCrawler

load_dotenv()


API_TOKEN = os.getenv("BOT_API_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Global set of keywords
global_keywords = set(["cat", "dog"])

# Global variable to control the parsing process
crawler: CryptoCrawler | None = None


class AddKeywordState(StatesGroup):
    waiting_for_keyword = State()

class RemoveKeywordState(StatesGroup):
    waiting_for_keyword = State()

kb_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Show Keywords")],
        [KeyboardButton(text="Add Keyword"), KeyboardButton(text="Remove Keyword")],
        [KeyboardButton(text="Start Search"), KeyboardButton(text="Stop Search")],
    ],
    resize_keyboard=True
)


@dp.startup()
async def on_startup():
    logging.info("Bot is starting up...")


@dp.shutdown()
async def on_shutdown():
    logging.info("Bot is shutting down...")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    /start or /help - show welcome and main menu with buttons.
    """
    await message.answer(
        text=(
            "Hello! This is an image search bot.\n\n"
            "Here are the actions you can take from the buttons below:\n"
            "1) Show Keywords - show current keywords\n"
            "2) Add Keyword — add a keyword\n"
            "3) Remove Keyword — remove the keyword\n"
            "4) Start Search - start the search\n"
            "5) Stop Search - stop the search\n"
        ),
        reply_markup=kb_main
    )


@dp.message(F.text.lower() == "show keywords")
async def show_keywords(message: Message):
    """
    "Show Keywords" button: show current keywords.
    """
    if not global_keywords:
        await message.answer("There are no keywords.", reply_markup=kb_main, parse_mode="html")
    else:
        text = ", ".join(sorted(global_keywords))
        await message.answer(f"Current keywords:\n<b>{text}</b>", reply_markup=kb_main, parse_mode="html")


@dp.message(F.text.lower() == "add keyword")
async def add_keyword_button(message: Message, state: FSMContext):
    """
    "Add Keyword" button: puts the word in the waiting state.
    """
    await message.answer("Add keyword:", reply_markup=kb_main, parse_mode="html")
    await state.set_state(AddKeywordState.waiting_for_keyword)


@dp.message(F.text.lower() == "remove keyword")
async def remove_keyword_button(message: Message, state: FSMContext):
    """
    "Remove Keyword" button: puts the word in the waiting state.
    """
    await message.answer("Remove keyword:", reply_markup=kb_main, parse_mode="html")
    await state.set_state(RemoveKeywordState.waiting_for_keyword)


@dp.message(F.text.lower() == "start search")
async def start_search_button(message: Message):
    """
    "Start Search" button: start the crawler (with fixed text_to_keyword or empty).
    """
    global crawler

    if not global_keywords:
        await message.answer("There are no keywords. You should add first (button Add Keyword).", reply_markup=kb_main, parse_mode="html")
        return

    # If the crawler is already running, stop it
    if crawler is not None:
        crawler.stop_parsing()
        crawler = None

    # text_to_keyword can be requested additionally, but here we will make it empty
    text_to_keyword = ""
    keywords_list = list(global_keywords)
    crawler = CryptoCrawler(keywords_list, text_to_keyword)
    crawler.start_parsing()

    await message.answer(
        "Crawling started.\n"
        f"Keywords: {', '.join(keywords_list)}\n"
        "To stop crawling press: Stop Search",
        reply_markup=kb_main, 
        parse_mode="html"
    )


@dp.message(F.text.lower() == "stop search")
async def stop_search_button(message: Message):
    """
    "Stop Search" button: stop the crawler.
    """
    global crawler
    if crawler is not None:
        crawler.stop_parsing()
        crawler = None
    await message.answer("Crowling stopped.", reply_markup=kb_main, parse_mode="html")


@dp.message(AddKeywordState.waiting_for_keyword)
async def process_add_keyword(message: Message, state: FSMContext):
    """
    Processing the entered word for addition.
    """
    word = message.text.strip().lower()
    if word in global_keywords:
        await message.answer(f"Keyword <b>{word}</b> already in keywords list.", reply_markup=kb_main, parse_mode="html")
    else:
        global_keywords.add(word)
        await message.answer(f"Added <b>{word}</b> to keywords list.", reply_markup=kb_main, parse_mode="html")

    await state.clear()


@dp.message(RemoveKeywordState.waiting_for_keyword)
async def process_remove_keyword(message: Message, state: FSMContext):
    """
    Processing the entered word for deletion.
    """
    word = message.text.strip().lower()
    if word in global_keywords:
        global_keywords.remove(word)
        await message.answer(f"Removed <b>{word}</b> from keywords list.", reply_markup=kb_main, parse_mode="html")
    else:
        await message.answer(f"Keyword <b>{word}</b> not in the list.", reply_markup=kb_main, parse_mode="html")

    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
