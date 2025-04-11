#!/bin/bash

# Получаем текущую дату и время
DATE=$(date +%Y-%m-%d_%H%M%S)

# Путь для сохранения бэкапа
BACKUP_PATH="data/backups/backup_$DATE.sql"

# Создаем резервную копию базы данных
echo "Создание резервной копии базы данных..."
docker exec -t db pg_dump -U app -d image_hosting > $BACKUP_PATH

# Проверяем успешность создания бэкапа
if [ $? -eq 0 ]; then
    echo "Резервная копия успешно создана: $BACKUP_PATH"
    echo "Размер файла: $(du -h $BACKUP_PATH | cut -f1)"
else
    echo "Ошибка при создании резервной копии!"
    exit 1
fi 