import os
from unittest.mock import patch

def test_config_load():
    """Check that Config values are correctly read from the environment variables."""
    with patch.dict(os.environ, {
        "BOT_API_TOKEN": "test_token",
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "SERVER_HOST": "0.0.0.0",
        "SERVER_HOST_HUMANABLE": "localhost",
        "SERVER_PORT": "5000",
        "SAVE_IMAGES_PATH": "test_images",
        "IMAGES_ARCHIVE_NAME": "test_archive"
    }):
        from config import Config
        c = Config(init_env=False)
        assert c.API_TOKEN == "test_token"
        assert c.CELERY_BROKER_URL == "redis://localhost:6379/0"
        assert c.SERVER_HOST == "0.0.0.0"
        assert c.SERVER_PORT == "5000"
        assert c.SAVE_IMAGES_PATH == "test_images"
        assert c.IMAGES_ARCHIVE_NAME == "test_archive"
