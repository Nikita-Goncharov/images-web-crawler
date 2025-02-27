import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message

from bot import (
    show_keywords,
    global_keywords,
    cmd_start,
    process_add_keyword,
    process_remove_keyword,
    start_search_button,
    stop_search_button
)


@pytest.mark.asyncio
async def test_cmd_start():
    """Check that /start sends the expected response."""
    message = AsyncMock(spec=Message)
    message.text = "/start"

    await cmd_start(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "Hello! This is an image search bot." in args[0]


@pytest.mark.asyncio
async def test_show_keywords_empty():
    """If global_keywords is empty, it should return: 'There are no keywords.'"""

    backup_keywords = global_keywords.copy()
    global_keywords.clear()

    message = AsyncMock(spec=Message)
    message.text = "keywords"

    await show_keywords(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "There are no keywords." in args[0]

    global_keywords.update(backup_keywords)


@pytest.mark.asyncio
async def test_show_keywords_non_empty():
    """If global_keywords is not empty, check that they are displayed."""
    backup_keywords = global_keywords.copy()
    global_keywords.clear()
    global_keywords.update(["cat", "dog"])

    message = AsyncMock(spec=Message)
    message.text = "keywords"

    await show_keywords(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args

    assert "cat, dog" in args[0]

    global_keywords.clear()
    global_keywords.update(backup_keywords)


@pytest.mark.asyncio
async def test_process_add_keyword():
    """Check adding a new keyword."""
    backup_keywords = global_keywords.copy()
    global_keywords.clear()

    message = AsyncMock(spec=Message)
    message.text = "new_keyword"

    state = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()

    await process_add_keyword(message, state)

    assert "new_keyword" in global_keywords
    message.answer.assert_called_once()
    state.clear.assert_called_once()

    global_keywords.clear()
    global_keywords.update(backup_keywords)


@pytest.mark.asyncio
async def test_process_remove_keyword():
    """Check removing a keyword."""
    backup_keywords = global_keywords.copy()
    global_keywords.clear()
    global_keywords.update(["cat", "dog"])

    message = AsyncMock(spec=Message)
    message.text = "cat"

    state = AsyncMock()

    await process_remove_keyword(message, state)
    assert "cat" not in global_keywords
    message.answer.assert_called_once()

    global_keywords.clear()
    global_keywords.update(backup_keywords)


@pytest.mark.asyncio
@patch("bot.crawler", None)
async def test_start_search_button_no_keywords():
    """Check the case when there are no keywords and a warning appears."""
    backup_keywords = global_keywords.copy()
    global_keywords.clear()

    message = AsyncMock(spec=Message)

    await start_search_button(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "There are no keywords." in args[0]

    global_keywords.update(backup_keywords)


@pytest.mark.asyncio
@patch("bot.crawler")
async def test_stop_search_button(mock_crawler):
    """Check stopping the search."""
    message = AsyncMock(spec=Message)

    mock_crawler.stop_parsing = AsyncMock()
    await stop_search_button(message)

    mock_crawler.stop_parsing.assert_called_once()
    message.answer.assert_called()
