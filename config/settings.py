import os
from pathlib import Path

# Настройки сервера
SERVER_ADDRESS = ('0.0.0.0', 8000)

# Настройки для загрузки файлов
ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif')
ALLOWED_LENGTH = (5 * 1024 * 1024)  # 5MB
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/gif']

# Пути к директориям
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

# Старые пути (для совместимости с Docker-контейнером)
UPLOAD_DIR = 'images'
IMAGES_PATH = '/app/images'
LOGS_PATH = '/app/logs'
LOG_FILE = 'app.log'
ERROR_FILE = 'upload_failed.html'
STATIC_PATH = '/app/static'  # Возвращаем оригинальный путь для Docker

# Новые пути (с использованием Path)
IMAGES_DIR = DATA_DIR / 'images'
LOGS_DIR = DATA_DIR / 'logs'
STATIC_DIR = DATA_DIR / 'static'

# Создаем директории, если их нет
for directory in [DATA_DIR, IMAGES_DIR, LOGS_DIR, STATIC_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Настройки базы данных
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'image_hosting'),
    'user': os.getenv('DB_USER', 'app'),
    'password': os.getenv('DB_PASSWORD', 'app_password'),
    'host': os.getenv('DB_HOST', 'db'),
    'port': os.getenv('DB_PORT', '5432'),
    'connect_timeout': 10
}

# Настройки подключения
DB_CONNECT_RETRIES = 10
DB_RETRY_DELAY = 5

# Строка подключения к базе данных
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"