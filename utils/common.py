# utils/common.py
import asyncio
import time
import re
from aiogram import Bot, types
from settings import settings

# --- ВОТ ЭТА ФУНКЦИЯ, КОТОРОЙ НЕ ХВАТАЛО ---
def get_cookies_path():
    """Возвращает путь к файлу cookies.txt как строку."""
    return str(settings.cookies_path)
# -------------------------------------------

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