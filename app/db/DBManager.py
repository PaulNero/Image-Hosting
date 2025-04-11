import logging
import time
import os
import psycopg2
from loguru import logger
from pathlib import Path

from app.utils.singleton import SingletonMeta
from config.settings import DB_CONFIG, DB_CONNECT_RETRIES, DB_RETRY_DELAY


class DBManager(metaclass=SingletonMeta):
    """Менеджер подключения к базе данных PostgreSQL"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Установка соединения с базой данных"""
        for attempt in range(DB_CONNECT_RETRIES):
            try:
                self.conn = psycopg2.connect(**DB_CONFIG)
                logger.info("Успешное подключение к PostgreSQL")
                return
            except psycopg2.OperationalError as e:
                if attempt < DB_CONNECT_RETRIES - 1:
                    logger.warning(f"Попытка подключения {attempt + 1}/{DB_CONNECT_RETRIES} не удалась: {e}")
                    time.sleep(DB_RETRY_DELAY)
                else:
                    logger.error(f"Не удалось подключиться к PostgreSQL после {DB_CONNECT_RETRIES} попыток")
                    raise
    
    def get_connection(self):
        """Получение активного соединения"""
        if not self.conn or self.conn.closed:
            self._connect()
        return self.conn

    def execute(self, query: str) -> None:
        if not self.conn:
            logger.error("No database connection")
            return
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
        except psycopg2.Error as e:
            logger.error(f"Error executing query: {e}")

    def execute_file(self, filename: str) -> None:
        try:
            with open(filename, 'r') as f:
                query = f.read()
                self.execute(query)
        except FileNotFoundError:
            logger.error(f"File {filename} not found")

    def init_tables(self) -> None:
        if not self.conn:
            logger.error("No database connection")
            return
        
        # Используем абсолютный путь к SQL-файлу
        current_dir = Path(__file__).parent
        sql_file_path = current_dir / 'init_tables.sql'
        
        logger.info(f"Инициализация таблиц из файла {sql_file_path}")
        self.execute_file(sql_file_path)
        logger.info('Tables initialized')
        self.conn.commit()

    def get_images(self, page: int = 1, per_page: int = 10) -> list[tuple]:
        """
        Получает список изображений с пагинацией.
        
        Args:
            page: Номер страницы (начиная с 1)
            per_page: Количество изображений на странице
            
        Returns:
            Список кортежей с данными изображений
        """
        offset = (page - 1) * per_page
        logger.info(f'Try to get images with offset {offset}, limit {per_page}')
        with self.get_connection().cursor() as cursor:
            cursor.execute("""
                SELECT id, filename, original_name, size, file_type, upload_time 
                FROM images 
                ORDER BY upload_time DESC 
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            return cursor.fetchall()

    def add_image(self, filename: str, original_name: str, length: int, ext: str) -> None:
        logger.info(f'Try to add image {filename}')
        with self.conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO images "
                "(filename, original_name, size, file_type)"
                "VALUES (%s, %s, %s, %s)",
                (filename, original_name, length, ext)
            )
        self.conn.commit()

    def clear_images(self) -> None:
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM images")
        self.conn.commit()

    def delete_image(self, filename: str) -> None:
        logger.info(f'Try to delete image {filename}')
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM images WHERE filename = %s", (filename,))
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Error deleting image: {e}")