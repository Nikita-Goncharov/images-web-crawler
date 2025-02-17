import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

app = Celery("save_images", broker=os.getenv("CELERY_BROKER_URL"))
app.conf.broker_connection_retry_on_startup = True
app.conf.beat_schedule = {
    "add-every-20-seconds": {
        "task": "tasks.remove_duplicates",
        "schedule": 20.0,
        "args": ("parsed_images/",),
    },
}
