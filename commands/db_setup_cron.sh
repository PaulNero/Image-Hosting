#!/bin/bash

# Получаем абсолютный путь к директории проекта
PROJECT_DIR=$(pwd)

# Путь к скрипту бэкапа
BACKUP_SCRIPT="$PROJECT_DIR/commands/backup.sh"

# Делаем скрипты исполняемыми
chmod +x "$PROJECT_DIR/commands/backup.sh"
chmod +x "$PROJECT_DIR/commands/restore.sh"

# Создаем временный файл для crontab
TEMP_CRON=$(mktemp)
crontab -l > $TEMP_CRON 2>/dev/null || true

# Проверяем, нет ли уже такой задачи
if grep -q "$BACKUP_SCRIPT" $TEMP_CRON; then
    echo "Задача по созданию резервных копий уже настроена в crontab"
else
    # Добавляем задачу в crontab (каждый день в 3:00)
    echo "0 3 * * * $BACKUP_SCRIPT >> $PROJECT_DIR/data/logs/backup.log 2>&1" >> $TEMP_CRON
    crontab $TEMP_CRON
    echo "Задача по ежедневному созданию резервных копий добавлена в crontab"
fi

# Удаляем временный файл
rm $TEMP_CRON

echo "Настройка автоматического резервного копирования завершена" 