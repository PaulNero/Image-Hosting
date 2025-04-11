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
from app.handlers.AdvancedHandler import AdvancedHTTPRequestHandler
from app.handlers.FileHandler import FileHandler
from app.db import DBManager
from config import settings

from PIL import Image
import json
import re
import secrets
import time
from datetime import datetime


"""
Основной обработчик запросов сервера хостинга изображений.

Этот класс предоставляет функциональность для:
- Показа главной страницы и интерфейса загрузки
- Загрузки и сохранения изображений
- Отображения списка загруженных изображений
- Удаления изображений
- Обслуживания статических файлов (HTML, JS, CSS)
"""
class ImageHostingHandler(AdvancedHTTPRequestHandler):
    server_version = 'Image Hosting Server/0.2'

    def __init__(self, request, client_address, server):
        # Отладочная информация о путях
        logger.info(f"STATIC_PATH: {settings.STATIC_PATH}")
        logger.info(f"STATIC_PATH существует: {os.path.exists(settings.STATIC_PATH)}")
        logger.info(f"Содержимое STATIC_PATH: {os.listdir(settings.STATIC_PATH) if os.path.exists(settings.STATIC_PATH) else 'не существует'}")
        
        self.db = DBManager()
        super().__init__(request, client_address, server)
        

    def redirect_to(self, path):
        """
        Выполняет перенаправление клиента на указанный путь.
        
        Args:
            path: Путь, на который нужно перенаправить клиента
        """
        self.send_response(302)
        self.send_header('Location', path)
        self.end_headers()

    def serve_static_file(self, path: str, content_type: str = None):
        """
        Отправляет статические файлы клиенту.
        
        Args:
            path: Путь к файлу в папке static/
            content_type: Тип контента (MIME-тип) файла
        
        Этот метод обрабатывает:
        1. Проверку существования файла
        2. Определение правильного content-type
        3. Отправку файла с правильными заголовками
        """
        try:
            file_path = os.path.join(settings.STATIC_PATH, path.lstrip('/'))
            logger.info(f"Запрошен файл: {file_path}")
            logger.info(f"Файл существует: {os.path.isfile(file_path)}")
            
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

    def get_index(self):
        """
        Обрабатывает GET запрос для главной страницы.
        
        Возвращает основную HTML-страницу с интерфейсом приложения.
        """
        self.serve_static_file('index.html', 'text/html')

    def get_upload(self):
        """
        Обрабатывает GET запрос для страницы загрузки.
        
        Возвращает HTML-страницу с формой для загрузки изображений.
        """
        self.serve_static_file('upload.html', 'text/html')

    def get_images(self):
        """
        Возвращает список всех загруженных картинок в формате JSON с поддержкой пагинации.
        
        Параметры запроса:
        - page: номер страницы (по умолчанию 1)
        - per_page: количество изображений на странице (по умолчанию 10)
        
        Формат ответа:
        {
            "images": [
                {
                    "id": 1,
                    "filename": "image1.jpg",
                    "original_name": "original.jpg",
                    "upload_time": "2024-04-11 12:00:00",
                    "size": 1024,
                    "file_type": "image/jpeg"
                },
                ...
            ],
            "total": 100,
            "page": 1,
            "per_page": 10
        }
        """
        try:
            logger.info(f'GET {self.path}')
            
            # Получаем параметры из запроса
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(self.path).query)
            page = int(query.get('page', [1])[0])
            per_page = int(query.get('per_page', [10])[0])
            
            # Проверяем, что значения корректны
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 10
            elif per_page > 50:  # Ограничиваем макс. количество
                per_page = 50
            
            # Получаем изображения из БД с сортировкой по времени загрузки
            images = self.db.get_images(page, per_page)
            
            # Получаем общее количество изображений
            with self.db.get_connection().cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM images")
                total = cursor.fetchone()[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            # Преобразуем кортежи в словари для JSON
            images_list = []
            for img in images:
                # Конвертируем datetime в строку, если это объект datetime
                upload_time = img[5]
                if hasattr(upload_time, 'isoformat'):
                    upload_time = upload_time.isoformat()
                elif isinstance(upload_time, str):
                    # Если это строка, оставляем как есть
                    pass
                else:
                    # Если это что-то другое, преобразуем в строку
                    upload_time = str(upload_time)
                
                images_list.append({
                    'id': img[0],          # id
                    'filename': img[1],    # filename
                    'original_name': img[2],  # original_name
                    'size': img[3],        # size
                    'file_type': img[4],   # file_type
                    'upload_time': upload_time  # upload_time, преобразованное в строку
                })
                
            response_data = {
                "images": images_list,
                "total": total,
                "page": page,
                "per_page": per_page
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        except Exception as e:
            self.handle_error(500, f'Error listing images: {str(e)}')

    def get_image(self, filename=None):
        """
        Отдает картинку по её имени.
        
        Args:
            filename: Имя файла картинки (опционально, может быть получено из URL)
        
        Этот метод:
        1. Проверяет существование файла
        2. Определяет тип содержимого (MIME-тип)
        3. Отправляет файл изображения с правильными заголовками
        """
        try:
            # Если filename не передан, получаем его из URL
            if filename is None:
                filename = self.path.split('/')[-1]
            
            logger.info(f'GET /images/{filename}')
            image_path = os.path.join(settings.IMAGES_PATH, filename)
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

    def post_upload(self):
        """
        Обрабатывает POST запрос для загрузки изображения.
        
        Этот метод:
        1. Принимает данные формы с файлом
        2. Проверяет тип файла (допустимы только изображения)
        3. Генерирует уникальное имя файла
        4. Сохраняет файл и добавляет информацию в базу данных
        5. Возвращает JSON-ответ с информацией об успешной загрузке
        """
        try:
            logger.info(f'POST {self.path}')
            
            # Получаем заголовки и тело запроса
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Парсим multipart/form-data
            form_data = FileHandler.parse_multipart_form_data(self.headers, body)
            
            if not form_data or 'file' not in form_data:
                self.handle_error(400, 'No image file found in request')
                return
                
            file_data = form_data['file']
            
            # Проверяем тип файла
            if not FileHandler.validate_file(file_data['content']):
                self.handle_error(400, 'Invalid file type')
                return
                
            # Получаем информацию о файле
            original_name = file_data['filename']
            file_content = file_data['content']
            file_size = len(file_content)
            file_ext = original_name.split('.')[-1].lower()
            
            # Генерируем уникальное имя файла
            filename = f"{uuid.uuid4()}.{file_ext}"
            file_path = os.path.join(settings.IMAGES_PATH, filename)
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                f.write(file_content)
                
            # Сохраняем информацию в БД
            self.db.add_image(
                filename=filename,
                original_name=original_name,
                length=file_size,
                ext=file_ext
            )
            
            # Отправляем ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response_data = {
                'success': True,
                'filename': filename,
                'original_name': original_name,
                'size': file_size,
                'file_type': f'image/{file_ext}'
            }
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            logger.error(f'Error uploading file: {str(e)}')
            self.handle_error(500, str(e))

    def delete_image(self, filename):
        """
        Удаляет изображение по его имени.
        
        Args:
            filename: Имя файла изображения
        
        Этот метод:
        1. Проверяет существование файла
        2. Удаляет запись из базы данных
        3. Удаляет физический файл
        4. Возвращает JSON-ответ с результатом операции
        """
        try:
            logger.info(f'DELETE /api/images/{filename}')
            image_path = os.path.join(settings.IMAGES_PATH, filename)
            
            # Проверяем существование файла
            if not os.path.isfile(image_path):
                self.handle_error(404, 'Image not found')
                return
                
            # Удаляем запись из БД
            self.db.delete_image(filename)
            
            # Удаляем файл
            os.remove(image_path)
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response_data = {
                'success': True,
                'message': 'Image deleted successfully'
            }
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            self.handle_error(500, f'Error deleting image: {str(e)}')

    def delete_image_by_id(self, id=None):
        """
        Удаляет изображение по его ID из базы данных.
        
        Args:
            id: Идентификатор изображения в базе данных
        
        Этот метод:
        1. Получает информацию об изображении из БД по ID
        2. Удаляет физический файл
        3. Удаляет запись из БД
        4. Перенаправляет пользователя на страницу со списком изображений
        """
        try:
            logger.info(f'GET /delete/{id}')
            
            if id is None:
                self.handle_error(400, 'Image ID is required')
                return
                
            # Получаем имя файла по ID
            with self.db.get_connection().cursor() as cursor:
                cursor.execute("SELECT filename FROM images WHERE id = %s", (id,))
                result = cursor.fetchone()
                
                if not result:
                    self.handle_error(404, f'Image with ID {id} not found')
                    return
                    
                filename = result[0]
            
            # Удаляем физический файл
            image_path = os.path.join(settings.IMAGES_PATH, filename)
            if os.path.isfile(image_path):
                os.remove(image_path)
            
            # Удаляем запись из БД
            with self.db.get_connection().cursor() as cursor:
                cursor.execute("DELETE FROM images WHERE id = %s", (id,))
            self.db.get_connection().commit()
            
            # Перенаправляем на страницу со списком изображений
            self.redirect_to('/all_images.html')
            
        except Exception as e:
            logger.error(f'Error deleting image by ID: {str(e)}')
            self.handle_error(500, f'Error deleting image: {str(e)}')