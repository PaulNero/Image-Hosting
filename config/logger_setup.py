import os
import sys
from loguru import logger
from config.settings import LOGS_DIR, LOG_FILE

def setup_logger():
    """Настройка логгера."""
    try:
        # Создаем директорию для логов, если её нет
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Путь к файлу логов
        log_path = LOGS_DIR / LOG_FILE

        # Удаляем все предыдущие обработчики
        logger.remove()  

        try:
            # В терминал, более подробно
            logger.add(
                sys.stdout, 
                format="[{time:YYYY-MM-DD HH:mm:ss}] | {level} | {message}", 
                colorize=True,
                level="DEBUG"
            )
        except Exception as e:
            print(f"Warning: Could not setup console logging: {e}")

        try:
            # В файл, только важные события
            logger.add(
                str(log_path),  # Преобразуем Path в строку
                format="[{time:YYYY-MM-DD HH:mm:ss}] | {level} | {message}",
                level="INFO",
                rotation="10 MB",
                retention="10 days",
                compression="zip",
                backtrace=True,
                diagnose=True
            )
        except Exception as e:
            print(f"Error: Could not setup file logging: {e}")
            # блокирует запуск приложения если логи не записались
            raise  
        
        logger.info("Logger initialized")
        
    except Exception as e:
        print(f"Critical error in logger setup: {e}")
        # блокирует запуск приложения если нет файла логов или нет доступа к нему
        raise  
