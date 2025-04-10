from Router import Router
from AdvancedHandler import AdvancedHTTPRequestHandler

def register_routes(router: Router, handler_class: AdvancedHTTPRequestHandler):
    # Основные маршруты
    router.add_route('GET', '/', handler_class.serve_static_file)
    router.add_route('GET', '/upload', handler_class.get_upload)
    router.add_route('GET', '/images', handler_class.get_images)
    router.add_route('GET', '/api/images', handler_class.get_images)
    router.add_route('GET', '/all_images.html', handler_class.serve_static_file)
    router.add_route('GET', '/upload_success.html', handler_class.serve_static_file)
    router.add_route('GET', '/favicon.ico', handler_class.serve_static_file)
    
    # Маршруты для изображений
    router.add_route('GET', '/images/<filename>', handler_class.get_image)
    router.add_route('POST', '/upload', handler_class.post_upload)
    router.add_route('DELETE', '/api/delete/<image_id>', handler_class.delete_image)
    
    # Маршруты для статических файлов
    router.add_route('GET', '/static/<path>', handler_class.serve_static_file)

# get_routes = {
#     '/upload': ImageHostingHandler.get_upload,
#     '/api/images': ImageHostingHandler.get_images,
# }

# post_routes = {
#     '/upload': ImageHostingHandler.post_upload,
# }