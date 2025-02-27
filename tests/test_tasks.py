import os
import pytest
from unittest.mock import patch, MagicMock
from tasks import download_image, has_ext, is_image_valid

@pytest.fixture
def fake_response():
    """Fake response object for requests.get."""
    mock_resp = MagicMock()
    mock_resp.content = b"\x89PNG\r\n\x1a\n"  # Byte sequence mimicking a PNG
    mock_resp.raise_for_status = MagicMock()
    return mock_resp

@patch("tasks.redis_client")
def test_download_image(mock_redis):
    mock_redis.sismember.return_value = False  # Simulate that the hash does not exist

    save_dir = "test_dir"
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    try:
        download_image("https://http.cat/images/102.jpg", save_dir)
        mock_redis.sadd.assert_called_once()
        mock_redis.incr.assert_called_once_with("saved_images_count")
    finally:
        # Remove the created directory
        if os.path.exists(save_dir):
            for f in os.listdir(save_dir):
                os.remove(os.path.join(save_dir, f))
            os.rmdir(save_dir)


def test_has_ext():
    assert has_ext("image.jpg") is True
    assert has_ext("image.png") is True
    assert has_ext("image.jpeg") is False  # By default, it is converted to .jpg
    assert has_ext("document.pdf") is False


@patch("tasks.get_image_size", return_value=(320, 320))
def test_is_image_valid_large(mock_size):
    """Check that a 320x320 image is considered valid."""
    assert is_image_valid("some_path.png") is True


@patch("tasks.get_image_size", return_value=(100, 100))
def test_is_image_valid_small(mock_size):
    """Check that a 100x100 image is not valid (too small)."""
    assert is_image_valid("some_path.png") is False
