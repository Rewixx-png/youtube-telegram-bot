# config_reader.py
from pathlib import Path

# Определяем путь к файлу с токеном
token_file_path = Path(__file__).parent / 'token.txt'

# Проверяем, существует ли файл
if not token_file_path.is_file():
    raise FileNotFoundError(f"Не найден файл с токеном по пути: {token_file_path}")

# Читаем токен из файла и удаляем лишние пробелы или переносы строк
BOT_TOKEN = token_file_path.read_text().strip()

# Проверяем, что токен не пустой
if not BOT_TOKEN:
    raise ValueError("Файл 'token.txt' пуст. Пожалуйста, укажите в нем токен вашего бота.")