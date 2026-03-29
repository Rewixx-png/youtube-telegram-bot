# bot.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from handlers import start, video_selection, download
from settings import settings

logger = logging.getLogger(__name__)


def build_api_base_url() -> str:
    if settings.telegram_api_base_url:
        return settings.telegram_api_base_url.rstrip("/")

    if settings.api_domain:
        domain = settings.api_domain.removeprefix("https://").removeprefix("http://").rstrip("/")
        return f"https://{domain}"

    raise ValueError("Set TELEGRAM_API_BASE_URL or API_DOMAIN in .env")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    server_url = build_api_base_url()
    logger.info("Starting bot with API base: %s", server_url)
    
    local_server = TelegramAPIServer.from_base(server_url)
    session = AiohttpSession(api=local_server)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session
    )
    
    actual_base_url = bot.session.api.base
    logger.info(f"!!! FINAL CHECK: Bot is configured to use API base URL: {actual_base_url} !!!")
    
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(video_selection.router)
    dp.include_router(download.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, polling_timeout=60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
