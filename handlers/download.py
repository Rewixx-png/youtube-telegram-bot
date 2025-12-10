# handlers/download.py
import os
import asyncio
import logging
import requests
from html import escape
from aiogram import Router, F, Bot, types
from aiogram.types import FSInputFile
import yt_dlp

from utils.common import COOKIES_PATH, ProgressLogger

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("dl:"))
async def download_video_callback_handler(callback: types.CallbackQuery, bot: Bot):
    await callback.answer("Запрос принят!")
    
    _, video_id, format_id = callback.data.split(':')
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    loop = asyncio.get_running_loop()
    progress_logger = ProgressLogger(bot, callback.message, loop)

    await callback.message.edit_caption(caption="Подготовка к скачиванию...")
    
    video_path, thumbnail_path = None, None
    try:
        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'cookiefile': str(COOKIES_PATH),
            'progress_hooks': [progress_logger.progress_hook],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = escape(info.get('title', 'video'))
            
            thumbnails = info.get('thumbnails', [])
            thumbnail_url = thumbnails[-1].get('url') if thumbnails else None
            
            # Качаем обложку отдельно
            if thumbnail_url:
                thumbnail_path = f"{video_id}.jpg"
                response = requests.get(thumbnail_url)
                if response.status_code == 200:
                    with open(thumbnail_path, 'wb') as f: f.write(response.content)
                else: thumbnail_path = None
            
            # Запускаем скачивание в отдельном потоке, чтобы не блочить Event Loop
            await loop.run_in_executor(None, lambda: ydl.download([video_url]))
            
            video_path = f"{video_id}.mp4"

        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"📤 Отправляю видео..."
        )

        thumbnail_input = FSInputFile(thumbnail_path) if thumbnail_path else None
        video_file = FSInputFile(video_path)
        
        # Отправляем видео
        await bot.send_video(
            chat_id=callback.message.chat.id,
            video=video_file, 
            thumbnail=thumbnail_input, 
            supports_streaming=True, 
            caption=title,
            request_timeout=3600  # Тайм-аут 1 час
        )
        
        await callback.message.delete()
        logger.info(f"Video {video_id} sent successfully to user {callback.from_user.id}.")

    except Exception as e:
        logger.error(f"Error downloading {video_url} with format {format_id}", exc_info=True)
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"❌ Произошла ошибка при скачивании или отправке видео."
        )
    
    finally:
        # Уборка мусора
        if video_path and os.path.exists(video_path): os.remove(video_path)
        if thumbnail_path and os.path.exists(thumbnail_path): os.remove(thumbnail_path)