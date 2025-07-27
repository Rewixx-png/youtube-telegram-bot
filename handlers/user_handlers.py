# handlers/user_handlers.py
import os
import asyncio
import logging
import re
import requests
import time
from html import escape
from pathlib import Path
from aiogram import Bot, Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

logger = logging.getLogger(__name__)
user_router = Router()

COOKIES_PATH = Path(__file__).parent.parent / 'cookies.txt'

# --- ПЕРЕПИСАННЫЙ КЛАСС С ЯВНЫМ ВЫЗОВОМ ЧЕРЕЗ BOT ---
class ProgressLogger:
    def __init__(self, bot: Bot, message: types.Message, loop: asyncio.AbstractEventLoop):
        self.bot = bot
        self.message = message
        self.loop = loop
        self.last_update_time = 0

    def _edit_caption_threadsafe(self, text: str, parse_mode: str = None):
        """Безопасная обертка для вызова edit_caption из другого потока."""
        coro = self.bot.edit_message_caption(
            chat_id=self.message.chat.id,
            message_id=self.message.message_id,
            caption=text,
            parse_mode=parse_mode
        )
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            current_time = time.time()
            if current_time - self.last_update_time < 2.5:
                return
            self.last_update_time = current_time
            
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            
            if total_bytes and downloaded_bytes:
                percent = downloaded_bytes / total_bytes * 100
                progress = int(percent / 10)
                progress_bar = '█' * progress + '░' * (10 - progress)
                
                text = f"📥 Скачиваю видео...\n`[{progress_bar}] {percent:.1f}%`"
                self._edit_caption_threadsafe(text, parse_mode="MarkdownV2")

        elif d['status'] == 'finished':
            text = f"✅ Скачивание завершено. Начинаю обработку..."
            self._edit_caption_threadsafe(text)

# (остальной код остается без изменений)

def get_emoji_for_resolution(resolution):
    if resolution >= 2160: return "💎"
    elif resolution >= 1440: return "🌟"
    elif resolution >= 1080: return "🔥"
    elif resolution >= 720: return "✅"
    else: return "⚙️"

def format_bytes(size):
    if size is None: return "Неизв."
    power = 1024; n = 0
    power_labels = {0: '', 1: 'КБ', 2: 'МБ', 3: 'ГБ'}
    while size > power and n < len(power_labels) - 1:
        size /= power; n += 1
    return f"{size:.1f} {power_labels[n]}"

def get_video_id(url):
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

@user_router.message(CommandStart())
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
        "Просто отправь мне ссылку на видео, и магия начнется! ✨"
    )
    await message.answer(start_text)

@user_router.message(F.text.contains("youtu"))
async def get_video_formats_handler(message: types.Message):
    clean_url = message.text.split("?")[0]
    video_id = get_video_id(clean_url)
    if not video_id:
        await message.answer("Не удалось извлечь ID видео из ссылки. Пожалуйста, отправьте корректную ссылку на YouTube.")
        return
        
    status_message = await message.answer("Анализирую доступные форматы...")
    
    try:
        ydl_opts = {'noplaylist': True, 'cookiefile': str(COOKIES_PATH)}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            formats = info.get('formats', [])
        
        builder = InlineKeyboardBuilder()
        found_formats = False
        
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
        thumbnails = info.get('thumbnails', []); thumbnail_url = thumbnails[-1].get('url') if thumbnails else None
        
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


# --- ИЗМЕНЕНИЕ: ПОЛУЧАЕМ ОБЪЕКТ BOT В ХЕНДЛЕР ---
@user_router.callback_query(F.data.startswith("dl:"))
async def download_video_callback_handler(callback: types.CallbackQuery, bot: Bot):
    await callback.answer("Запрос принят!")
    
    _, video_id, format_id = callback.data.split(':')
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # --- ИЗМЕНЕНИЕ: ПЕРЕДАЕМ BOT В ЛОГГЕР ---
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
            if thumbnail_url:
                thumbnail_path = f"{video_id}.jpg"
                response = requests.get(thumbnail_url)
                if response.status_code == 200:
                    with open(thumbnail_path, 'wb') as f: f.write(response.content)
                else: thumbnail_path = None
            
            await loop.run_in_executor(None, lambda: ydl.download([video_url]))
            
            video_path = f"{video_id}.mp4"

        # Теперь вызываем edit_caption через bot, а не через message
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            caption=f"📤 Отправляю видео..."
        )

        thumbnail_input = FSInputFile(thumbnail_path) if thumbnail_path else None
        video_file = FSInputFile(video_path)
        
        await bot.send_video(
            chat_id=callback.message.chat.id,
            video=video_file, 
            thumbnail=thumbnail_input, 
            supports_streaming=True, 
            caption=title
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
        if video_path and os.path.exists(video_path): os.remove(video_path)
        if thumbnail_path and os.path.exists(thumbnail_path): os.remove(thumbnail_path)