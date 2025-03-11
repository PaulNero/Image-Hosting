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

import io
import os.path
import uuid
import magic
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from loguru import logger
from os import listdir, makedirs
from os.path import isfile, join, exists
from typing import Dict, Callable
import email
from email.parser import BytesParser
from email.policy import default

from PIL import Image

# Основные настройки сервера
SERVER_ADDRESS = ('0.0.0.0', 8000)
ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif')
ALLOWED_LENGTH = (5 * 1024 * 1024)  # 5MB
UPLOAD_DIR = 'images'
IMAGES_PATH = '/app/images'
LOGS_PATH = '/app/logs'
STATIC_PATH = '/app/static'

# Создание директории для логов, если она не существует
if not exists(LOGS_PATH):
    makedirs(LOGS_PATH, exist_ok=True)

# Настройка логирования в stdout
logger.remove()  # Удаляем стандартный обработчик
logger.add(
    sys.stdout,
    format="[{time:YYYY-MM-DD HH:mm:ss}] | {level} | {message}",
    colorize=True,
    backtrace=True,
    diagnose=True,
)

def parse_multipart_form_data(headers, body):
    """Парсинг multipart/form-data."""
    content_type = headers.get('Content-Type', '')
    if not content_type.startswith('multipart/form-data'):
        return None

    # Извлекаем boundary из Content-Type
    boundary = content_type.split('boundary=')[1].encode()
    
    # Разделяем тело на части
    parts = body.split(boundary)
    
    # Пропускаем первую и последнюю пустые части
    parts = parts[1:-1]
    
    result = {}
    for part in parts:
        try:
            # Пропускаем пустые части
            if not part.strip():
                continue
            
            # Удаляем начальные \r\n
            part = part.strip(b'\r\n')
            
            # Парсим заголовки части
            headers_end = part.find(b'\r\n\r\n')
            if headers_end == -1:
                continue
                
            headers_text = part[:headers_end]
            content = part[headers_end + 4:]
            
            # Удаляем последний \r\n из контента
            if content.endswith(b'\r\n'):
                content = content[:-2]
            
            headers = email.message_from_bytes(headers_text, policy=default)
            
            # Извлекаем имя поля
            content_disposition = headers.get('Content-Disposition', '')
            if 'name=' not in content_disposition:
                continue
                
            name = content_disposition.split('name=')[1].split(';')[0].strip('"')
            
            # Если это файл
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
                result[name] = {'filename': filename, 'content': content}
            else:
                result[name] = content.decode()
        except Exception as e:
            logger.error(f'Error parsing part: {e}')
            continue
    
    return result

