from celery import Celery

from config import config

API_TOKEN = config.API_TOKEN

app = Celery("save_images", broker=config.CELERY_BROKER_URL)
app.conf.broker_connection_retry_on_startup = True
