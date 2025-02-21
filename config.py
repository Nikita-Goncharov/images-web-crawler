import os 

from dotenv import load_dotenv

load_dotenv()

class Config:
    API_TOKEN = os.getenv("BOT_API_TOKEN", "")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")
    
    SERVER_HOST = os.getenv("SERVER_HOST", "")
    SERVER_HOST_HUMANABLE = os.getenv("SERVER_HOST_HUMANABLE", "")
    SERVER_PORT = os.getenv("SERVER_PORT", 0)
    
    SAVE_IMAGES_PATH = os.getenv("SAVE_IMAGES_PATH", "images")
    IMAGES_ARCHIVE_NAME = os.getenv("IMAGES_ARCHIVE_NAME", "images")
    
    
config = Config()