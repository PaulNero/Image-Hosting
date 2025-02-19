from http.server import HTTPServer, BaseHTTPRequestHandler

# Обработчик входящих запросов
class ImageHostingHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'Hello, world!')

    def do_POST(self):
        pass

# Инициализируем сервер
def run():
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, ImageHostingHandler)
    try:
        print(f"Serving at http://{server_address[0]}:{server_address[1]}")
        httpd.serve_forever()
    except Exception:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run()