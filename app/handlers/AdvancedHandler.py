import json
import os.path
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from loguru import logger

from app.router import Router
from config.settings import STATIC_PATH

class AdvancedHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Обработчик HTTP-запросов с поддержкой маршрутизации, HTML и JSON ответов.

    Атрибуты:
        router (Router): объект маршрутизатора, сопоставляет путь и метод с обработчиком.
        default_response (callable): функция, вызываемая при отсутствии маршрута (возвращает 404).

    Основные методы:
        - do_GET: обрабатывает GET-запросы.
        - do_POST: обрабатывает POST-запросы.
        - do_PUT: обрабатывает PUT-запросы.
        - do_PATCH: обрабатывает PATCH-запросы.
        - do_DELETE: обрабатывает DELETE-запросы.
        - do_HEAD: обрабатывает HEAD-запросы.
        - send_html: отправляет HTML-файл как ответ.
        - send_json: отправляет JSON-ответ.
    """

    def __init__(self, request, client_address, server):
        self.default_response = lambda: self.handle_error(404, "Страница не найдена")
        self.router = Router()
        super().__init__(request, client_address, server)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def handle_error(self, status_code: int, message: str):
        logger.error(f'Error {status_code}: {message}')
        # Получаем заголовок Accept
        accept = self.headers.get('Accept', '')

        # Отправляем HTML для Браузера
        if 'text/html' in accept:
            # TODO: Заготовка под использование картинок в шаблоне error.html
            #       Добавить .error-img в css
            # image_map = {
            #     404: '404.png',
            #     403: '403.png',
            #     500: '500.png'
            # }
            # image = image_map.get(status_code, 'error.png')

            # self.send_html('error.html', code=status_code, context={
            #     'status_code': status_code,
            #     'message': message,
            #     'image': image
            # })
            self.send_html('error.html', code=status_code, context={
                'status_code': status_code,
                'message': message
            })
        else:
            # Отправляем JSON для Postman
            self.send_json({'error': message}, code=status_code)

    def send_html(self, file: str,
                  code: int = 200,
                  headers: dict = None,
                  file_path: str = STATIC_PATH,
                  context: dict = None) -> None:
        try:
            self.send_response(code)
            self.send_header('Content-type', 'text/html')
            if headers:
                for header, value in headers.items():
                    self.send_header(header, value)
            self.end_headers()

            with open(os.path.join(file_path, file), encoding='utf-8') as f:
                content = f.read()

            # Простая подстановка переменных вида {{ ключ }}
            if context:
                for key, value in context.items():
                    content = content.replace(f'{{{{ {key} }}}}', str(value))

            self.wfile.write(content.encode('utf-8'))

        except Exception as e:
            logger.error(f"Ошибка при отправке HTML: {e}")
            self.send_json({'error': 'Internal Server Error'}, code=500)

    def send_json(self, response: dict,
                  code: int = 200,
                  headers: dict = None) -> None:
        
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        if headers:
            for header, value in headers.items():
                self.send_header(header, value)
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def _handle_request(self, method: str) -> None:
        """
        Общая логика обработки HTTP-запросов.
        
        Параметры:
        - method: HTTP-метод (GET, POST, PUT, PATCH, DELETE, HEAD)
        """
        try:
            # Разбираем URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Получаем обработчик для пути
            handler, result = self.router.resolve(method, path)
            
            if isinstance(result, str):
                # Если result - строка, значит это сообщение об ошибке
                if result == '404 Not Found':
                    self.handle_error(404, 'Not Found')
                elif result == '405 Method Not Allowed':
                    self.handle_error(405, 'Method Not Allowed')
                return
            
            if handler:
                # Если это метод get_image, передаем только filename из URL
                if method == 'GET' and handler.__name__ == 'get_image':
                    filename = path.split('/')[-1]
                    handler(self, filename=filename)
                # Если это метод get_index или get_upload, не передаем никаких аргументов
                elif handler.__name__ in ['get_index', 'get_upload']:
                    handler(self)
                else:
                    # Для остальных методов передаем все параметры
                    handler(self, **result)
            else:
                self.handle_error(404, 'Not Found')
        except Exception as e:
            self.handle_error(500, f'Internal Server Error: {str(e)}')

    def do_GET(self):
        """Обработка GET запросов"""
        self._handle_request('GET')

    def do_POST(self) -> None:
        """Обработка POST запросов"""
        self._handle_request('POST')

    def do_PUT(self) -> None:
        """Обработка PUT запросов"""
        self._handle_request('PUT')
    
    def do_PATCH(self) -> None:
        """Обработка PATCH запросов"""
        self._handle_request('PATCH')

    def do_DELETE(self) -> None:
        """Обработка DELETE запросов"""
        self._handle_request('DELETE')

    def do_HEAD(self) -> None:
        """Обработка HEAD запросов"""
        self._handle_request('HEAD')

    