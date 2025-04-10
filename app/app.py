"""
Это основной файл приложения для хостинга изображений. 
Он обрабатывает загрузку картинок, показывает их список и отдает статические файлы.

Как использовать:
1. Запустить сервер
2. Открыть в браузере http://localhost
3. Загружать картинки через форму
4. Смотреть загруженные картинки в галерее

Технические детали:
- Поддерживает картинки: jpg, jpeg, png, gif
- Максимальный размер файла: 5MB 
- Все картинки хранятся в папке images/
- Статические файлы в папке static/
"""

import os
from http.server import HTTPServer
from ImageHostingHandler import ImageHostingHandler
from dotenv import load_dotenv
from loguru import logger
from settings import SERVER_ADDRESS
from logger_setup import setup_logger
from DBManager import DBManager
from Router import Router
from routes import register_routes

# Инициализируем сервер
def run(server_class=HTTPServer, handler_class=ImageHostingHandler):
    load_dotenv()
    setup_logger()

    db = DBManager(os.getenv('POSTGRES_DB'),
                   os.getenv('POSTGRES_USER'),
                   os.getenv('POSTGRES_PASSWORD'),
                   os.getenv('POSTGRES_HOST'),
                   os.getenv('POSTGRES_PORT'))
    db.init_tables()

    router = Router()
    register_routes(router, handler_class)

    httpd = HTTPServer(SERVER_ADDRESS, ImageHostingHandler)
    try:
        logger.info(f"Serving at http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}")
        httpd.serve_forever()
    except BaseException:
        pass
    finally:
        logger.info('Server stopped')
        httpd.server_close()

if __name__ == "__main__":
    run()