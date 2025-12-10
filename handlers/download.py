# handlers/download.py
import os
import asyncio
import logging
import requests
from html import escape
from aiogram import Router, F, Bot, types
from aiogram.types import FSInputFile
import yt_dlp

from utils.common import get_cookies_path, ProgressLogger

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("dl:"))
async def download_video_callback_handler(callback: types.CallbackQuery, bot: Bot):
    await callback.answer("Запрос принят!")
    
    _, video_id, format_id = callback.data.split(':')
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    loop = asyncio.get_running_loop()
    progress_logger = ProgressLogger(bot, callback.message, loop)

    await callback.message.edit_caption(caption="🚀 Начинаю магию...")
    
    video_path, thumbnail_path = None, None
    try:
        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'cookiefile': get_cookies_path(),
            'progress_hooks': [progress_logger.progress_hook],
            # Добавляем заголовки, чтобы YouTube не банил картинки
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Сначала качаем видео
            await loop.run_in_executor(None, lambda: ydl.download([video_url]))
            
            # 2. Получаем инфо для обложки
            info = ydl.extract_info(video_url, download=False)
            title = escape(info.get('title', 'video'))
            video_path = f"{video_id}.mp4"

            # 3. УМНЫЙ ПОИСК ОБЛОЖКИ (JPG ONLY)
            thumbnails = info.get('thumbnails', [])
            thumbnail_url = None
            
            # Ищем самую качественную картинку, у которой расширение строго jpg (или отсутствует webp в урле)
            # Перебираем с конца (там обычно лучшее качество)
            for t in reversed(thumbnails):
                # Проверяем расширение, если оно указано в метаданных
                if t.get('ext') == 'jpg' or (t.get('url') and '.jpg' in t.get('url')):
                    thumbnail_url = t.get('url')
                    break
            
            # Если JPG не нашли, берем любую последнюю (fallback)
            if not thumbnail_url and thumbnails:
                thumbnail_url = thumbnails[-1].get('url')

            # Скачиваем обложку
            if thumbnail_url:
                thumbnail_path = f"{video_id}.jpg"
                try:
                    # Качаем с таймаутом и User-Agent
                    response = requests.get(thumbnail_url, timeout=10, headers=ydl_opts['http_headers'])
                    if response.status_code == 200:
                        with open(thumbnail_path, 'wb') as f:
                            f.write(response.content)
                    else:
                        logger.warning(f"Thumbnail download failed: {response.status_code}")
                        thumbnail_path = None
                except Exception as e:
                    logger.error(f"Failed to download thumbnail: {e}")
                    thumbnail_path = None

        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"📤 Загружаю на сервера Telegram..."
        )

        # Подготавливаем файлы для отправки
        video_file = FSInputFile(video_path)
        thumbnail_input = FSInputFile(thumbnail_path) if thumbnail_path else None
        
        # Отправляем
        await bot.send_video(
            chat_id=callback.message.chat.id,
            video=video_file, 
            thumbnail=thumbnail_input, 
            supports_streaming=True, 
            caption=title,
            request_timeout=3600 # Час на выгрузку
        )
        
        await callback.message.delete()
        logger.info(f"Video {video_id} sent successfully.")

    except Exception as e:
        logger.error(f"Error downloading {video_url}: {e}", exc_info=True)
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"❌ Ошибка: {str(e)[:100]}"
        )
    
    finally:
        # Уборка мусора
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)