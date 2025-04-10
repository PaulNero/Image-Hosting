SERVER_ADDRESS = ('0.0.0.0', 8000)

ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif')
ALLOWED_LENGTH = (5 * 1024 * 1024)  # 5MB
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/gif']

UPLOAD_DIR = 'images'
IMAGES_PATH = '/app/images'

LOGS_PATH = '/app/logs'
LOG_FILE = 'app.log'
ERROR_FILE = 'upload_failed.html'

STATIC_PATH = '/app/static'