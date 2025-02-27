from celery_app import app
from config import config

def test_celery_app_broker():
    """Ensure that broker_url matches the value from config."""
    assert app.conf.broker_url == config.CELERY_BROKER_URL
