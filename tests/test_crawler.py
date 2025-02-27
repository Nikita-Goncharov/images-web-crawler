import pytest
from unittest.mock import patch, MagicMock
from crawler import Crawler

@pytest.mark.asyncio
@patch("crawler.download_image.delay")
@patch("crawler.httpx.AsyncClient.get")
async def test_crawler_scrape_images(mock_get, mock_download):
    """Check that images are scanned and a Celery task is called."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_html = """
    <html>
      <body>
        <img src="http://example.com/image.jpg" alt="cat picture" />
        <a href="page2.html">Link 1</a>
        <a href="page3.html">Link 2</a>
      </body>
    </html>
    """
    mock_response.text = mock_html
    mock_get.return_value = mock_response

    c = Crawler(keywords=["cat", "dog"], text_to_keyword="")
    links = await c.scrape_images("http://example.com")

    assert len(links) == 2
    
    mock_download.assert_called_once()
    call_args, call_kwargs = mock_download.call_args
    
    assert call_args[0] == "http://example.com/image.jpg"
    assert "cat" in call_args[1]  


@pytest.mark.asyncio
async def test_image_find_keyword():
    """Check keyword detection in image attributes."""
    from bs4 import BeautifulSoup

    html = """<img src="test.png" alt="Cute Cat" title="Something else" />"""
    soup = BeautifulSoup(html, "html.parser")
    img_tag = soup.find("img")

    c = Crawler(keywords=["cat", "dog"], text_to_keyword="")
    found = c.image_find_keyword(img_tag, "test.png")
    assert "cat" in found


@pytest.mark.asyncio
@patch("crawler.Process")
def test_crawler_start_parsing(mock_process):
    """Check that start_parsing() creates a process and sets running = True."""
    c = Crawler(["cat"], "")
    c.start_parsing()
    assert c.shared_data["running"] is True
    mock_process.assert_called_once()


@pytest.mark.asyncio
@patch("crawler.Process")
@patch("crawler.app.control.purge", return_value=0)
def test_crawler_stop_parsing(mock_celery_purge, mock_process):
    """Check that stop_parsing() sets running = False and calls join() on the process."""
    c = Crawler(["cat"], "")
    c.start_parsing()
    c.stop_parsing()

    assert c.shared_data["running"] is False

    instance = mock_process.return_value
    instance.join.assert_called_once()
