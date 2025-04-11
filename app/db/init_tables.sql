-- Создание таблицы для хранения информации об изображениях
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    original_name VARCHAR(255) NOT NULL,
    size INTEGER NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индекса для быстрого поиска по имени файла
CREATE INDEX IF NOT EXISTS idx_images_filename ON images(filename);

-- Создание индекса для сортировки по времени загрузки
CREATE INDEX IF NOT EXISTS idx_images_upload_time ON images(upload_time DESC);