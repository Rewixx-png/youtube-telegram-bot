# handlers/start.py
import logging
from html import escape
from aiogram import Router, types
from aiogram.filters import CommandStart

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot.")
    user_name = escape(message.from_user.full_name)
    start_text = (
        f"<b>Привет, {user_name}! 🚀</b>\n\n"
        "Я твой персональный ассистент для скачивания видео с YouTube.\n\n"
        "<b>Что я умею:</b>\n"
        "✅ Предлагаю все доступные качества, включая <b>4K</b>.\n"
        "✅ Скачиваю видео и звук, а затем соединяю их в один <b>MP4</b> файл.\n"
        "✅ Показываю обложку видео и примерный размер файла.\n\n"
        "Просто отправь мне ссылку на видео, и магия начнется! ✨\n\n"
        "По всем вопросам бота – @RewiX_X"
    )
    await message.answer(start_text)