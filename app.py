import io
import os.path
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from loguru import logger

from PIL import Image

SERVER_ADDRESS = ('0.0.0.0', 8000)
ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif')
ALLOWED_LENGTH = (5 * 1024 * 1024)

logger.add('logs/app.log', format='[{time: YYYY-MM-DD HH:mm:ss}] | {level} | {message}')

# Обработчик входящих запросов
class ImageHostingHandler(BaseHTTPRequestHandler):
    server_version = 'Image Hosting Server/0.1'

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            logger.info(f'GET {self.path}')
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(open('index.html', 'rb').read())
        else:
            logger.warning(f'GET {self.path}')
            self.send_response(404, 'Not Found')

    def do_POST(self):
        if self.path == '/upload':

            logger.info(f"POST {self.path}")
            content_length = int(self.headers.get('Content-Length'))
            if content_length > ALLOWED_LENGTH:
                self.send_response(413, 'Payload Too Large')
                return

            filename = self.headers.get('Filename')

            if not filename:
                logger.error('Bad Request')
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
            self.wfile.write(open('upload_success.html', 'rb').read())

        else:
            self.send_response(405, 'Method Not Allowed')

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