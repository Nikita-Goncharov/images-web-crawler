import os 

class Config:
    def __init__(self, init_env=True):
        if init_env:
            from dotenv import load_dotenv
            
            load_dotenv()
    
    @property
    def API_TOKEN(self):
        return os.getenv("BOT_API_TOKEN", "")
    
    @property
    def CELERY_BROKER_URL(self):
        return os.getenv("CELERY_BROKER_URL", "")
    
    @property
    def SERVER_HOST(self):
        return os.getenv("SERVER_HOST", "")
    
    @property
    def SERVER_HOST_HUMANABLE(self):
        return os.getenv("SERVER_HOST_HUMANABLE", "")
    
    @property
    def SERVER_PORT(self):
        return os.getenv("SERVER_PORT", 0)
    
    @property
    def SAVE_IMAGES_PATH(self):
        return os.getenv("SAVE_IMAGES_PATH", "images")
    
    @property
    def IMAGES_ARCHIVE_NAME(self):
        return os.getenv("IMAGES_ARCHIVE_NAME", "images")


config = Config()