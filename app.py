import io
import os.path
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from loguru import logger
from os import listdir
from os.path import isfile, join

from PIL import Image

SERVER_ADDRESS = ('0.0.0.0', 8000)
ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif')
ALLOWED_LENGTH = (5 * 1024 * 1024)

logger.add('logs/app.log', format='[{time: YYYY-MM-DD HH:mm:ss}] | {level} | {message}')

# Обработчик входящих запросов
class ImageHostingHandler(BaseHTTPRequestHandler):
    server_version = 'Image Hosting Server/0.1'

    routes = {
        '/': 'route_get_index',
        '/index': 'route_get_index',
        '/upload': 'route_post_upload',
        '/images':'route_get_images',
        '/favicon.ico': 'route_get_favicon', # TODO: Обработка перемещена с nginx в app
    }

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

    def route_get_favicon(self):
        logger.info(f'GET {self.path}')
        self.send_response(200)
        self.send_header('Content-type', 'image/x-icon')
        self.end_headers()
        self.wfile.write(open('static/favicon.ico', 'rb').read())


    def do_GET(self):
        # if self.path in self.routes:
        if self.path == '/images':
            exec(f'self.{self.routes[self.path]}()')
        elif self.path.startswith('/images/') and self.path != '/images':
            # Обработка динамического пути для конкретного изображения
            filename = self.path.split('/')[-1]
            self.route_get_image(filename)
        elif self.path in self.routes:
            exec(f'self.{self.routes[self.path]}()')
        else:
            logger.warning(f'GET 404 {self.path}')
            self.send_response(404, 'Not Found')
            self.send_header('Content-Length', '9')
            self.end_headers()
            self.wfile.write(b'Not Found')

    def route_get_index(self):
        logger.info(f'GET {self.path}')
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(open('static/index.html', 'rb').read())

    def route_get_images(self):
        logger.info(f'GET {self.path}')
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()

        images = [f for f in listdir('/app/images') if isfile(join('/app/images', f))]
        self.wfile.write(f'{{"images": {images}}}'.encode('utf-8'))
        # self.wfile.write(json.dumps({'images': images}).encode('utf-8'))

    def route_get_image(self, filename):
        logger.info(f'GET /images/{filename}')
        image_path = f'/app/images/{filename}'
        if os.path.isfile(image_path):
            self.send_response(200)
            # Определяем тип контента на основе расширения
            ext = filename.rsplit('.', 1)[-1].lower()
            content_type = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif'
            }.get(ext, 'application/octet-stream')
            self.send_header('Content-type', content_type)
            self.end_headers()
            with open(image_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            logger.warning(f'GET 404 Image /images/{filename}')
            self.send_response(404, 'Not Found')
            self.send_header('Content-Length', '9')  # Длина строки 'Not Found'
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_POST(self):
        if self.path == '/upload':
            exec(f'self.{self.routes[self.path]}()')
            # self.route_post_upload()
        else:
            logger.warning(f'POST 405 {self.path}')
            self.send_response(405, 'Method Not Allowed')

    def route_post_upload(self):
        logger.info(f"POST {self.path}")
        content_length = int(self.headers.get('Content-Length'))
        if content_length > ALLOWED_LENGTH:
            self.send_response(413, 'Payload Too Large')
            return

        filename = self.headers.get('Filename')

        if not filename:
            logger.error('Lack Header of Filename')
            self.send_response(400, 'Bad Request')
            return

        filename, ext = filename.split('\\')[-1].split('.')

        # filename, ext = filename.rsplit('.', 1)
        if ext not in ALLOWED_EXTENSIONS:
            logger.error('Unsupported Extension')
            self.send_response(400, 'Bad Request')
            return

        data = self.rfile.read(content_length)
        image_id = uuid.uuid4()

        with open(f'images/{image_id}.{ext}', 'wb') as f:
            f.write(data)

        logger.info(f"Upload success: {image_id}.{ext}")
        self.send_response(201, "Created")
        self.send_header('Location', f'http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}/images/{filename}.{ext}')

        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(open('static/upload_success.html', 'rb').read())


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