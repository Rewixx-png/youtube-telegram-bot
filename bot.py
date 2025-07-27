# bot.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from handlers.user_handlers import user_router
from config_reader import BOT_TOKEN

logger = logging.getLogger(__name__)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger.info("Starting bot with Local Bot API Server...")

    local_server = TelegramAPIServer.from_base("http://127.0.0.1:8081")

    session = AiohttpSession(api=local_server)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session
    )
    
    actual_base_url = bot.session.api.base
    logger.info(f"!!! FINAL CHECK: Bot is configured to use API base URL: {actual_base_url} !!!")
    
    dp = Dispatcher()
    dp.include_router(user_router)

    await bot.delete_webhook(drop_pending_updates=True)
    
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
    await dp.start_polling(bot, polling_timeout=60)
    # -----------------------

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")