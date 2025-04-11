import email
from email.parser import BytesParser
from email.policy import default
import magic
from loguru import logger
from app.db import DBManager
from config import settings

class FileHandler:
    """Обработчик файлов для загрузки и валидации."""
    
    @staticmethod
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

    @staticmethod
    def validate_file(file_content: bytes) -> bool:
        """Проверка безопасности файла"""
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_buffer(file_content)
            return file_type in settings.ALLOWED_MIME_TYPES
        except Exception as e:
            logger.error(f"Error validating file: {e}")
            return False