# Обработчик входящих запросов
class ImageHostingHandler(BaseHTTPRequestHandler):
    """
    Основной обработчик запросов сервера.
    
    Что умеет:
    - Показывать главную страницу
    - Загружать картинки
    - Показывать список загруженных картинок
    - Отдавать статические файлы (html, js, css)
    """

    server_version = 'Image Hosting Server/0.1'

    def parse_multipart_form_data(self, headers, body):
        """Парсинг multipart/form-data."""
        content_type = headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            return None

        # Извлекаем boundary из Content-Type
        boundary = content_type.split('boundary=')[1].encode()
        
        # Разделяем тело на части
        parts = body.split(boundary)
        
        # Пропускаем первую и последнюю пустые части
        parts = parts[1:-1]
        
        result = {}
        for part in parts:
            try:
                # Пропускаем пустые части
                if not part.strip():
                    continue
                
                # Удаляем начальные \r\n
                part = part.strip(b'\r\n')
                
                # Парсим заголовки части
                headers_end = part.find(b'\r\n\r\n')
                if headers_end == -1:
                    continue
                    
                headers_text = part[:headers_end]
                content = part[headers_end + 4:]
                
                # Удаляем последний \r\n из контента
                if content.endswith(b'\r\n'):
                    content = content[:-2]
                
                headers = email.message_from_bytes(headers_text, policy=default)
                
                # Извлекаем имя поля
                content_disposition = headers.get('Content-Disposition', '')
                if 'name=' not in content_disposition:
                    continue
                    
                name = content_disposition.split('name=')[1].split(';')[0].strip('"')
                
                # Если это файл
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                    result[name] = {'filename': filename, 'content': content}
                else:
                    result[name] = content.decode()
            except Exception as e:
                logger.error(f'Error parsing part: {e}')
                continue
        
        return result

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        SimpleHTTPRequestHandler.end_headers(self)

    def handle_error(self, status_code: int, message: str):
        logger.error(f'Error {status_code}: {message}')
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(f'{{"error": "{message}"}}'.encode('utf-8'))

    def serve_static_file(self, path: str, content_type: str = None):
        """
        Отправляет статические файлы клиенту.
        
        Параметры:
        - path: путь к файлу в папке static/
        - content_type: тип файла (например text/html для html файлов)
        
        Как работает:
        1. Проверяет существование файла
        2. Определяет правильный content-type
        3. Отправляет файл с правильными заголовками
        """
        try:
            file_path = os.path.join(STATIC_PATH, path.lstrip('/'))
            if not os.path.isfile(file_path):
                self.handle_error(404, f'File not found: {file_path}')
                return

            # Определяем content-type если не указан
            if not content_type:
                if path.endswith('.html'):
                    content_type = 'text/html'
                elif path.endswith('.js'):
                    content_type = 'application/javascript'
                elif path.endswith('.ico'):
                    content_type = 'image/x-icon'
                elif path.endswith('.css'):
                    content_type = 'text/css'

            self.send_response(200)
            if content_type:
                self.send_header('Content-type', content_type)
                
            # Специальные заголовки для favicon
            if path.endswith('.ico'):
                self.send_header('Cache-Control', 'public, max-age=31536000')
            else:
                self.send_header('Cache-Control', 'public, max-age=3600')
                
            # Отправляем размер файла
            self.send_header('Content-Length', str(os.path.getsize(file_path)))
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        except Exception as e:
            self.handle_error(500, f'Error serving file: {str(e)}')

    def get_upload(self):
        """Обработка GET запроса для страницы загрузки"""
        self.serve_static_file('upload.html', 'text/html')

    def do_GET(self):
        try:
            if self.path == '/':
                self.serve_static_file('index.html', 'text/html')
            elif self.path == '/upload':
                self.serve_static_file('upload.html', 'text/html')
            elif self.path == '/images':
                # Редирект на страницу со списком изображений
                self.send_response(301)
                self.send_header('Location', '/all_images.html')
                self.end_headers()
            elif self.path == '/api/images':
                self.get_images()
            elif self.path == '/all_images.html':
                self.serve_static_file('all_images.html', 'text/html')
            elif self.path.startswith('/upload_success.html'):
                self.serve_static_file('upload_success.html', 'text/html')
            elif self.path.startswith('/static/'):
                path = self.path[8:]  # Убираем '/static/' из пути
                self.serve_static_file(path)
            elif self.path.startswith('/images/') and self.path != '/images':
                filename = self.path.split('/')[-1]
                self.get_image(filename)
            elif self.path == '/favicon.ico':
                self.serve_static_file('favicon.ico')
            else:
                self.handle_error(404, 'Not Found')
        except Exception as e:
            self.handle_error(500, str(e))

    def get_images(self):
        """
        Возвращает список всех загруженных картинок в формате JSON.
        
        Формат ответа:
        {
            "images": ["image1.jpg", "image2.png", ...]
        }
        """
        try:
            logger.info(f'GET {self.path}')
            images = [f for f in listdir(IMAGES_PATH) if isfile(join(IMAGES_PATH, f))]
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            import json
            self.wfile.write(json.dumps({"images": images}).encode('utf-8'))
        except Exception as e:
            self.handle_error(500, f'Error listing images: {str(e)}')

    def get_image(self, filename):
        """
        Отдает картинку по её имени.
        
        Параметры:
        - filename: имя файла картинки
        
        Проверки:
        1. Существует ли файл
        2. Является ли файл картинкой
        3. Правильный ли формат
        """
        try:
            logger.info(f'GET /images/{filename}')
            image_path = os.path.join(IMAGES_PATH, filename)
            if not os.path.isfile(image_path):
                self.handle_error(404, 'Image not found')
                return

            # Проверяем тип файла
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(image_path)
            if not file_type.startswith('image/'):
                self.handle_error(400, 'Invalid file type')
                return

            self.send_response(200)
            self.send_header('Content-type', file_type)
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            with open(image_path, 'rb') as f:
                self.wfile.write(f.read())
        except Exception as e:
            self.handle_error(500, f'Error serving image: {str(e)}')

    def do_POST(self):
        if self.path == '/upload':
            post_routes[self.path](self)
        else:
            logger.warning(f'POST 405 {self.path}')
            self.send_response(405, 'Method Not Allowed')

    def post_upload(self):
        """
        Обрабатывает загрузку новой картинки.
        
        Что делает:
        1. Проверяет размер файла
        2. Проверяет формат картинки
        3. Генерирует уникальное имя
        4. Сохраняет картинку
        5. Перенаправляет на страницу успеха
        
        Ограничения:
        - Максимальный размер файла: 5MB
        - Форматы: jpg, jpeg, png, gif
        """
        try:
            logger.info(f"POST {self.path}")
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > ALLOWED_LENGTH:
                self.handle_error(413, 'Payload Too Large')
                return

            # Читаем тело запроса
            body = self.rfile.read(content_length)
            
            # Парсим multipart/form-data
            form_data = self.parse_multipart_form_data(self.headers, body)
            
            if not form_data or 'image' not in form_data:
                logger.error('No image file found in request')
                self.handle_error(400, 'No image file uploaded')
                return

            file_data = form_data['image']
            if not isinstance(file_data, dict) or 'filename' not in file_data:
                logger.error('Invalid file data')
                self.handle_error(400, 'Invalid file data')
                return

            filename = file_data['filename']
            _, ext = os.path.splitext(filename)
            if not ext or ext.lower()[1:] not in ALLOWED_EXTENSIONS:
                logger.error(f'Unsupported Extension: {ext}')
                self.handle_error(400, 'File type not allowed')
                return

            file_content = file_data['content']
            image_id = uuid.uuid4()
            image_name = f'{image_id}{ext}'
            image_path = os.path.join(IMAGES_PATH, image_name)
            
            # Проверяем, что контент не пустой
            if not file_content:
                logger.error('Empty file content')
                self.handle_error(400, 'Empty file')
                return
            
            try:
                # Создаем директорию для изображений, если её нет
                os.makedirs(IMAGES_PATH, exist_ok=True)
                
                # Сохраняем файл
                with open(image_path, 'wb') as f:
                    f.write(file_content)

                # Проверяем, что файл является валидным изображением
                with Image.open(image_path) as im:
                    im.verify()
                
                logger.info(f"Upload success: {image_name}")
                self.send_response(301)
                self.send_header('Location', f'/upload_success.html?image={image_name}')
                self.end_headers()
                
            except (IOError, SyntaxError) as e:
                logger.error(f'Invalid file: {e}')
                if os.path.exists(image_path):
                    os.remove(image_path)
                self.handle_error(400, 'Invalid file')
            except Exception as e:
                logger.error(f'Error saving file: {e}')
                if os.path.exists(image_path):
                    os.remove(image_path)
                self.handle_error(500, 'Error saving file')
                
        except Exception as e:
            logger.error(f'Error in post_upload: {e}')
            self.handle_error(500, 'Internal server error')

    def do_HEAD(self):
        """Обработка HEAD запросов"""
        try:
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
            elif self.path == '/favicon.ico':
                self.send_response(200)
                self.send_header('Content-type', 'image/x-icon')
                self.end_headers()
            elif self.path.startswith('/images/') and self.path != '/images':
                filename = self.path.split('/')[-1]
                image_path = os.path.join(IMAGES_PATH, filename)
                if os.path.isfile(image_path):
                    self.send_response(200)
                    mime = magic.Magic(mime=True)
                    file_type = mime.from_file(image_path)
                    self.send_header('Content-type', file_type)
                    self.end_headers()
                else:
                    self.handle_error(404, 'Image not found')
            else:
                self.handle_error(404, 'Not Found')
        except Exception as e:
            self.handle_error(500, str(e))

get_routes = {
    '/upload': ImageHostingHandler.get_upload,
    '/api/images': ImageHostingHandler.get_images,
}

post_routes = {
    '/upload': ImageHostingHandler.post_upload,
}

# Инициализируем сервер
def run():
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