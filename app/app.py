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
from app.handlers.ImageHostingHandler import ImageHostingHandler
from dotenv import load_dotenv
from loguru import logger
from config.settings import SERVER_ADDRESS
from config.logger_setup import setup_logger
from app.db.DBManager import DBManager
from app.router import Router

# Было у router перенесено сюда, из-за проблемы с циклическими импортами
def register_routes(router, handler_class):
    """
    Регистрирует все маршруты в роутере.
    
    Аргументы:
        router: экземпляр класса Router
        handler_class: класс-обработчик запросов
    """
    # Статические файлы HTML
    router.add_route('GET', '/', handler_class.get_index)
    router.add_route('GET', '/index.html', lambda handler, **kwargs: handler.serve_static_file('index.html'))
    router.add_route('GET', '/upload.html', lambda handler, **kwargs: handler.serve_static_file('upload.html'))
    router.add_route('GET', '/upload', handler_class.get_upload)
    router.add_route('GET', '/all_images.html', lambda handler, **kwargs: handler.serve_static_file('all_images.html'))
    router.add_route('GET', '/error.html', lambda handler, **kwargs: handler.serve_static_file('error.html'))
    router.add_route('GET', '/upload_success.html', lambda handler, **kwargs: handler.serve_static_file('upload_success.html'))
    
    # Редирект со страницы /images-list на /all_images.html (согласно ТЗ)
    router.add_route('GET', '/images-list', lambda handler, **kwargs: handler.redirect_to('/all_images.html'))
    
    # Добавляем маршрут для HEAD-запросов
    router.add_route('HEAD', '/', lambda handler, **kwargs: handler.serve_static_file('index.html'))
    
    # API для работы с изображениями
    router.add_route('GET', '/api/images', handler_class.get_images)
    router.add_route('GET', '/api/images/<filename>', handler_class.get_image)
    router.add_route('POST', '/api/images', handler_class.post_upload)
    router.add_route('DELETE', '/api/images/<filename>', handler_class.delete_image)
    
    # Маршрут для удаления изображений по ID (согласно ТЗ)
    router.add_route('GET', '/delete/<id>', handler_class.delete_image_by_id)
    
    # Маршрут для доступа к изображениям через /images/
    router.add_route('GET', '/images/<filename>', handler_class.get_image)
    
    # Статические файлы (JS, CSS, иконки)
    router.add_route('GET', '/static/button.css', lambda handler, **kwargs: handler.serve_static_file('button.css'))
    router.add_route('GET', '/static/style.css', lambda handler, **kwargs: handler.serve_static_file('style.css'))
    router.add_route('GET', '/static/all_images.js', lambda handler, **kwargs: handler.serve_static_file('all_images.js'))
    router.add_route('GET', '/static/<path:path>', handler_class.serve_static_file)
    router.add_route('GET', '/favicon.ico', lambda handler, **kwargs: handler.serve_static_file('favicon.ico'))
    
    logger.info('Routes registered')

# Инициализируем сервер
def run(server_class=HTTPServer, handler_class=ImageHostingHandler):
    load_dotenv()
    setup_logger()

    # Инициализируем базу данных
    db = DBManager()
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