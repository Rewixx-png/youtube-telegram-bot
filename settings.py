# settings.py
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str
    
    # Telegram API Server
    telegram_api_id: str | int
    telegram_api_hash: str
    
    # Domain & SSL
    api_domain: str
    admin_email: str = "admin@localhost"
    
    # Paths
    base_dir: Path = Path(__file__).parent
    cookies_path: Path = base_dir / "cookies.txt"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()