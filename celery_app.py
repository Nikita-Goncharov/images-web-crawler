from celery import Celery

app = Celery("save_images", broker="redis://localhost")
app.conf.broker_connection_retry_on_startup = True
app.conf.beat_schedule = {
    "add-every-20-seconds": {
        "task": "tasks.remove_duplicates",
        "schedule": 20.0,
        "args": ("parsed_images/",),
    },
}
