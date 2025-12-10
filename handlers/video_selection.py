# handlers/video_selection.py
import logging
from html import escape
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

from utils.common import get_cookies_path, get_video_id, get_emoji_for_resolution, format_bytes

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.contains("youtu"))
async def get_video_formats_handler(message: types.Message):
    video_id = get_video_id(message.text)
    if not video_id:
        await message.answer("Не удалось извлечь ID видео. Проверьте ссылку.")
        return
    
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    status_message = await message.answer("🔍 Анализирую видео...")
    
    try:
        # Добавляем заголовки, чтобы притвориться браузером
        ydl_opts = {
            'noplaylist': True,
            'cookiefile': get_cookies_path(),
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(clean_url, download=False)
            except yt_dlp.utils.DownloadError as e:
                # Если YouTube заблокировал запрос
                if "Sign in" in str(e) or "cookies" in str(e).lower():
                    await status_message.edit_text("⛔ YouTube требует авторизацию.\nКуки протухли или сервер в бане.")
                    logger.error(f"YouTube Cookie Error: {e}")
                    return
                else:
                    raise e

            formats = info.get('formats', [])
        
        builder = InlineKeyboardBuilder()
        found_formats = False
        
        for f in sorted(formats, key=lambda x: x.get('height') or 0, reverse=True):
            if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                resolution = f.get('height')
                if not resolution: continue
                
                format_id = f.get('format_id')
                filesize = f.get('filesize') or f.get('filesize_approx')
                ext = f.get('ext')
                
                emoji = get_emoji_for_resolution(resolution)
                button_text = f"{emoji} {resolution}p ({ext}, {format_bytes(filesize)})"
                callback_data = f"dl:{video_id}:{format_id}"
                
                builder.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))
                found_formats = True
        
        if not found_formats:
            await status_message.edit_text("😔 Не нашел доступных форматов для скачивания (возможно, видео ограничено).")
            return
            
        title = escape(info.get('title', 'Video'))
        thumbnails = info.get('thumbnails', [])
        thumbnail_url = thumbnails[-1].get('url') if thumbnails else None
        
        await status_message.delete()
        caption_text = f"<b>{title}</b>\n\nВыберите качество:"
        builder.adjust(2)
        
        if thumbnail_url:
            await message.answer_photo(photo=thumbnail_url, caption=caption_text, reply_markup=builder.as_markup())
        else:
            await message.answer(caption_text, reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"CRITICAL ERROR for {clean_url}: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Ошибка при анализе: {str(e)[:100]}")