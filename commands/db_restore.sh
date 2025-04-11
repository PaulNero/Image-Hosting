#!/bin/bash

# Проверяем, что аргумент передан
if [ $# -eq 0 ]; then
    echo "Ошибка: не указан файл резервной копии"
    echo "Использование: ./restore.sh path/to/backup.sql"
    exit 1
fi

BACKUP_FILE=$1

# Проверяем существование файла
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Ошибка: файл $BACKUP_FILE не существует"
    exit 1
fi

# Восстанавливаем базу данных из резервной копии
echo "Восстановление базы данных из файла $BACKUP_FILE..."
docker exec -i db psql -U app -d image_hosting < "$BACKUP_FILE"

# Проверяем успешность восстановления
if [ $? -eq 0 ]; then
    echo "База данных успешно восстановлена из резервной копии $BACKUP_FILE"
else
    echo "Ошибка при восстановлении базы данных!"
    exit 1
fi 