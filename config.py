import os 

from dotenv import load_dotenv

load_dotenv()

class Config:
    API_TOKEN = os.getenv("BOT_API_TOKEN", "")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")
    
    SERVER_HOST = os.getenv("SERVER_HOST", "")
    SERVER_HOST = "localhost" if os.getenv("SERVER_HOST", "") == "0.0.0.0" else os.getenv("SERVER_HOST", "")
    SERVER_PORT = os.getenv("SERVER_PORT", 0)
    
config = Config()