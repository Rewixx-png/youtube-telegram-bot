# handlers/video_selection.py
import logging
from html import escape
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

from utils.common import COOKIES_PATH, get_video_id, get_emoji_for_resolution, format_bytes

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.contains("youtu"))
async def get_video_formats_handler(message: types.Message):
    # Извлекаем ID
    video_id = get_video_id(message.text)
    if not video_id:
        await message.answer("Не удалось извлечь ID видео из ссылки. Пожалуйста, отправьте корректную ссылку на YouTube.")
        return
    
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    status_message = await message.answer("Анализирую доступные форматы...")
    
    try:
        ydl_opts = {'noplaylist': True, 'cookiefile': str(COOKIES_PATH)}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            formats = info.get('formats', [])
        
        builder = InlineKeyboardBuilder()
        found_formats = False
        
        # Сортируем форматы и выбираем только видео-потоки для мерджа
        for f in sorted(formats, key=lambda x: x.get('height') or 0, reverse=True):
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                resolution, format_id = f.get('height'), f.get('format_id')
                filesize = f.get('filesize') or f.get('filesize_approx')
                ext = f.get('ext')
                emoji = get_emoji_for_resolution(resolution)
                button_text = f"{emoji} {resolution}p ({ext}, {format_bytes(filesize)})"
                callback_data = f"dl:{video_id}:{format_id}"
                builder.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))
                found_formats = True
        
        if not found_formats:
            await status_message.edit_text("Не найдено подходящих видео-форматов для скачивания."); return
            
        title = escape(info.get('title', ''))
        thumbnails = info.get('thumbnails', [])
        thumbnail_url = thumbnails[-1].get('url') if thumbnails else None
        
        await status_message.delete()
        caption_text = f"<b>{title}</b>\n\nВыберите качество (бот добавит лучший звук и создаст MP4):"
        builder.adjust(2)
        
        if thumbnail_url:
            await message.answer_photo(photo=thumbnail_url, caption=caption_text, reply_markup=builder.as_markup())
        else:
            await message.answer(caption_text, reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error getting formats for {clean_url}: {e}", exc_info=True)
        await status_message.edit_text("❌ Произошла ошибка при получении информации о видео.")